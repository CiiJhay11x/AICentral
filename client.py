import tkinter as tk
from tkinter import messagebox, ttk
import requests
import socket
import threading
import time
import socketio
from PIL import Image, ImageTk
import os

# Get server IP (broadcast or hardcode)
def get_server_ip():
    # For now, skip scanning to speed up
    return None  # Will use hardcoded IP

SERVER_IP = get_server_ip() or "192.168.1.100:8080"
CLIENT_ID = socket.gethostname()[:8]

class PiSonetClient:
    def __init__(self, root):
        self.root = root
        self.root.title("PiSonet Client")
        self.root.geometry("800x600")
        # self.root.attributes('-fullscreen', True)  # Commented out for debugging
        self.active = False
        self.timer_id = None
        self.time_left = 0

        # Download and set background image
        self.bg_image = None
        self.load_background()

        # SocketIO for real-time coin detection
        self.sio = socketio.Client()
        self.sio.on('coin_detected', self.on_coin_detected)
        try:
            self.sio.connect(f"http://{SERVER_IP}")
            print("Connected to server via SocketIO")
        except:
            print("Failed to connect to server")

        self.create_lock_screen()

        # Emergency close (trial)
        self.root.bind("<Escape>", lambda e: self.emergency_close())

        # Admin panel
        self.root.bind("<F10>", lambda e: self.show_admin())

    def load_background(self):
        bg_url = "https://static.vecteezy.com/system/resources/previews/023/165/669/large_2x/game-background-with-magic-maya-altar-in-jungle-free-vector.jpg"
        bg_path = "background.jpg"
        if not os.path.exists(bg_path):
            try:
                response = requests.get(bg_url)
                with open(bg_path, 'wb') as f:
                    f.write(response.content)
                print("Background image downloaded")
            except:
                print("Failed to download background image")
                return
        
        try:
            img = Image.open(bg_path)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(img)
            self.bg_label = tk.Label(self.root, image=self.bg_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bg_label.lower()  # Send to back
        except:
            print("Failed to load background image")

    def on_coin_detected(self):
        print("Coin detected via SocketIO")
        self.time_left = 60
        self.show_done_button()

    def create_lock_screen(self):
        print("Creating lock screen...")
        self.clear_screen()
        
        # Create a canvas for the overlay with transparency effect
        self.canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Semi-transparent overlay
        self.canvas.create_rectangle(0, 0, 800, 600, fill='#000000', stipple='gray50', outline='')
        
        # Main content frame on canvas
        self.lock_frame = tk.Frame(self.canvas, bg='#ffffff', bd=2, relief='raised')
        self.canvas.create_window(400, 300, window=self.lock_frame, anchor='center')
        
        # Title
        title_label = tk.Label(self.lock_frame, text="🔒 PiSonet Computer Locked", 
                              font=("Segoe UI", 28, "bold"), bg='#ffffff', fg="#2c3e50")
        title_label.pack(pady=(20, 10))
        
        # Subtitle
        subtitle_label = tk.Label(self.lock_frame, text="Insert coin to unlock computer access", 
                                 font=("Segoe UI", 14), bg='#ffffff', fg="#7f8c8d")
        subtitle_label.pack(pady=(0, 20))
        
        # Insert coin button
        self.push_btn = tk.Button(self.lock_frame, text="🪙 INSERT COIN", 
                                 font=("Segoe UI", 16, "bold"), bg="#27ae60", fg="white", 
                                 padx=20, pady=10, command=self.start_countdown)
        self.push_btn.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(self.lock_frame, text="", 
                                    font=("Segoe UI", 12), bg='#ffffff', fg="#e74c3c")
        self.status_label.pack(pady=5)

        # Emergency close button (trial)
        self.close_btn = tk.Button(self.root, text="X", font=("Arial", 14), bg="red", fg="white", command=self.emergency_close)
        self.close_btn.place(relx=0.95, rely=0.02)

        # Admin trigger
        self.root.bind("<F10>", lambda e: self.show_admin())

    def start_countdown(self):
        self.active = True
        self.push_btn.config(state='disabled')
        self.status_label.config(text="⏳ Enabling coin slot... Please insert coin within 60 seconds", foreground="#f39c12")
        self.time_left = 60  # Default
        self.update_countdown()

        # Enable coinslot via server
        self.send_command("enable_relay")

        # Listen for coin (fallback)
        self.check_coin()

    def update_countdown(self):
        if self.time_left <= 0:
            self.end_session()
            return

        # Remove previous timer label if exists
        if hasattr(self, 'timer_label'):
            self.timer_label.destroy()
        
        self.timer_label = tk.Label(self.lock_frame, text=f"⏰ Time Left: {self.time_left}s", 
                                   font=("Segoe UI", 18, "bold"), bg='#ffffff', fg="#e74c3c")
        self.timer_label.pack(pady=5)

        self.timer_id = self.root.after(1000, self.decrement_timer)

    def decrement_timer(self):
        self.time_left -= 1
        self.update_countdown()

    def check_coin(self):
        try:
            resp = requests.get(f"http://{SERVER_IP}/api/coin_event", timeout=1)
            if resp.json().get("coin"):
                self.time_left = 60
                self.show_done_button()
        except:
            pass
        self.root.after(500, self.check_coin)

    def show_done_button(self):
        self.status_label.config(text="✅ Coin detected! Click DONE to unlock", fg="#27ae60")
        self.done_btn = tk.Button(self.lock_frame, text="✅ DONE PAYING", 
                                 font=("Segoe UI", 14, "bold"), bg="#3498db", fg="white", 
                                 padx=10, pady=5, command=self.unlock_screen)
        self.done_btn.pack(pady=5)

    def cancel_countdown(self):
        self.root.after_cancel(self.timer_id)
        self.end_session()

    def end_session(self):
        self.active = False
        self.send_command("disable_relay")
        self.create_lock_screen()

    def unlock_screen(self):
        self.root.after_cancel(self.timer_id)
        self.active = True
        self.send_command("unlock")

        self.clear_screen()
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.geometry("200x100")
        self.timer_window.attributes('-alpha', 0.7)
        self.timer_window.overrideredirect(True)
        self.timer_window.geometry("+%d+%d" % (self.root.winfo_screenwidth()-220, self.root.winfo_screenheight()-120))

        self.remaining = 3600  # 1 hour default
        self.timer_label = tk.Label(self.timer_window, text="1:00:00", font=("Arial", 14))
        self.timer_label.pack()

        tk.Button(self.timer_window, text="Insert Coin", command=self.add_time).pack()

        self.update_timer()

    def update_timer(self):
        if self.remaining <= 0:
            self.lock_screen()
            return
        self.remaining -= 1
        h = self.remaining // 3600
        m = (self.remaining % 3600) // 60
        s = self.remaining % 60
        self.timer_label.config(text=f"{h}:{m:02d}:{s:02d}")
        self.root.after(1000, self.update_timer)

    def add_time(self):
        # Send request to server to add time
        pass

    def send_command(self, cmd):
        try:
            requests.post(f"http://{SERVER_IP}/api/client/{CLIENT_ID}", json={"action": cmd})
        except:
            pass

    def clear_screen(self):
        for widget in self.root.winfo_children():
            if widget != self.bg_label:  # Keep background
                widget.destroy()
        # Recreate background if needed
        if hasattr(self, 'bg_label') and self.bg_label.winfo_exists():
            self.bg_label.lift()  # Bring to front? No, background should be back
            self.bg_label.lower()

    def emergency_close(self):
        if messagebox.askyesno("Emergency", "Close PiSonet Client?"):
            self.root.destroy()

    def show_admin(self):
        pwd = tk.simpledialog.askstring("Admin", "Password:", show="*")
        if pwd == "admin":
            self.admin_panel()

    def admin_panel(self):
        win = tk.Toplevel(self.root)
        win.title("Admin")
        tk.Button(win, text="Force Exit", command=self.emergency_close).pack()
        tk.Button(win, text="Change Wallpaper", command=self.change_wallpaper).pack()

    def change_wallpaper(self):
        # Windows: regedit, Linux: gsettings
        pass

if __name__ == "__main__":
    print("Starting PiSonet Client...")
    root = tk.Tk()
    app = PiSonetClient(root)
    print("Client initialized, starting main loop...")
    root.mainloop()