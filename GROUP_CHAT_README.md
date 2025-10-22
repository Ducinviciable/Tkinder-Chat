# Chức Năng Chat Nhóm

## Tổng Quan
Đã thêm chức năng chat nhóm vào ứng dụng chat hiện có, cho phép người dùng tạo nhóm, mời bạn bè và chat trong nhóm.

## Tính Năng Mới

### 1. Tab "Tạo Nhóm"
- **Vị trí**: Tab mới trong giao diện chính
- **Chức năng**:
  - Nhập tên nhóm
  - Chọn bạn bè từ danh sách (checkbox)
  - Tạo nhóm mới
  - Làm mới danh sách bạn bè

### 2. Tab "Nhóm Chat"
- **Vị trí**: Tab mới trong giao diện chính
- **Chức năng**:
  - Xem danh sách các nhóm đã tham gia
  - Mở chat nhóm
  - Tạo nhóm mới (chuyển sang tab tạo nhóm)

### 3. Chat Nhóm
- **Giao diện**: Tab động cho mỗi nhóm
- **Chức năng**:
  - Hiển thị tên nhóm và thành viên
  - Gửi tin nhắn nhóm
  - Tải lịch sử tin nhắn
  - Hiển thị tin nhắn real-time

## Cách Sử Dụng

### Bước 1: Khởi Động
```bash
# Terminal 1 - Chạy server
cd Chat/Server
python main.py

# Terminal 2 - Chạy client
cd Chat/Client
python run.py
```

### Bước 2: Thiết Lập
1. Đăng nhập với ít nhất 2 tài khoản khác nhau
2. Kết bạn giữa các tài khoản (tab "Tìm bạn")
3. Chấp nhận lời mời kết bạn

### Bước 3: Tạo Nhóm
1. Chuyển sang tab "Tạo nhóm"
2. Nhập tên nhóm
3. Chọn bạn bè muốn thêm vào nhóm
4. Nhấn "Tạo nhóm"

### Bước 4: Chat Nhóm
1. Chuyển sang tab "Nhóm chat"
2. Chọn nhóm muốn chat
3. Nhấn "Mở nhóm" hoặc double-click
4. Gửi tin nhắn trong nhóm

## Cấu Trúc Database

### Groups Collection
```
/groups/{groupId}/
├── id: string
├── name: string
├── createdBy: string (uid)
├── createdAt: timestamp
└── members: {uid: true}
```

### Group Messages
```
/groups/{groupId}/messages/{messageId}/
├── senderUid: string
├── text: string
└── ts: timestamp
```

### User Groups
```
/users/{uid}/groups/{groupId}: true
```

## API Commands

### Client → Server
- `CREATE_GROUP`: Tạo nhóm mới
- `LIST_GROUPS`: Lấy danh sách nhóm
- `SEND_GROUP_MESSAGE`: Gửi tin nhắn nhóm
- `LOAD_GROUP_HISTORY`: Tải lịch sử nhóm

### Server → Client
- `GROUPS`: Danh sách nhóm
- `GROUP_CREATED`: Xác nhận tạo nhóm
- `GROUP_MESSAGE`: Tin nhắn nhóm mới
- `GROUP_HISTORY`: Lịch sử tin nhắn

## Files Đã Thêm/Sửa

### Files Mới
- `Client/ui/create_group.py`: UI tạo nhóm
- `Client/ui/group_chat.py`: UI chat nhóm
- `test_group_chat.py`: Demo script

### Files Đã Sửa
- `Client/ui/chat_window.py`: Thêm tab nhóm
- `Client/ui/cmd_handlers.py`: Xử lý lệnh nhóm
- `Server/commands.py`: Logic server cho nhóm

## Lưu Ý Kỹ Thuật

1. **Authentication**: Chỉ thành viên nhóm mới có thể gửi tin nhắn
2. **Real-time**: Tin nhắn được gửi đến tất cả thành viên online
3. **History**: Lịch sử được lưu trong Firebase
4. **UI**: Sử dụng tkinter với tab động
5. **Error Handling**: Xử lý lỗi đầy đủ cho tất cả operations

## Testing

1. Tạo 2+ tài khoản
2. Kết bạn giữa các tài khoản
3. Tạo nhóm với nhiều thành viên
4. Test gửi tin nhắn từ các tài khoản khác nhau
5. Test tải lịch sử tin nhắn

## Troubleshooting

- **Không thấy tab**: Restart client
- **Không tạo được nhóm**: Kiểm tra kết nối server
- **Tin nhắn không hiện**: Kiểm tra Firebase connection
- **Lỗi database**: Kiểm tra Firebase credentials
