import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import subprocess # we need something to run the system commands to control volume and stuff
import time

mp_hands = mp.solutions.hands

# this is somewhat of a pipeline to detect and track hands
hands = mp_hands.Hands(
    static_image_mode=False, # we're working on video so .. 
    max_num_hands=1, # it is faster to track only one hand
    min_detection_confidence=0.8,  # higher for more reliable detection
    min_tracking_confidence=0.8
)
mp_draw = mp.solutions.drawing_utils  # you need to draw the landmarks on the hands .. the vector points to be precise

screen_w, screen_h = pyautogui.size()

cap = cv2.VideoCapture(0) # get the default camera ... can also be -1

if not cap.isOpened(): # check if camera open
    print("Error: Could not open video source.")
    exit()

# now initially we had the mouse movements as erratic ... so here we're gonna apply some slowing down .. like the movement gets smoother
smooth_factor = 0.15  # lower = smoother
# this factor is going to be used later for finding the mouse position wrt our finger position
prev_x, prev_y = None, None

# --- Volume control params ---
last_vol_change = 0
vol_cooldown = 0.1  # seconds, for rapid but not continuous volume changes
vol_min_dist = 40   # min spread for volume to start changing (pixels)
vol_max_dist = 200  # max spread for full volume change
vol_last_level = None  # for feedback display

def set_volume(percent):

    percent = int(np.clip(percent, 0, 100)) # to make sure they stay within a range -- when hand movements vary they many send very high or very low values .. they are all clipped to [0, 100] window
    # setting volume through amixer tool
    subprocess.call(['amixer', 'set', 'Master', f'{percent}%'])

while True:
    # we need to get frames of the webcam
    ret, frame = cap.read()
    if not ret:
        break

    # now normally .. we see the screen from our perspective .. so for cursor control .. we need to flip the view vertically
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # mediapipe works on RGB frames
    results = hands.process(rgb) # sending the RGB frame to the pipeline .. made earlier

    if results.multi_hand_landmarks: # if we get the coordinates then we proceed further

        for hand_landmarks in results.multi_hand_landmarks: # for the knuckle points to appear .. we need this 

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS) # we display the knuckle points where they are detected

            # so goal is to track index finger ... landmark 8 ... for the tip
            x = hand_landmarks.landmark[8].x
            y = hand_landmarks.landmark[8].y

            # just normal calculation of the relative mouse position -- 
            # mapping of pixels on screen to x and y 
            mouse_x = int(x * screen_w)
            mouse_y = int(y * screen_h)

            # Smoothing (exponential moving average) -- we do this for slower and smoother mouse movements
            if prev_x is None:
                prev_x, prev_y = mouse_x, mouse_y
            else:
                # on successive frames .. we blend our previous position with the current one .. 
                # so kinda fluid ? or smoother to say...
                mouse_x = int(prev_x + (mouse_x - prev_x) * smooth_factor)
                mouse_y = int(prev_y + (mouse_y - prev_y) * smooth_factor)
                prev_x, prev_y = mouse_x, mouse_y

            # this one controls the system mouse  -- did not work when there was conflict between cv2 and pyqt5 -- also use X11 .. limited support for Wayland
            pyautogui.moveTo(mouse_x, mouse_y, duration=0)
            
            # to find the pinch to detect clicks and all that .. we need distance calculations
            x_thumb = hand_landmarks.landmark[4].x * frame.shape[1]
            y_thumb = hand_landmarks.landmark[4].y * frame.shape[0]
            x_index = hand_landmarks.landmark[8].x * frame.shape[1]
            y_index = hand_landmarks.landmark[8].y * frame.shape[0]

            pinch_dist = np.hypot(x_index - x_thumb, y_index - y_thumb) # general euclidean distance calc

            # kept this at 20 .. I couldn't operate with larger values .. clicks were too sensitive
            if pinch_dist < 20:
                pyautogui.click()

            # volume control
            now = time.time()
            x_pinky = hand_landmarks.landmark[20].x * frame.shape[1]
            y_pinky = hand_landmarks.landmark[20].y * frame.shape[0]
            pinky_thumb_dist = np.hypot(x_pinky - x_thumb, y_pinky - y_thumb)

            if pinky_thumb_dist > vol_min_dist:
                # we clip it in the function itself .. but well .. doesn't hurt to do it here .. maybe remove this and try
                vol_percent = int(
                    np.clip(
                        (pinky_thumb_dist - vol_min_dist) / (vol_max_dist - vol_min_dist) * 100,
                        0, 100
                    )
                )
                # we change the volume after some cooldown passes
                if (now - last_vol_change > vol_cooldown) and (vol_percent != vol_last_level):
                    set_volume(vol_percent)
                    vol_last_level = vol_percent
                    last_vol_change = now

# .. this is just to release the captured web cam from earlier 
cap.release()
