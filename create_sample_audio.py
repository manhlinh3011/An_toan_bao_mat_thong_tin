#!/usr/bin/env python3
"""
Script để tạo file âm thanh mẫu cho testing
"""

import os
import struct
import math

def create_sample_mp3():
    """Tạo file MP3 mẫu đơn giản"""
    # Tạo dữ liệu âm thanh đơn giản (sine wave)
    sample_rate = 44100
    duration = 3  # 3 giây
    frequency = 440  # A4 note
    
    # Tạo dữ liệu PCM
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        sample = int(32767 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    # Tạo header WAV đơn giản
    data = b''.join(samples)
    data_size = len(data)
    
    # WAV header
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,  # PCM
        1,   # PCM format
        1,   # mono
        sample_rate,
        sample_rate * 2,  # byte rate
        2,   # block align
        16,  # bits per sample
        b'data',
        data_size
    )
    
    # Lưu file
    with open('sample_audio.wav', 'wb') as f:
        f.write(header + data)
    
    print("✅ Đã tạo file sample_audio.wav")

def create_sample_text_as_audio():
    """Tạo file giả lập MP3 từ text (cho demo)"""
    content = """
    🎵 SPOTIFY CLOUD SIMULATOR - SAMPLE AUDIO FILE 🎵
    
    Đây là file âm thanh mẫu để test hệ thống upload/download
    với các tính năng bảo mật:
    
    ✅ Mã hóa AES-GCM
    ✅ Trao đổi khóa RSA 1024-bit  
    ✅ Chữ ký số RSA/SHA-512
    ✅ Kiểm tra toàn vẹn SHA-512
    ✅ Phát hiện sửa đổi dữ liệu
    
    File này sẽ được mã hóa và truyền qua socket TCP
    để mô phỏng quá trình upload lên cloud Spotify.
    
    Timestamp: """ + str(int(__import__('time').time())) + """
    Size: Khoảng 1KB
    Format: Giả lập MP3
    
    🔒 SECURITY FEATURES:
    - AES-256-GCM encryption
    - RSA-1024 key exchange  
    - SHA-512 integrity check
    - Digital signature verification
    - Tampering detection
    
    """ * 5  # Lặp lại để tăng kích thước file
    
    with open('sample_podcast.mp3', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Đã tạo file sample_podcast.mp3")

if __name__ == "__main__":
    print("🎵 Tạo file âm thanh mẫu...")
    
    try:
        create_sample_mp3()
    except Exception as e:
        print(f"⚠️  Không thể tạo WAV: {e}")
        print("📝 Tạo file text thay thế...")
        create_sample_text_as_audio()
    
    print("\n🎯 File mẫu đã sẵn sàng để test!")
    print("📁 Sử dụng file này để test upload trong ứng dụng.")
