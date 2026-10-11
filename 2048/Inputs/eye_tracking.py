"""
Eye-tracking controller for the Unity 2048 game.

Look left / right / up / down and the script sends "left", "right", "up" or "down"
to Unity over UDP (default: 127.0.0.1:5006).

How it works:
  1. At start it spends ~2 seconds learning where your eyes sit when you look at
     the centre of the screen. Look at the middle and keep your head fairly still.
  2. Glance in a direction and hold it for a moment -> one move is sent.
  3. Look back to the centre to "re-arm" before the next move.
     (This stops the glance back to the middle counting as the opposite move.)

Install (PowerShell):
    pip install opencv-python mediapipe

Run:
    python eye_tracking_2048.py

Keys in the camera window:  C = recalibrate    Q = quit
Only run ONE camera script at a time (hand OR eye): they share the same webcam.
"""

import socket
import time

import cv2
import mediapipe as mp

# ----------------------------- settings -----------------------------
UNITY_IP = "127.0.0.1"   # same laptop as Unity
UNITY_PORT = 5006        # must match the Eye port on the UdpInputBridge in Unity
CAMERA_INDEX = 0         # try 1 if the wrong camera opens

H_THRESH = 0.09    # how far the iris must shift sideways to count (smaller = more sensitive)
V_THRESH = 0.08    # how far the iris must shift up/down to count
HOLD_TIME = 0.25   # seconds you must hold the glance
REARM_LEVEL = 0.5  # gaze must come back within 50% of the threshold before the next move
SMOOTHING = 0.4    # 0-1, higher = more responsive but more jittery
CALIB_SECONDS = 2.0
BLINK_OPEN_MIN = 0.12  # eye height / eye width below this = blink, frame is ignored
# ---------------------------------------------------------------------

# MediaPipe face-mesh landmark numbers (iris points need refine_landmarks=True).
RIGHT_EYE = {"outer": 33, "inner": 133, "top": 159, "bottom": 145, "iris": 468}
LEFT_EYE = {"outer": 263, "inner": 362, "top": 386, "bottom": 374, "iris": 473}


def eye_values(pt, eye):
    """Returns (horizontal ratio, vertical ratio, openness) for one eye.

    horizontal: 0 = iris at one corner, 1 = at the other (rises when looking right)
    vertical:   0 = iris at the upper lid, 1 = at the lower lid (rises when looking down)
    """
    ox, _ = pt(eye["outer"])
    ix, _ = pt(eye["inner"])
    _, ty = pt(eye["top"])
    _, by = pt(eye["bottom"])
    cx, cy = pt(eye["iris"])

    left_x, right_x = min(ox, ix), max(ox, ix)
    width = max(right_x - left_x, 1e-6)
    height = max(by - ty, 1e-6)

    return (cx - left_x) / width, (cy - ty) / height, height / width


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)  # CAP_DSHOW = cleaner on Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("Could not open the camera. Try changing CAMERA_INDEX.")
        return

    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,          # needed for the iris landmarks
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    smooth_h = smooth_v = None
    base_h = base_v = None
    calib_start = None
    calib_samples = []

    armed = True
    hold_dir = None
    hold_start = 0.0
    last_sent = ""
    show_until = 0.0

    print(f"Sending moves to {UNITY_IP}:{UNITY_PORT}. C = recalibrate, Q = quit.")

    while True:
        ok, img = cap.read()
        if not ok:
            break

        img = cv2.flip(img, 1)  # mirror: looking to your right = right on screen
        h, w = img.shape[:2]
        now = time.time()

        result = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        status = ""

        if result.multi_face_landmarks:
            lms = result.multi_face_landmarks[0].landmark

            def pt(i):
                return lms[i].x * w, lms[i].y * h

            rh, rv, r_open = eye_values(pt, RIGHT_EYE)
            lh, lv, l_open = eye_values(pt, LEFT_EYE)

            # Mark the irises so you can see it's tracking them
            for eye in (RIGHT_EYE, LEFT_EYE):
                ix, iy = pt(eye["iris"])
                cv2.circle(img, (int(ix), int(iy)), 4, (0, 255, 0), cv2.FILLED)

            if (r_open + l_open) / 2 < BLINK_OPEN_MIN:
                hold_dir = None  # blinking, ignore this frame
                status = "blink"
            else:
                cur_h = (rh + lh) / 2
                cur_v = (rv + lv) / 2
                if smooth_h is None:
                    smooth_h, smooth_v = cur_h, cur_v
                else:
                    smooth_h += SMOOTHING * (cur_h - smooth_h)
                    smooth_v += SMOOTHING * (cur_v - smooth_v)

                if base_h is None:
                    # --- calibration: average where the eyes sit when looking at the centre ---
                    if calib_start is None:
                        calib_start = now
                    calib_samples.append((smooth_h, smooth_v))
                    status = "Calibrating - look at the centre of the screen..."
                    if now - calib_start >= CALIB_SECONDS and calib_samples:
                        base_h = sum(s[0] for s in calib_samples) / len(calib_samples)
                        base_v = sum(s[1] for s in calib_samples) / len(calib_samples)
                        print("Calibrated.")
                else:
                    nh = (smooth_h - base_h) / H_THRESH   # 1.0 = threshold reached
                    nv = (smooth_v - base_v) / V_THRESH
                    magnitude = max(abs(nh), abs(nv))

                    direction = None
                    if armed:
                        if magnitude >= 1.0:
                            if abs(nh) >= abs(nv):
                                direction = "right" if nh > 0 else "left"
                            else:
                                direction = "down" if nv > 0 else "up"
                    elif magnitude < REARM_LEVEL:
                        armed = True

                    if direction is None:
                        hold_dir = None
                    elif direction != hold_dir:
                        hold_dir = direction
                        hold_start = now
                    elif now - hold_start >= HOLD_TIME:
                        sock.sendto(direction.encode("utf-8"), (UNITY_IP, UNITY_PORT))
                        print("Sent:", direction)
                        last_sent = direction
                        show_until = now + 0.6
                        armed = False
                        hold_dir = None

                    status = f"h {nh:+.2f}  v {nv:+.2f}  (1.00 = move)" + ("" if armed else "  look at centre")
        else:
            hold_dir = None
            status = "No face found"

        # On-screen feedback
        if now < show_until:
            cv2.putText(img, last_sent.upper(), (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 0), 4)
        cv2.putText(img, status, (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("2048 eye control", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("c"):  # start calibration again
            base_h = base_v = None
            calib_start = None
            calib_samples = []
            armed = True
            hold_dir = None

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()