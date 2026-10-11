"""
Raspberry Pi button controller for the Unity 2048 game.

Run this ON THE RASPBERRY PI. Each button press sends "up", "down", "left" or "right"
over the network to the laptop running Unity (default port 5007).

Wiring (4 buttons): one leg of each button to its GPIO pin, the other leg to any GND pin.
The Pi's internal pull-up resistors are used, so no extra resistors are needed.

    UP    -> GPIO 17 (physical pin 11)
    DOWN  -> GPIO 27 (physical pin 13)
    LEFT  -> GPIO 22 (physical pin 15)
    RIGHT -> GPIO 23 (physical pin 16)

Run:
    python3 pi_buttons_2048.py

The Pi and the laptop must be on the same network. Find the laptop's address by
running  ipconfig  in PowerShell and copying the "IPv4 Address".
"""

import socket
from signal import pause

from gpiozero import Button

# ----------------------------- settings -----------------------------
LAPTOP_IP = "192.168.1.50"   # <-- CHANGE THIS to your laptop's IPv4 address
UNITY_PORT = 5007            # must match the Pi port on the UdpInputBridge in Unity

PINS = {                     # BCM GPIO numbers
    "up": 17,
    "down": 27,
    "left": 22,
    "right": 23,
}
# ---------------------------------------------------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def send(direction):
    sock.sendto(direction.encode("utf-8"), (LAPTOP_IP, UNITY_PORT))
    print("Sent:", direction)


def make_handler(direction):
    # gpiozero calls the handler with no arguments, so wrap the direction in a closure
    def handler():
        send(direction)
    return handler


buttons = {}
for name, pin in PINS.items():
    button = Button(pin, bounce_time=0.05)   # bounce_time filters out contact bounce
    button.when_pressed = make_handler(name)
    buttons[name] = button

print(f"Ready. Sending button presses to {LAPTOP_IP}:{UNITY_PORT}. Press Ctrl+C to stop.")
pause()