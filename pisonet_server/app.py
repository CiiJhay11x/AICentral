# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit
import OPi.GPIO as GPIO
import time
import threading
import json
import os

app = Flask(__name__)
app.secret_key = 'pisonet_secret_key_change_later'
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# GPIO Setup
COIN_PIN = 3    # Physical Pin 5
RELAY_PIN = 5   # Physical Pin 29 (LOW = ON)

GPIO.setmode(GPIO.BOARD)
GPIO.setup(COIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Coin switch (active low)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.output(RELAY_PIN, GPIO.HIGH)  # Relay OFF by default

# Global Data
clients = {}  # client_id -> {name, time_left, rate_map, timer_thread, active}
timer_rates = {
    "P1": 10 * 60,   # 10 mins
    "P5": 60 * 60,   # 60 mins
    "P10": 3 * 3600  # 3 hours
}
default_timer = 60  # seconds for countdown

# Load saved data
if os.path.exists('clients.json'):
    with open('clients.json', 'r') as f:
        clients = json.load(f)

if os.path.exists('rates.json'):
    with open('rates.json', 'r') as f:
        timer_rates = json.load(f)

# User Model
class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return User()
    return None

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            user = User()
            login_user(user)
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard
@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', clients=clients, rates=timer_rates)

# API: Update Rates
@app.route('/api/update_rates', methods=['POST'])
@login_required
def update_rates():
    global timer_rates
    data = request.json
    for k, v in data.items():
        timer_rates[k] = int(v) * 60  # convert to seconds
    with open('rates.json', 'w') as f:
        json.dump(timer_rates, f)
    return jsonify(success=True)

# API: Manage Client
@app.route('/api/client/<client_id>', methods=['POST'])
@login_required
def manage_client(client_id):
    action = request.json.get('action')
    value = request.json.get('value')

    if client_id not in clients:
        clients[client_id] = {
            'name': f'PC-{client_id}',
            'time_left': 0,
            'rate_map': timer_rates,
            'active': False,
            'timer_thread': None
        }

    client = clients[client_id]

    if action == 'set_name':
        client['name'] = value
    elif action == 'add_time':
        client['time_left'] += int(value) * 60
    elif action == 'deduct_time':
        client['time_left'] = max(0, client['time_left'] - int(value) * 60)
    elif action == 'bypass_open':
        client['active'] = True
        client['start_time'] = time.time()
        if client['timer_thread'] and client['timer_thread'].is_alive():
            client['timer_thread'].join(timeout=1)
        client['timer_thread'] = threading.Thread(target=upward_timer, args=(client_id,))
        client['timer_thread'].start()

    with open('clients.json', 'w') as f:
        json.dump(clients, f)

    return jsonify(success=True, client=client)

# Upward Timer (for bypass mode)
def upward_timer(client_id):
    client = clients[client_id]
    start = client['start_time']
    while client['active']:
        elapsed = int(time.time() - start)
        client['time_used'] = elapsed
        # Calculate price tier
        tier = max(1, elapsed // 600)  # Every 10 mins = P1 increment
        price_key = f"P{tier}"
        price = timer_rates.get(price_key, timer_rates["P1"])
        socketio.emit('timer_update', {
            'client_id': client_id,
            'time_used': elapsed,
            'price_key': price_key,
            'price': price
        })
        time.sleep(1)

# Coin Detection & Relay Control
def coin_detection_loop():
    while True:
        if GPIO.input(COIN_PIN) == GPIO.LOW:  # Coin inserted
            GPIO.output(RELAY_PIN, GPIO.LOW)  # Enable coinslot
            # Notify all clients
            socketio.emit('coin_detected')
            time.sleep(1)  # Debounce
        else:
            GPIO.output(RELAY_PIN, GPIO.HIGH)  # Disable coinslot
        time.sleep(0.1)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Background Thread
@app.before_first_request
def start_background_tasks():
    threading.Thread(target=coin_detection_loop, daemon=True).start()

# Run App
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)