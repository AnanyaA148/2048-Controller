import socket
from signal import pause

from gpiozero import Button

# ----------------------------- settings -----------------------------
LAPTOP_IP = "192.168.137.1"   # <-- CHANGE THIS to your laptop's IPv4 address
UNITY_PORT = 5007            # must match the Pi port on the UdpInputBridge in Unity

# Grove Base Hat digital ports. The port number is the GPIO number.
PINS = {
    5: "up",      # D5
    16: "down",   # D16
    18: "left",   # D18
    22: "right",  # D22
}


 
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