import os
import hashlib
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

class CryptoManager:
    def __init__(self):
        self.session_key = None
        self.private_key = None
        self.public_key = None
        self.generate_rsa_keys()
        
    def generate_rsa_keys(self): #tạo cặp khóa RSA 1024-bit 
        """Tạo cặp khóa RSA 1024-bit"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=1024,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
    def generate_session_key(self): #tạo session key cho AES-GCM
        """Tạo session key cho AES-GCM"""
        self.session_key = AESGCM.generate_key(bit_length=256)
        return self.session_key
        
    def encrypt_session_key(self, public_key_pem=None): #mã hóa session key bằng RSA
        """Mã hóa session key bằng RSA"""
        if public_key_pem:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode()
            )
        else:
            public_key = self.public_key
            
        encrypted_key = public_key.encrypt(
            self.session_key,
            padding.PKCS1v15()
        )
        return base64.b64encode(encrypted_key).decode()
        
    def decrypt_session_key(self, encrypted_key_b64): #giải mã session key bằng RSA
        """Giải mã session key bằng RSA"""
        encrypted_key = base64.b64decode(encrypted_key_b64)
        self.session_key = self.private_key.decrypt(
            encrypted_key,
            padding.PKCS1v15()
        )
        return self.session_key
        
    def encrypt_file(self, file_data): #mã hóa file bằng AES-GCM
        """Mã hóa file bằng AES-GCM"""
        if not self.session_key:
            self.generate_session_key()
            
        aesgcm = AESGCM(self.session_key)
        nonce = os.urandom(12)  # 96-bit nonce cho GCM
        
        ciphertext = aesgcm.encrypt(nonce, file_data, None)
        
        # Tách ciphertext và tag (16 byte cuối)
        cipher_data = ciphertext[:-16]
        tag = ciphertext[-16:]
        
        return {
            'nonce': base64.b64encode(nonce).decode(),
            'cipher': base64.b64encode(cipher_data).decode(),
            'tag': base64.b64encode(tag).decode()
        }
        
    def decrypt_file(self, nonce_b64, cipher_b64, tag_b64): #giải mã file bằng AES-GCM
        """Giải mã file bằng AES-GCM"""
        if not self.session_key:
            raise ValueError("Session key not available")
            
        nonce = base64.b64decode(nonce_b64)
        cipher_data = base64.b64decode(cipher_b64)
        tag = base64.b64decode(tag_b64)
        
        # Ghép lại ciphertext với tag
        ciphertext = cipher_data + tag
        
        aesgcm = AESGCM(self.session_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        return plaintext
        
    def calculate_hash(self, nonce_b64, cipher_b64, tag_b64): #tính SHA-512 hash của nonce || ciphertext || tag
        """Tính SHA-512 hash của nonce || ciphertext || tag"""
        nonce = base64.b64decode(nonce_b64)
        cipher = base64.b64decode(cipher_b64)
        tag = base64.b64decode(tag_b64)
        
        data = nonce + cipher + tag
        return hashlib.sha512(data).hexdigest()
        
    def sign_metadata(self, metadata): #ký metadata bằng RSA/SHA-512
        """Ký metadata bằng RSA/SHA-512"""
        metadata_str = json.dumps(metadata, sort_keys=True)
        signature = self.private_key.sign(
            metadata_str.encode(),
            padding.PKCS1v15(),
            hashes.SHA512()
        )
        return base64.b64encode(signature).decode()
        
    def verify_signature(self, metadata, signature_b64, public_key_pem=None): #xác thực chữ ký bằng RSA/SHA-512
        """Xác thực chữ ký"""
        if public_key_pem:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode()
            )
        else:
            public_key = self.public_key
            
        metadata_str = json.dumps(metadata, sort_keys=True)
        signature = base64.b64decode(signature_b64)
        
        try:
            public_key.verify(
                signature,
                metadata_str.encode(),
                padding.PKCS1v15(),
                hashes.SHA512()
            )
            return True
        except:
            return False
            
    def get_public_key_pem(self):
        """Lấy public key dưới dạng PEM"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
    def verify_integrity(self, nonce_b64, cipher_b64, tag_b64): #kiểm tra tính toàn vẹn bằng AES-GCM tag
        """Kiểm tra tính toàn vẹn bằng AES-GCM tag"""
        try:
            # Thử giải mã để kiểm tra tag
            self.decrypt_file(nonce_b64, cipher_b64, tag_b64)
            return True
        except:
            return False

    def encrypt_aesgcm(self, data: bytes) -> bytes: #mã hóa file bằng AES-GCM
        """Mã hóa dữ liệu bằng AES-GCM, trả về nonce + ciphertext + tag (gộp)"""
        if not self.session_key:
            self.generate_session_key()
        aesgcm = AESGCM(self.session_key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        # Trả về nonce + ciphertext (bao gồm tag ở cuối)
        return nonce + ciphertext

    def decrypt_aesgcm(self, enc_data: bytes) -> bytes: #giải mã file bằng AES-GCM
        """Giải mã dữ liệu AES-GCM, input là nonce + ciphertext + tag"""
        if not self.session_key:
            raise ValueError("Session key not available")
        nonce = enc_data[:12]
        ciphertext = enc_data[12:]
        aesgcm = AESGCM(self.session_key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def encrypt_rsa(self, data: bytes) -> bytes:
        """Mã hóa dữ liệu bằng public key RSA"""
        return self.public_key.encrypt(
            data,
            padding.PKCS1v15()
        )

    def decrypt_rsa(self, enc_data: bytes) -> bytes:
        """Giải mã dữ liệu bằng private key RSA"""
        return self.private_key.decrypt(
            enc_data,
            padding.PKCS1v15()
        )

    def sign_rsa(self, data: bytes) -> bytes:
        """Ký dữ liệu bằng private key RSA/SHA-512"""
        return self.private_key.sign(
            data,
            padding.PKCS1v15(),
            hashes.SHA512()
        )

    def verify_rsa(self, data: bytes, signature: bytes) -> bool:
        """Xác thực chữ ký số bằng public key RSA/SHA-512"""
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA512()
            )
            return True
        except Exception:
            return False

    def hash_sha512(self, data: bytes) -> bytes: #tính hash SHA-512 cho dữ liệu
        """Tính hash SHA-512 cho dữ liệu"""
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(data)
        return digest.finalize()

    def verify_sha512(self, data: bytes, hash_value: bytes) -> bool: #kiểm tra hash SHA-512
        """Kiểm tra hash SHA-512"""
        digest = hashes.Hash(hashes.SHA512(), backend=default_backend())
        digest.update(data)
        return digest.finalize() == hash_value
