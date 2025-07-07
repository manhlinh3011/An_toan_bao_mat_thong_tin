#!/usr/bin/env python3
"""
Script để chạy cả Server và Client cùng lúc
"""

import subprocess
import time
import sys
import os
from threading import Thread

def run_server():
    """Chạy server app"""
    print("🚀 Khởi động Server App...")
    try:
        subprocess.run([sys.executable, "server_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️ Server đã dừng")
    except Exception as e:
        print(f"❌ Lỗi khi chạy server: {e}")

def run_client():
    """Chạy client app"""
    print("🚀 Khởi động Client App...")
    try:
        subprocess.run([sys.executable, "client_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n⏹️ Client đã dừng")
    except Exception as e:
        print(f"❌ Lỗi khi chạy client: {e}")

def main():
    print("🎵 Spotify Cloud Simulator - Phiên bản Tách riêng")
    print("=" * 50)
    print("📋 Hướng dẫn:")
    print("   - Server sẽ chạy tại: http://localhost:5001")
    print("   - Client sẽ chạy tại: http://localhost:5000")
    print("   - Nhấn Ctrl+C để dừng cả 2 ứng dụng")
    print("=" * 50)
    
    # Kiểm tra các file cần thiết
    required_files = [
        "server_app.py",
        "client_app.py",
        "crypto_utils.py",
        "socket_server.py",
        "socket_client.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Thiếu các file sau:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nVui lòng đảm bảo tất cả file đã được tạo.")
        return
    
    # Tạo thư mục uploads nếu chưa có
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("📁 Đã tạo thư mục uploads/")
    
    print("\n⏳ Khởi động trong 3 giây...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    print("\n🎯 Bắt đầu chạy cả 2 ứng dụng...")
    
    # Chạy server và client trong thread riêng biệt
    server_thread = Thread(target=run_server, daemon=True)
    client_thread = Thread(target=run_client, daemon=True)
    
    try:
        # Khởi động server trước
        server_thread.start()
        time.sleep(2)  # Đợi server khởi động
        
        # Khởi động client
        client_thread.start()
        
        print("\n✅ Cả 2 ứng dụng đã được khởi động!")
        print("🌐 Server: http://localhost:5001")
        print("🌐 Client: http://localhost:5000")
        print("\n⏹️ Nhấn Ctrl+C để dừng...")
        
        # Đợi cho đến khi có interrupt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Đang dừng các ứng dụng...")
        print("👋 Tạm biệt!")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

if __name__ == "__main__":
    main() 