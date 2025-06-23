import cv2
import mediapipe as mp
import numpy as np
import pyautogui

# we gotta initialize mediapipe's hand initializer
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.6
    )

mp_draw = mp.solutions.drawing_utils

# getting the screen size .. we gonna need this to map the mouse
screen_w, screen_h = pyautogui.size()

print(screen_h, screen_w)

# to get webcam?
cap = cv2.VideoCapture(0) # 0 or -1 used to refer to default cameras

if not cap.isOpened():
    print("Error: Could not open video source.")
    exit()

while True: 
    ret, frame = cap.read()  # ret is a boolean that tells whether the frame was successfully read

    if not ret: 
        break

    frame = cv2.flip(frame, 1)  # > 0 flips horizontally
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    # if a hand is detected --- we get landmarks? .. what are landmarks?
    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(frame, hand_landmarks)

            # index finger tip .. how?? -- so we're tracking the index finger here
            x = hand_landmarks.landmark[8].x
            y = hand_landmarks.landmark[8].y

            # thumb finger is landmark[4]

            # coordinates [0,1] to screen pixels -- you normalize them ? ... faster processing?
            mouse_x = int(x * screen_w)
            mouse_y = int(y * screen_h)
            pyautogui.moveTo(mouse_x, mouse_y, duration=0.01)

            # so for a click gesture -- we check the distance between thumb tip and index tip
            x_thumb = hand_landmarks.landmark[4].x * frame.shape[1]
            y_thumb = hand_landmarks.landmark[4].y * frame.shape[0]
            x_index = hand_landmarks.landmark[8].x * frame.shape[1]
            y_index = hand_landmarks.landmark[8].y * frame.shape[0]

            pinch_dist = np.hypot(x_index - x_thumb, y_index - y_thumb)
            if pinch_dist < 20:
                pyautogui.click()

            # we some feedback too .. 
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

cap.release()


# there is no smoothing here 
