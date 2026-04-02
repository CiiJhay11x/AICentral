# AICentral - PiSonet Server

This project implements a coin-operated computer network system using an Orange Pi One as the server.

## Project Structure

- `pisonet_server/`: Server application (Flask + SocketIO + GPIO)
  - `app.py`: Main server application
  - `templates/`: HTML templates for web dashboard
  - `requirements.txt`: Python dependencies
- `client.py`: Client application for Windows/Linux PCs

## Setup Instructions

1. On the Orange Pi One (Armbian):
   - Install dependencies: `pip3 install -r requirements.txt --break-system-packages`
   - Run the server: `python3 app.py`

2. On client PCs:
   - Install Python with tkinter
   - Run `python client.py`

## Features

- Web dashboard for admin management
- GPIO control for coin input and relay
- Real-time client monitoring via SocketIO
- Lock screen and timer on clients

## Hardware Wiring

- Coin Input: GPIO Pin 3 (Physical Pin 5)
- Relay Control: GPIO Pin 5 (Physical Pin 29)

## Default Credentials

- Admin login: admin / admin

Change passwords after setup for security.