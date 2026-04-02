import tkinter as tk
from tkinter import messagebox
import requests
import socket
import threading
import time

# Get server IP (broadcast or hardcode)
def get_server_ip():
    # Simple: assume same subnet
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    # Try common Pisone IPs
    for i in range(1, 255):
        test_ip = f"{'.'.join(ip.split('.')[:-1])}.{i}:8080"
        try:
            requests.get(f"http://{test_ip}/", timeout=0.5)
            return test_ip.split(':')[0]
        except:
            continue
    return None

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
        self.create_lock_screen()

        # Emergency close (trial)
        self.root.bind("<Escape>", lambda e: self.emergency_close())

        # Admin panel
        self.root.bind("<F10>", lambda e: self.show_admin())

    def create_lock_screen(self):
        print("Creating lock screen...")
        self.clear_screen()
        self.lock_frame = tk.Frame(self.root)
        self.lock_frame.pack(expand=True)

        tk.Label(self.lock_frame, text="PiSonet Computer Locked", font=("Arial", 24)).pack(pady=20)
        self.push_btn = tk.Button(self.lock_frame, text="Press to Enable Coin Insert", font=("Arial", 16), command=self.start_countdown)
        self.push_btn.pack(pady=20)

        # Emergency close button (trial)
        self.close_btn = tk.Button(self.root, text="X", font=("Arial", 14), bg="red", fg="white", command=self.emergency_close)
        self.close_btn.place(relx=0.95, rely=0.02)

        # Admin trigger
        self.root.bind("<F10>", lambda e: self.show_admin())

    def start_countdown(self):
        self.active = True
        self.push_btn.config(state=tk.DISABLED)
        self.time_left = 60  # Default
        self.update_countdown()

        # Enable coinslot via server
        self.send_command("enable_relay")

        # Listen for coin
        self.check_coin()

    def update_countdown(self):
        if self.time_left <= 0:
            self.end_session()
            return

        self.lock_frame.children.get("timer_label", tk.Label()).destroy()
        tk.Label(self.lock_frame, text=f"Time Left: {self.time_left}s", font=("Arial", 20), name="timer_label").pack()

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
        tk.Button(self.lock_frame, text="DONE PAYING", font=("Arial", 16), command=self.unlock_screen).pack(pady=10)

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