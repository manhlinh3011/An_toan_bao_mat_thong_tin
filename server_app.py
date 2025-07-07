from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import time
import json
from werkzeug.utils import secure_filename

# Import với error handling
try:
    from crypto_utils import CryptoManager
    print("✅ CryptoManager imported successfully")
except Exception as e:
    print(f"❌ Error importing CryptoManager: {e}")
    CryptoManager = None

try:
    from socket_server import SpotifyCloudServer
    print("✅ SpotifyCloudServer imported successfully")
except Exception as e:
    print(f"❌ Error importing SpotifyCloudServer: {e}")
    SpotifyCloudServer = None

app = Flask(__name__)
app.secret_key = 'spotify_cloud_server_secret_key_2024'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global variables
server_instance = None
server_thread = None
crypto_manager = CryptoManager() if CryptoManager else None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

# Routes
@app.route('/')
def index():
    return render_template('server_index.html')

@app.route('/files')
def files():
    return render_template('server_files.html')

@app.route('/logs')
def logs():
    return render_template('server_logs.html')

# API Routes
@app.route('/api/server-status')
def server_status():
    global server_instance
    try:
        return jsonify({
            'running': server_instance is not None and hasattr(server_instance, 'running') and server_instance.running
        })
    except Exception as e:
        return jsonify({'running': False, 'error': str(e)})

@app.route('/api/start-server', methods=['POST'])
def start_server():
    global server_instance, server_thread

    try:
        if not SpotifyCloudServer:
            return jsonify({'success': False, 'message': 'SpotifyCloudServer không khả dụng'})

        if server_instance and server_instance.running:
            return jsonify({'success': False, 'message': 'Server đã đang chạy'})

        server_instance = SpotifyCloudServer()
        server_thread = threading.Thread(target=server_instance.start_server)
        server_thread.daemon = True
        server_thread.start()

        # Wait a bit to ensure server starts
        time.sleep(1)

        return jsonify({'success': True, 'message': 'Server đã được khởi động'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stop-server', methods=['POST'])
def stop_server():
    global server_instance
    
    try:
        if server_instance:
            server_instance.stop_server()
            server_instance = None
        
        return jsonify({'success': True, 'message': 'Server đã được dừng'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/files')
def list_files():
    ensure_upload_folder()
    
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if allowed_file(filename):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
        
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': 'Tên file không được cung cấp'})
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'success': True, 'message': f'File {filename} đã được xóa'})
        else:
            return jsonify({'success': False, 'message': 'File không tồn tại'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download-file/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File không tồn tại'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/server-logs')
def get_server_logs():
    try:
        if server_instance and hasattr(server_instance, 'logs'):
            return jsonify({'logs': server_instance.logs})
        else:
            return jsonify({'logs': []})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    ensure_upload_folder()
    print("🚀 Starting Spotify Cloud Server...")
    print("📁 Upload folder:", os.path.abspath(UPLOAD_FOLDER))
    print("🌐 Server will be available at: http://localhost:5001")
    # Tự động khởi động server socket khi chạy Flask
    if SpotifyCloudServer:
        if not server_instance:
            server_instance = SpotifyCloudServer()
            server_thread = threading.Thread(target=server_instance.start_server)
            server_thread.daemon = True
            server_thread.start()
            print("[AUTO] Đã tự động khởi động server socket (port 8888)")
    app.run(host='0.0.0.0', port=5001, debug=True) 