#up: mã hóa file bằng AES-GCM, gửi nonce, ciphertext, tag lên server.
#down: nhận nonce, ciphertext, tag từ server, giải mã bằng AES-GCM.
import socket
import json
import os
import time
from crypto_utils import CryptoManager

class SpotifyClient: 
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.crypto = CryptoManager()
        self.server_public_key = None
        self.socket = None
        
    def connect(self): #kết nối đến server
        """Kết nối đến server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            
            # Handshake rõ ràng
            self.socket.send("Hello!".encode())
            response = self.socket.recv(1024).decode()
            print(f"[CLIENT] Gửi: Hello! | Nhận: {response}")
            if response != "Ready!":
                raise Exception(f"Handshake failed: {response}")
            
            # Nhận public key từ server
            self.server_public_key = self.socket.recv(2048).decode()
            
            print("Kết nối thành công đến Spotify Cloud")
            return True
            
        except Exception as e:
            print(f"Lỗi kết nối: {e}")
            return False
            
    def upload_file(self, filepath, simulate_tampering=False): #upload file lên server
        """Upload file lên server"""
        try:
            if not os.path.exists(filepath):
                return {'status': 'error', 'message': 'File không tồn tại'}
                
            # Đọc file
            with open(filepath, 'rb') as f:
                file_data = f.read()
                
            # Tạo session key và mã hóa
            self.crypto.generate_session_key()
            encrypted_data = self.crypto.encrypt_file(file_data)
            
            # Tạo metadata
            metadata = {
                'filename': os.path.basename(filepath).replace('temp_', ''),
                'size': len(file_data),
                'timestamp': int(time.time())
            }
            
            # Ký metadata
            metadata_signature = self.crypto.sign_metadata(metadata)
            
            # Tính hash
            file_hash = self.crypto.calculate_hash(
                encrypted_data['nonce'],
                encrypted_data['cipher'],
                encrypted_data['tag']
            )
            
            # Mô phỏng sửa đổi dữ liệu nếu được yêu cầu
            if simulate_tampering:
                print("Mô phỏng sửa đổi dữ liệu...")
                # Thay đổi một byte trong ciphertext
                cipher_bytes = encrypted_data['cipher'].encode()
                if len(cipher_bytes) > 10:
                    tampered = cipher_bytes[:10] + b'X' + cipher_bytes[11:]
                    encrypted_data['cipher'] = tampered.decode('latin-1')
            
            # Tạo packet
            packet = {
                'nonce': encrypted_data['nonce'],
                'cipher': encrypted_data['cipher'],
                'tag': encrypted_data['tag'],
                'hash': file_hash,
                'sig': metadata_signature
            }
            
            # Mã hóa session key bằng public key của server
            encrypted_session_key = self.crypto.encrypt_session_key(self.server_public_key)
            
            # Gửi request
            request = {
                'type': 'upload',
                'packet': packet,
                'metadata': metadata,
                'encrypted_session_key': encrypted_session_key,
                'client_public_key': self.crypto.get_public_key_pem()
            }
            
            # Gửi dữ liệu với kích thước
            data = json.dumps(request).encode()
            size = str(len(data)).zfill(8)
            self.socket.send(size.encode())
            self.socket.send(data)

            # Nhận 4 bytes đầu là kích thước
            size_data = self.socket.recv(8)
            if not size_data:
                return {'status': 'error', 'message': 'No response size received'}
            response_size = int(size_data.decode())

            print(f"[SERVER] size_data: '{size_data}', data_size: {response_size}")

            # Nhận đúng số byte response
            response_bytes = b''
            while len(response_bytes) < response_size:
                chunk = self.socket.recv(response_size - len(response_bytes))
                if not chunk:
                    break
                response_bytes += chunk

            response_data = response_bytes.decode()
            print(f"[CLIENT] Received response_data: {response_data}")  # Thêm dòng này

            print(f"[SERVER] Raw data received (len={len(data)}): {data[:200]}")
            print(f"[SERVER] Decoded data: {data.decode(errors='replace')[:200]}")

            response = json.loads(response_data)
            
            return response
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def download_file(self, filename, save_path): #download file từ server
        """Download file từ server"""
        try:
            # Tạo metadata cho yêu cầu download
            metadata = {
                'filename': filename,
                'timestamp': int(time.time())
            }
            
            # Ký yêu cầu
            signature = self.crypto.sign_metadata(metadata)
            
            # Gửi request
            request = {
                'type': 'download',
                'metadata': metadata,
                'signature': signature,
                'client_public_key': self.crypto.get_public_key_pem()
            }
            
            # Gửi dữ liệu với kích thước
            data = json.dumps(request).encode()
            size = str(len(data)).zfill(8)
            self.socket.send(size.encode())
            self.socket.send(data)

            # Nhận response
           # Nhận 4 bytes đầu là kích thước
            size_data = self.socket.recv(8)
            if not size_data:
                return {'status': 'error', 'message': 'No response size received'}
            response_size = int(size_data.decode())

            print(f"[SERVER] size_data: '{size_data}', data_size: {response_size}")

            # Nhận đúng số byte response
            response_bytes = b''
            while len(response_bytes) < response_size:
                chunk = self.socket.recv(response_size - len(response_bytes))
                if not chunk:
                    break
                response_bytes += chunk

            response_data = response_bytes.decode()
            response = json.loads(response_data)
            
            if response['status'] != 'ACK':
                return response
                
            # Giải mã session key
            encrypted_session_key = response['encrypted_session_key']
            self.crypto.decrypt_session_key(encrypted_session_key)
            
            # Lấy packet
            packet = response['packet']
            metadata = response['metadata']
            
            # Kiểm tra hash
            calculated_hash = self.crypto.calculate_hash(
                packet['nonce'],
                packet['cipher'],
                packet['tag']
            )
            
            if calculated_hash != packet['hash']:
                return {'status': 'NACK', 'error': 'integrity', 'message': 'Hash không khớp'}
                
            # Kiểm tra chữ ký
            if not self.crypto.verify_signature(metadata, packet['sig'], self.server_public_key):
                return {'status': 'NACK', 'error': 'auth', 'message': 'Chữ ký không hợp lệ'}
                
            # Kiểm tra tính toàn vẹn AES-GCM
            if not self.crypto.verify_integrity(packet['nonce'], packet['cipher'], packet['tag']):
                return {'status': 'NACK', 'error': 'integrity', 'message': 'Tag AES-GCM không hợp lệ'}
                
            # Giải mã file
            file_data = self.crypto.decrypt_file(
                packet['nonce'],
                packet['cipher'],
                packet['tag']
            )
            
            # Lưu file
            with open(save_path, 'wb') as f:
                f.write(file_data)
                
            return {'status': 'ACK', 'message': 'Download thành công'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
            
    def disconnect(self): #ngắt kết nối
        """Ngắt kết nối"""
        if self.socket:
            self.socket.close()
            print("Đã ngắt kết nối")

if __name__ == "__main__":
    client = SpotifyClient()
    
    if client.connect():
        # Test upload
        print("\n=== Test Upload ===")
        result = client.upload_file("test_audio.mp3")
        print(f"Upload result: {result}")
        
        # Test upload với tampering
        print("\n=== Test Upload với Tampering ===")
        result = client.upload_file("test_audio.mp3", simulate_tampering=True)
        print(f"Upload result: {result}")
        
        # Test download
        print("\n=== Test Download ===")
        result = client.download_file("test_audio.mp3", "downloaded_audio.mp3")
        print(f"Download result: {result}")
        
        client.disconnect()
