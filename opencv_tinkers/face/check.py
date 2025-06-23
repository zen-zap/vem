import cv2
import face_recognition
import numpy as np
import sqlite3
import pickle
from datetime import datetime

def load_known_faces():

    conn = sqlite3.connect('face.db')
    c = conn.cursor()
    c.execute("SELECT id, name, encoding FROM users")

    data = c.fetchall()
    # once fetched .. you could close the resource
    conn.close()

    # we're returning lists as usual -- feels weird returning them like this
    ids, names, encodings = [], [], []
    for uid, name, enc in data:
        ids.append(uid)
        names.append(name)
        encodings.append(pickle.loads(enc)) # this one loads the encodings of the face

    return ids, names, encodings


def already_marked_today(conn, user_id):

    today = datetime.now().date().isoformat()
    c = conn.cursor()
    c.execute("SELECT 1 FROM attendance WHERE user_id=? AND DATE(timestamp)=?", (user_id, today))

    return c.fetchone() is not None

def main():

    ids, names, encodings = load_known_faces()

    if not ids:
        print("nay registrations hath found")
        return

    cap = cv2.VideoCapture(0)

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)

        # this is the face to be recognised
        encs = face_recognition.face_encodings(rgb, locations)

        for _, enc in zip(locations, encs):

            matches = face_recognition.compare_faces(encodings, enc, tolerance=0.45)
            # this one is euclidean distance comparison -- pretty simple
            face_distances = face_recognition.face_distance(encodings, enc)

            # best match would be where the variation is the least
            best_match = np.argmin(face_distances) if face_distances.size else None

            name = "Unknown"
            user_id = None
            if best_match is not None and matches[best_match]:
                name = names[best_match]
                user_id = ids[best_match]
                # attendance is marked if not already for today
                with sqlite3.connect('face.db') as conn:
                    if not already_marked_today(conn, user_id):
                        c = conn.cursor()
                        now = datetime.now().isoformat()
                        c.execute("INSERT INTO attendance (user_id, timestamp) VALUES (?, ?)", (user_id, now))
                        conn.commit()
                        print(f"Attendance marked for {name} at {now}")

    cap.release()

if __name__ == "__main__":
    main()
