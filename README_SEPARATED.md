# Spotify Cloud Simulator - Phiên bản Tách riêng Server/Client

Dự án này đã được tách thành 2 ứng dụng riêng biệt:
- **Server App** (Port 5001): Quản lý server socket và lưu trữ file
- **Client App** (Port 5000): Giao diện upload/download và kết nối đến server

## 🚀 Cách chạy

### 1. Khởi động Server App
```bash
python server_app.py
```
Server sẽ chạy tại: http://localhost:5001

### 2. Khởi động Client App
```bash
python client_app.py
```
Client sẽ chạy tại: http://localhost:5000

## 📁 Cấu trúc dự án

```
MLinh2/
├── server_app.py              # Ứng dụng Server (Port 5001)
├── client_app.py              # Ứng dụng Client (Port 5000)
├── crypto_utils.py            # Tiện ích mã hóa
├── socket_server.py           # Server Socket TCP
├── socket_client.py           # Client Socket TCP
├── templates/
│   ├── server_base.html       # Template base cho Server
│   ├── server_index.html      # Dashboard Server
│   ├── server_files.html      # Quản lý file Server
│   ├── server_logs.html       # Logs Server
│   ├── client_base.html       # Template base cho Client
│   ├── client_index.html      # Dashboard Client
│   ├── client_upload.html     # Upload Client
│   ├── client_download.html   # Download Client
│   └── client_security.html   # Security tests Client
├── static/
│   ├── style.css
│   └── script.js
└── uploads/                   # Thư mục lưu trữ file
```

## 🔧 Tính năng

### Server App (Port 5001)
- **Dashboard**: Trạng thái server, thống kê file
- **Quản lý File**: Xem, tải xuống, xóa file
- **Logs**: Theo dõi hoạt động server
- **API**: Cung cấp API cho client

### Client App (Port 5000)
- **Dashboard**: Kết nối server, danh sách file
- **Upload**: Upload file với bảo mật cao
- **Download**: Download file qua socket hoặc trực tiếp
- **Security Tests**: Test AES-GCM, RSA, SHA-512, Socket

## 🔐 Bảo mật

### Mã hóa AES-GCM
- Khóa 256-bit
- Xác thực tích hợp
- Phát hiện tampering

### Trao đổi khóa RSA
- RSA 1024-bit PKCS#1 v1.5
- Session key được mã hóa
- Chữ ký số SHA-512

### Giao thức Socket TCP
- Handshake bảo mật
- Mã hóa end-to-end
- Kiểm tra toàn vẹn

## 📊 Giao diện

### Server Interface
- **Màu chủ đạo**: Xanh dương (Primary)
- **Focus**: Quản lý server và file
- **Navigation**: Dashboard, Files, Logs

### Client Interface
- **Màu chủ đạo**: Xanh lá (Success)
- **Focus**: Upload/Download và bảo mật
- **Navigation**: Dashboard, Upload, Download, Security

## 🔄 Luồng hoạt động

1. **Khởi động Server**: Chạy `server_app.py` trước
2. **Khởi động Client**: Chạy `client_app.py`
3. **Kết nối**: Client tự động kết nối đến server qua HTTP API
4. **Upload**: File được mã hóa và gửi qua Socket TCP
5. **Download**: File được giải mã và tải về

## 🛠️ API Endpoints

### Server API (Port 5001)
- `GET /api/server-status` - Trạng thái server
- `POST /api/start-server` - Khởi động server
- `POST /api/stop-server` - Dừng server
- `GET /api/files` - Danh sách file
- `POST /api/delete-file` - Xóa file
- `GET /api/download-file/<filename>` - Tải file
- `GET /api/server-logs` - Logs server

### Client API (Port 5000)
- `GET /api/server-status` - Proxy đến server
- `POST /api/start-server` - Proxy đến server
- `POST /api/stop-server` - Proxy đến server
- `GET /api/files` - Proxy đến server
- `POST /api/upload` - Upload file qua socket
- `POST /api/download` - Download file qua socket
- `POST /api/test-*` - Test bảo mật

## 🎯 Lợi ích của việc tách riêng

1. **Tách biệt trách nhiệm**: Server chỉ quản lý file, Client chỉ xử lý UI
2. **Mở rộng dễ dàng**: Có thể chạy nhiều client kết nối đến 1 server
3. **Bảo trì đơn giản**: Sửa lỗi riêng biệt cho từng ứng dụng
4. **Phát triển độc lập**: Team có thể làm việc song song
5. **Triển khai linh hoạt**: Server có thể chạy trên máy khác

## 🚨 Lưu ý

- **Thứ tự khởi động**: Server phải chạy trước Client
- **Port**: Server (5001), Client (5000)
- **Kết nối**: Client kết nối đến server qua HTTP API
- **Socket**: Upload/Download sử dụng Socket TCP port 8888
- **File**: Cả 2 app dùng chung thư mục `uploads/`

## 🔧 Troubleshooting

### Server không khởi động
- Kiểm tra port 5001 có bị chiếm không
- Đảm bảo thư mục `uploads/` có quyền ghi

### Client không kết nối được server
- Kiểm tra server đã chạy chưa
- Kiểm tra URL server trong `client_app.py`
- Kiểm tra firewall

### Upload/Download thất bại
- Kiểm tra server socket (port 8888)
- Kiểm tra file có đúng định dạng không
- Kiểm tra kích thước file (tối đa 50MB) 