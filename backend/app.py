from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from ultralytics import YOLO
import cv2
import time
import base64
import requests

# Constants
PROCESSING_RESOLUTION = (640, 384)
MODEL = YOLO('backend/N9.pt')

# Flask app setup
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


def process_video():
    """Main video processing loop that reads frames, runs detection, and streams to frontend."""
    print("=== Starting process_video ===")
    cap = cv2.VideoCapture('http://127.0.0.1:8080/live')
    #cap = cv2.VideoCapture('frontend/public/video/smoke4.mp4')
    print(f"VideoCapture opened: {cap.isOpened()}")
    frame_count = 0
    skip_frame = 0
    skip_frames = 4  # Process detection on 1/4 frames for better performance on weak computers

    while cap.isOpened():
        ret, frame = cap.read()
        print(f"Frame {frame_count}: read success={ret}, frame shape={frame.shape if ret else 'None'}")
        if not ret:
            print("End of video, looping back to start")
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Loop video
            continue
        frame_count += 1
        skip_frame += 1
        print(f"Processing frame {frame_count}, skip_frame={skip_frame}")

        # Save original frame for display
        raw_frame = frame.copy()
        original_height, original_width = frame.shape[:2]
        scale_x = original_width / PROCESSING_RESOLUTION[0]
        scale_y = original_height / PROCESSING_RESOLUTION[1]

        # Resize frame for processing (YOLO works better on smaller images)
        frame = cv2.resize(frame, PROCESSING_RESOLUTION)

        # Skip detection on most frames for performance, but still emit raw frame to frontend
        if skip_frame % skip_frames != 0:
            try:
                _, buffer = cv2.imencode('.jpg', raw_frame)
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                socketio.emit('video_frame', {'image': jpg_as_text})
            except Exception as e:
                print(f"Error encoding raw frame: {e}")
            time.sleep(0.01)  # Faster emission for non-detection frames
            continue

        try:
            # Run YOLO detection
            results = MODEL(frame)
            detected = False
            if len(results[0].boxes) > 0:
                print(f"Detected {len(results[0].boxes)} objects")
                for box in results[0].boxes:
                    class_id = int(box.cls.item())
                    confidence = box.conf.item()
                    print(f"Class: {class_id}, Confidence: {confidence:.2f}")
                    if class_id == 2:  # Only detect 'gas_leak'
                        if confidence > 0.6:  # Confidence threshold
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            # Draw on original frame with scaled coords
                            x1_orig = int(x1 * scale_x)
                            y1_orig = int(y1 * scale_y)
                            x2_orig = int(x2 * scale_x)
                            y2_orig = int(y2 * scale_y)
                            cv2.rectangle(raw_frame, (x1_orig, y1_orig), (x2_orig, y2_orig), (0, 255, 0), 2)
                            cv2.putText(raw_frame, f'Gas Leak {confidence:.2f}', (x1_orig, y1_orig-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                            detected = True
                            video_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # in seconds
                            alert_message = f'Gas leak {confidence:.2f} at {video_time:.2f}s!'

                            # Send alert to frontend
                            socketio.emit('gas_leak_event', {'status': alert_message})

                            # Send alert to Frappe MRP for GUI toast
                            try:
                                frappe_response = requests.post(
                                    'http://localhost:80/api/method/mrp.api.alert_handler.handle_gas_alert',
                                    headers={'Content-Type': 'application/json'},
                                    json={'message': alert_message},
                                    timeout=2  # Short timeout for realtime
                                )
                                print(f"🚀 Frappe alert request sent, status: {frappe_response.status_code}")
                            except Exception as e:
                                print(f"❌ Failed to send alert to Frappe: {e}")

                            print(f"🚨 Gas leak detected! Confidence: {confidence:.2f}, Video time: {video_time:.2f}s, Alert sent!")
                        else:
                            print(f"Low confidence: {confidence:.2f}")
                    else:
                        print(f"Wrong class: {class_id}")
            else:
                print("No detections")
        except Exception as e:
            print(f"Error in detection: {e}")

        try:
            # Encode raw frame (now with bounding boxes if detected) to base64
            _, buffer = cv2.imencode('.jpg', raw_frame)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('video_frame', {'image': jpg_as_text})
            print(f"Emitted detection frame {frame_count}")
        except Exception as e:
            print(f"Error encoding raw frame: {e}")

        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames (detection on 1/{skip_frames})")

        time.sleep(0.01)  # Control frame rate

# @socketio.on('manual_alert')
# def handle_manual_alert(data):
#     message = data.get('message', 'Manual smoke alert!')
#     socketio.emit('gas_leak_event', {'status': message})
#     print(f"🚨 Manual alert sent: {message}")

# @app.route('/execute_python', methods=['POST'])
# def execute_python():
#     try:
#         result = subprocess.run('python backend/example_script.py', shell=True, capture_output=True, text=True, cwd='.')
#         print("Script output:", result.stdout)
#         if result.stderr:
#             print("Script error:", result.stderr)
#         # No need to emit messages to frontend anymore
#         return jsonify({'status': 'success', 'output': result.stdout})
#     except Exception as e:
#         return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    socketio.start_background_task(process_video)
    socketio.run(app, debug=True, port=5000)
