# ------------------------------------------------------------
#  POSE TRACKER  -  School Project
#  Python + Flask (website) + OpenCV (camera/pictures) + MediaPipe (AI pose finder)
# ------------------------------------------------------------

import os
import uuid

import cv2
import numpy as np
import mediapipe as mp
from flask import Flask, render_template, request, Response, jsonify

app = Flask(__name__)

# Folder where uploaded videos are kept
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# MediaPipe tools:
#   mp_pose = the AI model that finds 33 body points
#   mp_draw = a helper that draws dots and lines on the body
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils


def track_pose(frame, pose):
    """Find the body in one picture (frame) and draw the skeleton on it."""

    # OpenCV uses BGR colours, MediaPipe wants RGB colours. So we convert.
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = pose.process(rgb)

    if result.pose_landmarks is None:
        cv2.putText(frame, "No person found", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return frame

    # Draw the dots and lines
    mp_draw.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # Fun part: are the hands up?
    # Point 15 and 16 = wrists, point 11 and 12 = shoulders.
    # In a picture, a SMALLER y number means HIGHER up.
    points = result.pose_landmarks.landmark
    hands_up = 0
    if points[15].y < points[11].y:
        hands_up += 1
    if points[16].y < points[12].y:
        hands_up += 1

    messages = {0: "Hands down", 1: "One hand up!", 2: "Both hands up!"}
    cv2.putText(frame, messages[hands_up], (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 0), 3)
    return frame


def make_stream(source):
    """Read a camera (source = 0) or a video file (source = path),
    track the pose on every frame, and send frames to the browser one by one."""

    cap = cv2.VideoCapture(source)
    try:
        with mp_pose.Pose(min_detection_confidence=0.5,
                          min_tracking_confidence=0.5) as pose:
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:          # camera failed or video finished
                    break

                # Make the picture smaller so the website stays fast
                height, width = frame.shape[:2]
                new_width = 640
                frame = cv2.resize(frame, (new_width, int(height * new_width / width)))

                frame = track_pose(frame, pose)

                ok, jpg = cv2.imencode(".jpg", frame)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")
    finally:
        cap.release()               # always switch the camera off


# ---------------------- WEBSITE PAGES ----------------------

@app.route("/")
def home():
    return render_template("index.html")



# OFFLINE mode 1: one photo
@app.route("/photo", methods=["POST"])
def photo():
    file = request.files.get("file")
    if file is None:
        return jsonify(error="Please choose a photo first."), 400

    data = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        return jsonify(error="That file is not a picture."), 400

    # static_image_mode=True means "this is a single photo, not a video"
    with mp_pose.Pose(static_image_mode=True) as pose:
        image = track_pose(image, pose)

    ok, jpg = cv2.imencode(".jpg", image)
    return Response(jpg.tobytes(), mimetype="image/jpeg")


# OFFLINE mode 2: a video file
@app.route("/upload_video", methods=["POST"])
def upload_video():
    file = request.files.get("file")
    if file is None:
        return jsonify(error="Please choose a video first."), 400

    name = uuid.uuid4().hex + ".mp4"        # a safe, unique name
    file.save(os.path.join(UPLOAD_FOLDER, name))
    return jsonify(name=name)


@app.route("/video_feed/<name>")
def video_feed(name):
    path = os.path.join(UPLOAD_FOLDER, os.path.basename(name))
    return Response(make_stream(path),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    # Open http://127.0.0.1:5000 in your browser
    app.run(debug=False, threaded=True)
