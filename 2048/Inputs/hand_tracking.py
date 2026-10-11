"""
Hand-tracking controller for the Unity 2048 game (zone version).

The camera view is split into a small centre box plus four sections
(up / down / left / right). Whichever section your hand is in is the move:

    - Hand in the centre box  -> nothing happens (resting position)
    - Move your hand into a section -> that move is sent immediately
    - Keep it there -> the move repeats every REPEAT_INTERVAL seconds
    - Return to the centre to reset

Moves are sent to Unity over UDP (default: 127.0.0.1:5005).
The active section lights up green so you can see what the game is getting.

Install (PowerShell):
    pip install opencv-python cvzone mediapipe

Run:
    python hand_tracking_2048.py

Press Q in the camera window to quit.
"""

import socket
import time

import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector

# ----------------------------- settings -----------------------------
UNITY_IP = "127.0.0.1"   # same laptop as Unity
UNITY_PORT = 5005        # must match the Hand port on the UdpInputBridge in Unity
CAMERA_INDEX = 0         # try 1 if the wrong camera opens

DEAD_ZONE = 0.40         # size of the centre box (0.1 = tiny, 0.5 = big). Bigger = hand must go further
REPEAT_WHILE_HELD = True # keep sending moves while your hand stays in a section
REPEAT_INTERVAL = 0.6    # seconds between repeats while held
MIN_INTERVAL = 0.2       # never send two moves closer together than this (stops flicker at section edges)
SMOOTHING = 0.5          # 0-1, higher = follows your hand faster but more jittery
# ---------------------------------------------------------------------

# Palm points (wrist + base of each finger), used only to find the hand's position.
# Using these means opening or closing your fingers doesn't move the dot.
PALM_POINTS = [0, 5, 9, 13, 17]


def get_zone(px, py, w, h):
    """Which section is the point in? Returns "up"/"down"/"left"/"right", or None in the centre box."""
    nx = (px - w / 2) / (w / 2)   # -1 (far left) .. +1 (far right)
    ny = (py - h / 2) / (h / 2)   # -1 (top) .. +1 (bottom)

    if max(abs(nx), abs(ny)) < DEAD_ZONE:
        return None
    if abs(nx) >= abs(ny):
        return "right" if nx > 0 else "left"
    return "down" if ny > 0 else "up"


def draw_zones(img, active):
    """Draw the centre box, the section dividers, and tint the active section."""
    h, w = img.shape[:2]
    cx, cy = w // 2, h // 2
    dw, dh = int(DEAD_ZONE * w / 2), int(DEAD_ZONE * h / 2)
    tl, tr = (cx - dw, cy - dh), (cx + dw, cy - dh)
    br, bl = (cx + dw, cy + dh), (cx - dw, cy + dh)

    if active:
        polygons = {
            "up":    [(0, 0), (w, 0), tr, tl],
            "down":  [(0, h), (w, h), br, bl],
            "left":  [(0, 0), tl, bl, (0, h)],
            "right": [(w, 0), tr, br, (w, h)],
        }
        overlay = img.copy()
        cv2.fillPoly(overlay, [np.array(polygons[active], np.int32)], (0, 255, 0))
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)

    for a, b in [((0, 0), tl), ((w, 0), tr), ((w, h), br), ((0, h), bl)]:
        cv2.line(img, a, b, (255, 255, 255), 1)
    cv2.rectangle(img, tl, br, (255, 255, 255), 2)

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "UP", (cx - 20, 28), font, 0.8, (255, 255, 255), 2)
    cv2.putText(img, "DOWN", (cx - 40, h - 12), font, 0.8, (255, 255, 255), 2)
    cv2.putText(img, "LEFT", (10, cy + 8), font, 0.8, (255, 255, 255), 2)
    cv2.putText(img, "RIGHT", (w - 100, cy + 8), font, 0.8, (255, 255, 255), 2)


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # CAP_DSHOW = faster/cleaner on Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # don't let old frames queue up (less lag)
    if not cap.isOpened():
        print("Could not open the camera. Try changing CAMERA_INDEX.")
        return

    detector = HandDetector(maxHands=1, detectionCon=0.8)

    smooth_x = smooth_y = None
    active_zone = None   # the section the hand is currently in (None = centre / no hand)
    last_fire = 0.0

    print(f"Sending moves to {UNITY_IP}:{UNITY_PORT}. Press Q in the window to quit.")

    while True:
        ok, img = cap.read()
        if not ok:
            break

        img = cv2.flip(img, 1)  # mirror so moving your hand right = right on screen
        h, w = img.shape[:2]
        now = time.time()

        hands, _ = detector.findHands(img, draw=False)

        zone = None
        if hands:
            hand = hands[0]
            lm = hand["lmList"]

            cx = sum(lm[i][0] for i in PALM_POINTS) / len(PALM_POINTS)
            cy = sum(lm[i][1] for i in PALM_POINTS) / len(PALM_POINTS)
            if smooth_x is None:
                smooth_x, smooth_y = cx, cy
            else:
                smooth_x += SMOOTHING * (cx - smooth_x)
                smooth_y += SMOOTHING * (cy - smooth_y)

            zone = get_zone(smooth_x, smooth_y, w, h)
        else:
            smooth_x = smooth_y = None  # hand left the frame

        # --- decide whether to send a move ---
        if zone is None:
            active_zone = None   # back in the centre (or no hand): reset
        elif now - last_fire >= MIN_INTERVAL:
            entered = zone != active_zone
            repeat = REPEAT_WHILE_HELD and now - last_fire >= REPEAT_INTERVAL
            if entered or repeat:
                sock.sendto(zone.encode("utf-8"), (UNITY_IP, UNITY_PORT))
                print("Sent:", zone)
                active_zone = zone
                last_fire = now

        # --- drawing ---
        draw_zones(img, zone)
        if hands:
            x, y, bw, bh = hands[0]["bbox"]
            cv2.rectangle(img, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
            cv2.circle(img, (int(smooth_x), int(smooth_y)), 9, (0, 255, 255), cv2.FILLED)

        cv2.imshow("2048 hand control", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()