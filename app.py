from flask import Flask, jsonify, request, send_file, abort
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

VIDEO_DIRECTORY = "../HumanFallDetection/saved_falls"

@app.route('/video/<path:filename>')
def serve_video(filename):
    file_path = os.path.join(VIDEO_DIRECTORY, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Video not found"}), 404
    
    # Range handling for video playback
    range_header = request.headers.get('Range', None)
    if range_header:
        start, end = range_header.strip().split('=')[1].split('-')
        start = int(start)
        file_size = os.path.getsize(file_path)
        end = int(end) if end else file_size - 1
        length = end - start + 1

        with open(file_path, 'rb') as f:
            f.seek(start)
            video_bytes = f.read(length)

        headers = {
            'Content-Range': f'bytes {start}-{end}/{file_size}',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(length),
            'Content-Type': 'video/mp4',
        }

        return video_bytes, 206, headers

    return send_file(file_path, mimetype='video/mp4')

@app.route('/metadata', methods=['GET'])
def get_metadata():
    metadata_path = os.path.join(VIDEO_DIRECTORY, 'fall_metadata.json')
    if not os.path.exists(metadata_path):
        return jsonify({"error": "No metadata found"}), 404
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    return jsonify(metadata)

# WebSocket endpoint for real-time notifications
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def send_notification(event_type, message):
    """Send a real-time notification to all connected clients."""
    notification_data = {
        "type": event_type,
        "message": message,
        "timestamp": datetime.datetime.now().isoformat()
    }
    socketio.emit('new_notification', notification_data)

# Endpoint to trigger notifications for testing
@app.route('/trigger-notification', methods=['POST'])
def trigger_notification():
    data = request.json
    send_notification(data['type'], data['message'])
    return jsonify({"status": "Notification sent"}), 200

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5000, debug=True)
    