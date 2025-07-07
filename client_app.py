from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import os
import requests
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
    from socket_client import SpotifyClient
    print("✅ SpotifyClient imported successfully")
except Exception as e:
    print(f"❌ Error importing SpotifyClient: {e}")
    SpotifyClient = None

app = Flask(__name__)
app.secret_key = 'spotify_cloud_client_secret_key_2024'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Server configuration
SERVER_URL = 'http://localhost:5001'

# Global variables
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
    return render_template('client_index.html')

@app.route('/upload')
def upload():
    return render_template('client_upload.html')

@app.route('/download')
def download():
    return render_template('client_download.html')

@app.route('/security')
def security():
    return render_template('client_security.html')

# API Routes
@app.route('/api/server-status')
def server_status():
    try:
        response = requests.get(f'{SERVER_URL}/api/server-status', timeout=5)
        return jsonify(response.json())
    except requests.exceptions.RequestException:
        return jsonify({'running': False, 'error': 'Không thể kết nối đến server'})

@app.route('/api/start-server', methods=['POST'])
def start_server():
    try:
        response = requests.post(f'{SERVER_URL}/api/start-server', timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Không thể kết nối đến server: {str(e)}'})

@app.route('/api/stop-server', methods=['POST'])
def stop_server():
    try:
        response = requests.post(f'{SERVER_URL}/api/stop-server', timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Không thể kết nối đến server: {str(e)}'})

@app.route('/api/files')
def list_files():
    try:
        response = requests.get(f'{SERVER_URL}/api/files', timeout=5)
        return jsonify(response.json())
    except requests.exceptions.RequestException:
        return jsonify({'error': 'Không thể kết nối đến server'})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    try:
        # Check if server is running
        server_status_response = requests.get(f'{SERVER_URL}/api/server-status', timeout=5)
        if not server_status_response.json().get('running', False):
            return jsonify({
                'success': False, 
                'message': 'Server chưa được khởi động. Vui lòng khởi động server trước.'
            })
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Không có file được chọn'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Không có file được chọn'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Định dạng file không được hỗ trợ'})
        
        simulate_tampering = request.form.get('simulate_tampering') == 'true'
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(UPLOAD_FOLDER, 'temp_' + filename)
        ensure_upload_folder()
        file.save(temp_filepath)
        
        try:
            # Use socket client to upload
            if not SpotifyClient:
                return jsonify({'success': False, 'message': 'SpotifyClient không khả dụng'})
            
            client = SpotifyClient()
            if client.connect():
                result = client.upload_file(temp_filepath, simulate_tampering)
                client.disconnect()
                
                if result['status'] == 'ACK':
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                    return jsonify({
                        'success': True,
                        'message': 'Upload thành công',
                        'security_info': {
                            'handshake': True,
                            'key_exchange': True,
                            'encryption': True,
                            'signature': True,
                            'verification': True
                        }
                    })
                else:
                    # Nếu upload thất bại, xóa file tạm
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath)
                    return jsonify({
                        'success': False,
                        'message': result.get('message', 'Upload thất bại'),
                        'security_error': {
                            'type': result.get('error', 'unknown'),
                            'message': result.get('message', 'Lỗi không xác định'),
                            'details': 'Hệ thống đã phát hiện và từ chối dữ liệu bị sửa đổi'
                        }
                    })
            else:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                return jsonify({'success': False, 'message': 'Không thể kết nối đến server socket'})
                
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return jsonify({'success': False, 'message': f'Lỗi upload: {str(e)}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download', methods=['POST'])
def api_download():
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'message': 'Tên file không được cung cấp'})
        
        # Check if server is running
        server_status_response = requests.get(f'{SERVER_URL}/api/server-status', timeout=5)
        if not server_status_response.json().get('running', False):
            return jsonify({
                'success': False, 
                'message': 'Server chưa được khởi động. Vui lòng khởi động server trước.'
            })
        
        # Use socket client to download
        if not SpotifyClient:
            return jsonify({'success': False, 'message': 'SpotifyClient không khả dụng'})
        
        DOWNLOAD_FOLDER = 'downloads'
        if not os.path.exists(DOWNLOAD_FOLDER):
            os.makedirs(DOWNLOAD_FOLDER)
        save_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        client = SpotifyClient()
        if client.connect():
            result = client.download_file(filename, save_path)
            client.disconnect()
            
            if result['status'] == 'SUCCESS' or result['status'] == 'ACK':
                return jsonify({
                    'success': True,
                    'message': 'Download thành công',
                    'file_path': save_path,
                    'security_info': {
                        'handshake': True,
                        'key_exchange': True,
                        'decryption': True,
                        'signature_verification': True,
                        'integrity_check': True
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': result.get('message', 'Download thất bại')
                })
        else:
            return jsonify({'success': False, 'message': 'Không thể kết nối đến server socket'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    try:
        response = requests.post(f'{SERVER_URL}/api/delete-file', 
                               json=request.get_json(), 
                               timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Không thể kết nối đến server: {str(e)}'})

@app.route('/api/download-file/<filename>')
def download_file(filename):
    try:
        response = requests.get(f'{SERVER_URL}/api/download-file/{filename}', 
                              stream=True, 
                              timeout=30)
        if response.status_code == 200:
            return response.content, 200, {
                'Content-Type': response.headers.get('Content-Type', 'application/octet-stream'),
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        else:
            return jsonify({'error': 'File không tồn tại'}), 404
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Không thể kết nối đến server: {str(e)}'}), 500

@app.route('/api/test-aesgcm', methods=['POST'])
def test_aesgcm():
    try:
        if not crypto_manager:
            return jsonify({'success': False, 'message': 'CryptoManager không khả dụng'})
        
        data = request.get_json()
        test_data = data.get('data', 'Hello World!')
        
        # Test encryption
        encrypted_data = crypto_manager.encrypt_aesgcm(test_data.encode())
        
        # Test decryption
        decrypted_data = crypto_manager.decrypt_aesgcm(encrypted_data)
        
        if decrypted_data.decode() == test_data:
            return jsonify({
                'success': True,
                'message': 'AES-GCM test thành công',
                'original': test_data,
                'encrypted': encrypted_data.hex()[:50] + '...',
                'decrypted': decrypted_data.decode()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'AES-GCM test thất bại - dữ liệu không khớp'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test-rsa', methods=['POST'])
def test_rsa():
    try:
        if not crypto_manager:
            return jsonify({'success': False, 'message': 'CryptoManager không khả dụng'})
        
        data = request.get_json()
        test_data = data.get('data', 'Hello World!')
        
        # Test RSA encryption/decryption
        encrypted_data = crypto_manager.encrypt_rsa(test_data.encode())
        decrypted_data = crypto_manager.decrypt_rsa(encrypted_data)
        
        # Test RSA signing/verification
        signature = crypto_manager.sign_rsa(test_data.encode())
        is_valid = crypto_manager.verify_rsa(test_data.encode(), signature)
        
        if decrypted_data.decode() == test_data and is_valid:
            return jsonify({
                'success': True,
                'message': 'RSA test thành công',
                'original': test_data,
                'encrypted': encrypted_data.hex()[:50] + '...',
                'decrypted': decrypted_data.decode(),
                'signature_valid': is_valid
            })
        else:
            return jsonify({
                'success': False,
                'message': 'RSA test thất bại'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test-sha512', methods=['POST'])
def test_sha512():
    try:
        if not crypto_manager:
            return jsonify({'success': False, 'message': 'CryptoManager không khả dụng'})
        
        data = request.get_json()
        test_data = data.get('data', 'Hello World!')
        
        # Test SHA-512
        hash_value = crypto_manager.hash_sha512(test_data.encode())
        
        # Test verification
        is_valid = crypto_manager.verify_sha512(test_data.encode(), hash_value)
        
        if is_valid:
            return jsonify({
                'success': True,
                'message': 'SHA-512 test thành công',
                'original': test_data,
                'hash': hash_value.hex(),
                'verification': is_valid
            })
        else:
            return jsonify({
                'success': False,
                'message': 'SHA-512 test thất bại'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test-socket', methods=['POST'])
def test_socket():
    try:
        if not SpotifyClient:
            return jsonify({'success': False, 'message': 'SpotifyClient không khả dụng'})
        
        client = SpotifyClient()
        if client.connect():
            client.disconnect()
            return jsonify({
                'success': True,
                'message': 'Socket connection test thành công'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Socket connection test thất bại'
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def test_initial_handshake():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 8888))
        s.send("Hello!".encode())
        response = s.recv(1024).decode()
        print(f"[HANDSHAKE TEST] Gửi: Hello! | Nhận: {response}")
        s.close()
    except Exception as e:
        print(f"[HANDSHAKE TEST] Lỗi: {e}")

if __name__ == '__main__':
    ensure_upload_folder()
    print("🚀 Starting Spotify Cloud Client...")
    print("📁 Upload folder:", os.path.abspath(UPLOAD_FOLDER))
    print("🌐 Client will be available at: http://localhost:5000")
    print("🔗 Connecting to server at:", SERVER_URL)
    # Test handshake khi khởi động
    test_initial_handshake()
    app.run(host='0.0.0.0', port=5000, debug=True) 