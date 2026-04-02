# AICentral - PiSonet Server

This project implements a coin-operated computer network system using an Orange Pi One as the server.

## Project Structure

- `pisonet_server/`: Server application (Flask + SocketIO + GPIO)
  - `app.py`: Main server application
  - `templates/`: HTML templates for web dashboard
  - `requirements.txt`: Python dependencies
- `client.py`: Client application for Windows/Linux PCs

## Quick Setup (Clone Repository)

1. **Push the code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Add PiSonet implementation"
   git push origin main
   ```

2. **On Orange Pi One** (IP: 192.168.1.100, root password: 1234):
   ```bash
   # SSH into Orange Pi
   ssh root@192.168.1.100
   # Password: 1234

   # Clone the repository
   git clone https://github.com/CiiJhay11x/AICentral.git
   cd AICentral

   # Install Python dependencies
   pip3 install -r pisonet_server/requirements.txt --break-system-packages

   # Run the server
   cd pisonet_server
   python3 app.py
   ```

3. **On Client PCs** (Windows/Linux with GUI):
   ```bash
   # Clone or download client.py
   git clone https://github.com/CiiJhay11x/AICentral.git
   cd AICentral

   # Install required packages (if not already installed)
   pip install requests python-socketio pillow --break-system-packages

   # Run the client
   python client.py
   ```

   **Note**: Client requires a graphical desktop environment. Does not run on headless servers.

## Detailed Installation Guide

### Step 1: Prepare Your Development Environment

If you're developing on a different machine:

1. Ensure you have Git installed
2. Clone this repository:
   ```bash
   git clone https://github.com/CiiJhay11x/AICentral.git
   cd AICentral
   ```

3. Install Python dependencies locally (optional, for testing):
   ```bash
   cd pisonet_server
   pip install -r requirements.txt
   ```

### Step 2: Orange Pi One Server Setup

#### Hardware Requirements
- Orange Pi One with Armbian installed
- SD card with Armbian_26.2.1_Orangepione_trixie_current_6.12.74_minimal.img
- Coin acceptor connected to GPIO Pin 3 (Physical Pin 5)
- Relay module connected to GPIO Pin 5 (Physical Pin 29)

#### Software Installation

1. **Flash Armbian to SD Card**:
   ```bash
   # On your host machine
   sudo dd if=Armbian_26.2.1_Orangepione_trixie_current_6.12.74_minimal.img of=/dev/sdX bs=4M status=progress
   ```

2. **Boot Orange Pi One**:
   - Insert SD card
   - Power on (no monitor needed)
   - Default SSH: root / 1234 (you mentioned this is your password)

3. **Initial Configuration**:
   ```bash
   # SSH into the Pi
   ssh root@192.168.1.100
   # Password: 1234

   # Update system
   apt update && apt upgrade -y

   # Install required packages
   apt install python3 python3-pip git curl -y

   # Set hostname (optional)
   hostnamectl set-hostname piserver

   # Enable GPIO support
   echo "overlays=sun8i-h3-orangepi-one" >> /boot/armbianEnv.txt
   reboot
   ```

4. **Clone and Install PiSonet**:
   ```bash
   # After reboot, SSH back in
   ssh root@192.168.1.100

   # Clone repository
   git clone https://github.com/CiiJhay11x/AICentral.git
   cd AICentral/pisonet_server

   # Install Python packages
   pip3 install -r requirements.txt --break-system-packages

   # Test GPIO (optional)
   python3 -c "import OPi.GPIO as GPIO; GPIO.setmode(GPIO.BOARD); GPIO.setup(3, GPIO.IN); print('GPIO OK')"
   ```

5. **Run the Server**:
   ```bash
   # In the pisonet_server directory
   python3 app.py
   ```
   The server will start on port 8080. Access the dashboard at: http://192.168.1.100:8080

#### Troubleshooting Port Issues
- If port 8080 is blocked, check firewall:
  ```bash
  ufw allow 8080
  ```
- Or run as root (not recommended for production):
  ```bash
  sudo python3 app.py
  ```
- To use port 80 (requires root):
  - Edit app.py and change port=8080 to port=80
  - Run with sudo

### Step 3: Client Setup

#### For Windows/Linux PCs

1. **Install Python**:
   - Windows: Download from python.org
   - Linux: Usually pre-installed, ensure tkinter is available:
     ```bash
     # Ubuntu/Debian
     sudo apt install python3-tk
     ```

2. **Download Client**:
   ```bash
   # Clone repository
   git clone https://github.com/CiiJhay11x/AICentral.git
   cd AICentral

   # Or download client.py directly
   wget https://raw.githubusercontent.com/CiiJhay11x/AICentral/main/client.py
   ```

3. **Install Dependencies**:
   ```bash
   pip install requests
   ```

4. **Run Client**:
   ```bash
   python client.py
   ```

The client will automatically detect the server at 192.168.1.100:8080 or scan the network.

#### Client Features
- Full-screen lock screen
- Coin insertion countdown
- Admin panel (F10, password: admin)
- Emergency exit (Escape)

### Step 4: Hardware Wiring

Connect to Orange Pi One GPIO:
- **Coin Input**: GPIO 3 (Physical Pin 5) - Connect to coin switch NO contact
- **Relay Control**: GPIO 5 (Physical Pin 29) - Connect to relay IN (LOW = ON)

Use pull-up resistors and proper power supplies for relays.

### Step 5: Configuration

#### Server Configuration
- Edit `pisonet_server/app.py` for custom settings
- Timer rates in `rates.json` (created automatically)
- Client data in `clients.json` (created automatically)

#### Security
- Change default admin password in `app.py`
- Change Flask secret key
- Consider HTTPS with nginx reverse proxy

### Step 6: Testing

1. **Server**:
   - Access http://192.168.1.100:8080
   - Login with admin/admin
   - Check GPIO functionality

2. **Client**:
   - Run client.py
   - Test lock screen and coin simulation

### Common Issues

- **Port not accessible**: Check firewall, try different port
- **GPIO errors**: Ensure proper Armbian version and overlays
- **Client can't connect**: Verify server IP and port
- **Tkinter missing**: Install python3-tk package

### Production Deployment

For production:
- Run server with systemd service
- Use nginx reverse proxy
- Enable HTTPS
- Set up proper logging
- Configure firewall (ufw)

## Features

- Web dashboard for admin management
- GPIO control for coin input and relay
- Real-time client monitoring via SocketIO
- Lock screen and timer on clients
- Upward billing for extended sessions

## Default Credentials

- Admin login: admin / admin

**Change passwords after setup for security!**