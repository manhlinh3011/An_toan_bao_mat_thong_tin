#nhận upload: giải mã file bằng AES-GCM, kiểm tra tag để xác thực toàn vẹn.
import socket
import threading
import json
import os
import time
from crypto_utils import CryptoManager

class SpotifyCloudServer: 
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.crypto = CryptoManager()
        self.server_socket = None
        self.running = False
        self.upload_dir = 'uploads'
        
        # Tạo thư mục uploads nếu chưa có
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            
    def start_server(self): #khởi động server socket
        """Khởi động server socket"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"Spotify Cloud Server đang chạy tại {self.host}:{self.port}")

            while self.running:
                try:
                    self.server_socket.settimeout(1.0)  # Timeout để có thể check running flag
                    client_socket, address = self.server_socket.accept()
                    print(f"Kết nối từ {address}")

                    # Tạo thread mới cho mỗi client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()

                except socket.timeout:
                    continue  # Timeout bình thường, tiếp tục loop
                except Exception as e:
                    if self.running:
                        print(f"Lỗi server: {e}")
                        break
        except Exception as e:
            print(f"Lỗi khởi động server: {e}")
            self.running = False
                    
    def handle_client(self, client_socket, address): #xử lý client connection gui khoa 
        """Xử lý client connection"""
        try:
            # Handshake
            message = client_socket.recv(1024).decode()
            print(f"[SERVER] Nhận handshake: {message}")
            if message == "Hello!":
                client_socket.send("Ready!".encode())
                print(f"[SERVER] Gửi: Ready! cho {address}")
                print(f"Handshake thành công với {address}")
            else:
                client_socket.send("Invalid handshake".encode())
                print(f"[SERVER] Handshake thất bại với {address}")
                return
                
            # Gửi public key cho client
            public_key_pem = self.crypto.get_public_key_pem()
            client_socket.send(public_key_pem.encode())
            
            # Nhận và xử lý yêu cầu
            while True:
                try:
                    # Nhận kích thước dữ liệu trước
                    size_data = client_socket.recv(8).decode()
                    if not size_data:
                        break

                    data_size = int(size_data)

                    # Nhận dữ liệu theo kích thước
                    data = b''
                    while len(data) < data_size:
                        chunk = client_socket.recv(min(4096, data_size - len(data)))
                        if not chunk:
                            break
                        data += chunk

                    if len(data) != data_size:
                        break
                    print(f"[SERVER] Raw data received (len={len(data)}): {data[:200]}")  # In 200 bytes đầu
                    print(f"[SERVER] Decoded data: {data.decode(errors='replace')[:200]}")
                    request = json.loads(data.decode())
                    
                    client_public_key_pem = request.get('client_public_key')
                    
                    if request['type'] == 'upload':
                        response = self.handle_upload(request)
                    elif request['type'] == 'download':
                        response = self.handle_download(request)
                    else:
                        response = {'status': 'error', 'message': 'Unknown request type'}
                        
                    print("DEBUG: Sending response:", response)
                    response_bytes = json.dumps(response).encode()
                    print(f"[SERVER] Sending response (size={len(response_bytes)}): {response}")  # Thêm dòng này

                    size = str(len(response_bytes)).zfill(8).encode()
                    client_socket.send(size)
                    client_socket.send(response_bytes)     
                    break                
                except json.JSONDecodeError:
                    response = {'status': 'error', 'message': 'Invalid JSON'}
                    response_bytes = json.dumps(response).encode()
                    size = str(len(response_bytes)).zfill(8).encode()
                    print(f"[SERVER] Sending response (size={len(response_bytes)}): {response}")  # Thêm dòng này

                    client_socket.send(size)
                    client_socket.send(response_bytes)
                    break 
                except Exception as e:
                    response = {'status': 'error', 'message': str(e)}
                    response_bytes = json.dumps(response).encode()
                    print(f"[SERVER] Sending response (size={len(response_bytes)}): {response}")  # Thêm dòng này

                    size = str(len(response_bytes)).zfill(8).encode()
                    client_socket.send(size)
                    client_socket.send(response_bytes)
                    break 
        except Exception as e:
            print(f"Lỗi xử lý client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Đóng kết nối với {address}")
            
    def handle_upload(self, request): #xử lý upload file
        """Xử lý upload file"""
        try:
            # Giải mã session key
            encrypted_session_key = request['encrypted_session_key']
            self.crypto.decrypt_session_key(encrypted_session_key)
            
            # Lấy dữ liệu từ request
            packet = request['packet']
            metadata = request['metadata']
            
            nonce = packet['nonce']
            cipher = packet['cipher']
            tag = packet['tag']
            received_hash = packet['hash']
            signature = packet['sig']
            
            # Kiểm tra hash
            calculated_hash = self.crypto.calculate_hash(nonce, cipher, tag)
            if calculated_hash != received_hash:
                return {'status': 'NACK', 'error': 'integrity', 'message': 'Hash không khớp'}
                
            # Kiểm tra chữ ký metadata
            client_public_key_pem = request.get('client_public_key')
            if not self.crypto.verify_signature(metadata, signature, client_public_key_pem):
                return {'status': 'NACK', 'error': 'auth', 'message': 'Chữ ký không hợp lệ'}
                
            # Kiểm tra tính toàn vẹn AES-GCM
            if not self.crypto.verify_integrity(nonce, cipher, tag):
                return {'status': 'NACK', 'error': 'integrity', 'message': 'Tag AES-GCM không hợp lệ'}
                
            # Giải mã file
            file_data = self.crypto.decrypt_file(nonce, cipher, tag)
            
            # Lưu file
            filename = metadata['filename']
            filepath = os.path.join(self.upload_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
                
            print(f"Upload thành công: {filename}")
            return {'status': 'ACK', 'message': 'Upload thành công'}
            
        except Exception as e:
            print(f"Lỗi upload: {e}")
            return {'status': 'NACK', 'error': 'server', 'message': str(e)}
            
    def handle_download(self, request): #xử lý download file
        """Xử lý download file"""
        try:
            # Kiểm tra chữ ký yêu cầu download
            metadata = request['metadata']
            signature = request['signature']
            client_pub_pem = request.get('client_public_key')
            if not client_pub_pem or not self.crypto.verify_signature(metadata, signature, client_pub_pem):
                return {'status': 'NACK', 'error': 'auth', 'message': 'Xác thực không hợp lệ'}

                
            # Đọc file
            filename = metadata['filename']
            filepath = os.path.join(self.upload_dir, filename)
            
            if not os.path.exists(filepath):
                return {'status': 'NACK', 'error': 'not_found', 'message': 'File không tồn tại'}
                
            with open(filepath, 'rb') as f:
                file_data = f.read()
                
            # Mã hóa file
            encrypted_data = self.crypto.encrypt_file(file_data)
            
            # Tạo hash và chữ ký
            file_hash = self.crypto.calculate_hash(
                encrypted_data['nonce'],
                encrypted_data['cipher'],
                encrypted_data['tag']
            )
            
            file_metadata = {
                'filename': filename,
                'size': len(file_data),
                'timestamp': int(time.time())
            }
            
            metadata_signature = self.crypto.sign_metadata(file_metadata)
            
            packet = {
                'nonce': encrypted_data['nonce'],
                'cipher': encrypted_data['cipher'],
                'tag': encrypted_data['tag'],
                'hash': file_hash,
                'sig': metadata_signature
            }
            
            print(f"Download thành công: {filename}")
            # Mã hóa session key với public key client để họ giải mã
            encrypted_session_key = self.crypto.encrypt_session_key(client_pub_pem)

            return {
                'status': 'ACK',
                'packet': packet,
                'metadata': file_metadata,
                'encrypted_session_key': encrypted_session_key
}

            
        except Exception as e:
            print(f"Lỗi download: {e}")
            return {'status': 'NACK', 'error': 'server', 'message': str(e)}
            
    def stop_server(self): #dừng server
        """Dừng server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("Server đã được dừng")

if __name__ == "__main__":
    server = SpotifyCloudServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nĐang dừng server...")
        server.stop_server()
