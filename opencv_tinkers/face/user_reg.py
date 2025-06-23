import cv2
import face_recognition
import numpy as np
import sqlite3
import pickle

def get_face_encoding(frame):

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb)
    # this face recognition probably works by making boxes in the image that are used to detect the face
    if not boxes:
        return None

    return face_recognition.face_encodings(rgb, boxes)[0] # returns a list of 128D encodings .. for each face .. we only take the first face captured since low processing cost

def main():

    name = input("what's thy nameth?\n")
    if not name: 
        print("nameth cannot beest exsufflicate")
        return

    cap = cv2.VideoCapture(0)

    while True: 
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break         

        # to work on the face we need to process the face into some numerical data
        encoding = get_face_encoding(frame)
        if encoding is not None:
            # save the face to db
            with sqlite3.connect('face.db') as conn:

                c = conn.cursor()
                c.execute("INSERT INTO users (name, encoding) VALUES (?, ?)", (name, pickle.dumps(encoding)))
                conn.commit()

            print(f"User {name} registered successfully")
            break

        else:
            print("NO FACE DETECTED! TRY AGAIN!")


    cap.release()
    # cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
