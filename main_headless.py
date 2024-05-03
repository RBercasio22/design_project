from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
from threading import Thread
import numpy as np
import imutils
import time
import dlib
import cv2
import threading
import pyrebase

config = {
    "apiKey": "AIzaSyCWl5-CwN2NYh_RZm1-P1O0l99Ete2pJe0",
    "authDomain": "eyeblinker-status.firebaseapp.com",
    "databaseURL": "https://eyeblinker-status-default-rtdb.firebaseio.com",
    "storageBucket": "eyeblinker-status.appspot.com",
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()

from playAlarm import *
from gps import *

location = 0
while location == 0:
    location = getLocation()


def schedule_function(interval):
    t = threading.Timer(interval, schedule_function, args=[interval])
    t.start()
    getLocation()


interval = 10
schedule_function(interval)


def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear


predictor_file = "shape_predictor_68_face_landmarks.dat"

EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 80
COUNTER = 0
HIGH_EAR_COUNTER = 0
ALARM_ON = False
AWAY_COUNTER = 0
AWAY_SENT = False

print("[INFO] loading facial landmark predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_file)
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
print("[INFO] starting video stream thread...")
vs = VideoStream(0).start()
vs.stream.set(3, 640)
vs.stream.set(4, 480)
time.sleep(1.0)

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=450)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    if not rects:
        if AWAY_COUNTER % 50 == 0 or AWAY_COUNTER == 0:
            print(f"AWAY: {AWAY_COUNTER}")
        AWAY_COUNTER += 1
        if AWAY_COUNTER > 100:
            if not AWAY_SENT:
                AWAY_SENT = True
                db.child("updates").update({"status": "NOT_FOUND"})

    else:
        if AWAY_SENT:
            db.child("updates").update({"status": "NORMAL"})
            COUNTER = 0
            AWAY_SENT = False
        AWAY_COUNTER = 0

    for rect in rects:
        shape = predictor(gray, rect)
        shape = face_utils.shape_to_np(shape)
        leftEye = shape[lStart:lEnd]
        rightEye = shape[rStart:rEnd]
        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)

        print(f"counter: {COUNTER}")
        print(f"high c : {HIGH_EAR_COUNTER}")
        if ear < EYE_AR_THRESH:
            COUNTER += 1
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                playAlarm()
                COUNTER = 0
        else:
            if HIGH_EAR_COUNTER > 10:
                COUNTER = 0
            else:
                HIGH_EAR_COUNTER += 1


    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()