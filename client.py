import tkinter as tk
from tkinter import messagebox, ttk
import requests
import socket
import threading
import time
import socketio

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

    def on_coin_detected(self):
        print("Coin detected via SocketIO")
        self.time_left = 60
        self.show_done_button()

    def create_lock_screen(self):
        print("Creating lock screen...")
        self.clear_screen()
        
        # Main frame with padding
        self.lock_frame = ttk.Frame(self.root, padding="20")
        self.lock_frame.pack(expand=True, fill='both')
        
        # Title
        title_label = ttk.Label(self.lock_frame, text="🔒 PiSonet Computer Locked", 
                               font=("Segoe UI", 28, "bold"), foreground="#2c3e50")
        title_label.pack(pady=(50, 30))
        
        # Subtitle
        subtitle_label = ttk.Label(self.lock_frame, text="Insert coin to unlock computer access", 
                                  font=("Segoe UI", 14), foreground="#7f8c8d")
        subtitle_label.pack(pady=(0, 40))
        
        # Insert coin button
        style = ttk.Style()
        style.configure("Coin.TButton", font=("Segoe UI", 16, "bold"), 
                       padding=20, background="#27ae60", foreground="white")
        self.push_btn = ttk.Button(self.lock_frame, text="🪙 INSERT COIN", 
                                  style="Coin.TButton", command=self.start_countdown)
        self.push_btn.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(self.lock_frame, text="", 
                                     font=("Segoe UI", 12), foreground="#e74c3c")
        self.status_label.pack(pady=10)

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
        
        self.timer_label = ttk.Label(self.lock_frame, text=f"⏰ Time Left: {self.time_left}s", 
                                    font=("Segoe UI", 18, "bold"), foreground="#e74c3c")
        self.timer_label.pack(pady=10)

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
        self.status_label.config(text="✅ Coin detected! Click DONE to unlock", foreground="#27ae60")
        style = ttk.Style()
        style.configure("Done.TButton", font=("Segoe UI", 14, "bold"), 
                       padding=10, background="#3498db", foreground="white")
        self.done_btn = ttk.Button(self.lock_frame, text="✅ DONE PAYING", 
                                  style="Done.TButton", command=self.unlock_screen)
        self.done_btn.pack(pady=10)

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
            widget.destroy()

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