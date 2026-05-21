from flask import Flask, Response, send_file
import cv2
import time

app = Flask(__name__)

def gen():
    cap = cv2.VideoCapture('http://localhost:5001/video_feed')
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.01)  # ~10 fps

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Video Stream</title>
    </head>
    <body>
        <h1>Smoke Video Stream</h1>
        <img src="/video_feed" style="max-width: 100%; height: auto;">
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
