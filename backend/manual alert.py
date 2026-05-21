from pynput import keyboard
import socketio

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print('Connected to server')

@sio.event
def disconnect():
    print('Disconnected from server')

def on_press(key):
    try:
        if key.char == 'a':
            sio.emit('manual_alert', {'message': 'Manual smoke alert!'})
            print("Manual alert sent!")
    except AttributeError:
        pass  # Special keys

# Connect to the server
sio.connect('http://localhost:5000')

# Start listening for key presses
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
