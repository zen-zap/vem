
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time

# ——— Setup ————————————————————————————————————————————
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75
)
mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

# Smoothing parameters
smoothening = 5
prev_x, prev_y = 0, 0
curr_x, curr_y = 0, 0

# Click cooldown
click_threshold = 30  # pixel distance on frame
click_cd = 0.3        # seconds
last_click_time = time.time()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        lm = results.multi_hand_landmarks[0]
        # Draw hand skeleton
        mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS,
                               mp_draw.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                               mp_draw.DrawingSpec(color=(0,0,255), thickness=2))

        # Get normalized landmarks
        nx = lm.landmark[8].x
        ny = lm.landmark[8].y

        # Map to screen coordinates
        target_x = np.interp(nx, [0,1], [0, screen_w])
        target_y = np.interp(ny, [0,1], [0, screen_h])

        # Smoothing to reduce jitter
        curr_x = prev_x + (target_x - prev_x) / smoothening
        curr_y = prev_y + (target_y - prev_y) / smoothening
        prev_x, prev_y = curr_x, curr_y

        # Move the OS cursor
        pyautogui.moveTo(curr_x, curr_y, duration=0.01)

        # Draw your “cursor” on the frame
        draw_x = int(np.interp(curr_x, [0, screen_w], [0, w]))
        draw_y = int(np.interp(curr_y, [0, screen_h], [0, h]))
        cv2.circle(frame, (draw_x, draw_y), 12, (255, 0, 0), cv2.FILLED)

        # Click detection via pinch
        x_thumb = int(lm.landmark[4].x * w)
        y_thumb = int(lm.landmark[4].y * h)
        x_index = int(lm.landmark[8].x * w)
        y_index = int(lm.landmark[8].y * h)
        dist = np.hypot(x_index - x_thumb, y_index - y_thumb)

        if dist < click_threshold and (time.time() - last_click_time) > click_cd:
            last_click_time = time.time()
            pyautogui.click()
            # Visual feedback on click
            cv2.circle(frame, (draw_x, draw_y), 20, (0,255,0), 3)

    # Show FPS (optional, for performance tuning)
    # fps = int(1/(time.time() - start_time))
    # cv2.putText(frame, f'FPS: {fps}', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)


cap.release()
