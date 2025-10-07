# Tkinter Chat Application

A real-time chat app using Python Tkinter, Firebase Auth, and a modular socket server. Supports friend discovery and requests backed by Firebase Realtime Database.

## Features

- Real-time messaging
- Firebase Email/Password authentication
- Friend features: find by email, send/accept/reject friend requests
- Modular server with Firebase Admin (email lookup) and RTDB storage

## Quick Start (Windows/PowerShell)

### Prerequisites

- Python 3.8+
- Firebase project with Email/Password enabled

### 1) Clone & create virtual env

```powershell
git clone https://github.com/Ducinviciable/Tkinder-Chat.git
cd Tkinder-Chat
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install firebase-admin python-dotenv
```

### 3) Firebase setup

1. Create a project at `https://console.firebase.google.com`
2. Enable Authentication → Sign-in method → Email/Password
3. Copy Web API Key: Project settings → General → Web API Key
4. Generate Service Account key: Project settings → Service accounts → Generate new private key (download JSON)

### 4) Configure .env

Both client and server auto-load `.env`.

```powershell
copy env.example .env
```

Open `.env` and fill:

```
FIREBASE_WEB_API_KEY=AIzaSy...yourKey
FIREBASE_DATABASE_URL=


### 5) Run

Server (Terminal 1):

```powershell
cd Server
python main.py
```

Client (Terminal 2):

```powershell
cd Client
python run.py
```

Server should print: `Server is listening on port 8080...` and Firebase init logs.

### 6) Verify

```powershell
python -c "from lib.firebase import API_KEY; print('Firebase API Key loaded:', 'Yes' if API_KEY else 'No')"
```

Client flow: login → Chat tab → Find Friend / Profile / Bạn bè tabs.

## Security Notes

- Never commit Firebase service account keys
- Use `.env` or environment variables
- `lib/firebase-service.json` is ignored by Git

## Project Structure

```
Chat/
├── Client/                      # Client application
│   ├── ui/
│   │   ├── chat_window.py       # Orchestrator: tạo tabs, gửi CMD, định tuyến CMD → cmd_handlers
│   │   ├── find_friend.py       # FindFriendFrame (UI tab “Tìm bạn”)
│   │   ├── friends_tab.py       # FriendsTabFrame (UI tab “Bạn bè”)
│   │   ├── private_chat.py      # PrivateChatTab (UI chat 1-1, transcript, input)
│   │   ├── user_profile.py      # UserProfileFrame (UI tab “Profile”)
│   │   └── cmd_handlers.py      # Xử lý phản hồi CMD từ server, cập nhật state + gọi UI
│   ├── auth.py                  # Đăng nhập Firebase, lấy idToken
│   ├── network.py               # Kết nối socket, gửi/nhận dòng, callback
│   └── run.py                   # Main client entry point
├── Server/                      # Server application (modular)
│   ├── main.py                  # Socket config, accept loop
│   ├── handler.py               # Per-connection I/O, AUTH, broadcast, CMD routing
│   ├── commands.py              # Command handlers (FIND_USER, LIST_FRIENDS, FRIEND_REQUESTS,
│   │                             # SEND_FRIEND_REQUEST, ACCEPT_REQUEST, REJECT_REQUEST, SEND_DM, LOAD_THREAD)
│   ├── firebase_admin_utils.py  # Firebase Admin init/verify, helpers RTDB (users/friends/chats)
│   └── state.py                 # Shared in-memory state (clients, locks, socket→user/uid, uid→socket)
├── lib/
│   ├── firebase.py              # Firebase configuration (loads .env)
│   └── firebase-service.json    # optional local creds (git-ignored)
├── env.example                  # sample .env to copy
└── README.md
```

## Friend Features (UI and Server command)

- UI:
  - Tab “Tìm bạn”: nhập email → `FIND_USER`. Nếu đã là bạn/đúng chính mình → disable nút gửi.
  - Tab “Profile”: danh sách yêu cầu đến (nút “Làm mới”), nút “Chấp nhận”/“Từ chối”.
  - Tab “Bạn bè”: hiển thị danh sách bạn (nút “Làm mới”), mở chat 1-1.

- Server commands:
  - `FIND_USER { email }` → `FIND_USER_RESULT { found, uid, email, displayName }`
  - `LIST_FRIENDS` → `FRIENDS { friends: [{ uid, email, displayName }] }`
  - `FRIEND_REQUESTS` → `FRIEND_REQUESTS { requests: [{ fromUid, fromEmail, createdAt }] }`
  - `SEND_FRIEND_REQUEST { toUid | toEmail }` → `FRIEND_REQUEST_SENT { ok | error }`
  - `ACCEPT_REQUEST { fromUid | fromEmail }` → `FRIEND_REQUEST_ACCEPTED { ok }`
  - `REJECT_REQUEST { fromUid | fromEmail }` → `FRIEND_REQUEST_REJECTED { ok }`

Notes:
- Server xác thực bằng Firebase Admin qua `AUTH <idToken>` khi kết nối socket (bắt buộc).
- Sau AUTH, server đảm bảo tồn tại hồ sơ `users/{uid}` (email/displayName).
- RTDB paths đang dùng:
  - `users/{uid}`: { email, displayName }
  - `users/{uid}/friends/{friendUid}`: true
  - `users/{uid}/incoming_requests/{fromUid}`: { createdAt }

## Explain (Giải thích hoạt động)

### 1) Xác thực và bắt tay (AUTH)
- Client đăng nhập Firebase (Email/Password) để lấy `idToken`.
- Khi mở kết nối socket tới server, client gửi dòng đầu: `AUTH <idToken>`.
- Server dùng Firebase Admin để `verify_id_token` → lấy `uid`, `email`, `name` và:
  - Lưu `conn._chat_uid`, `socket_to_uid[conn]`, `uid_to_socket[uid]` để định tuyến về sau.
  - Đảm bảo tồn tại `users/{uid}` (tạo tối thiểu `email`, `displayName` nếu thiếu).

Kết quả: mọi lệnh tiếp theo trên kết nối này đều gắn với đúng người dùng.

### 2) Tìm bạn (Find Friend)
- UI “Tìm bạn” gửi `FIND_USER { email }`.
- Server dùng Admin SDK `get_user_by_email` → trả `FIND_USER_RESULT { found, uid, email, displayName }`.
- Client hiển thị thẻ kết quả:
  - Nếu trùng với chính mình hoặc email đã có trong danh sách bạn → disable nút “Gửi yêu cầu kết bạn”.
  - Ngược lại cho phép gửi yêu cầu.

### 3) Gửi/nhận yêu cầu kết bạn (Friend Requests)
- Gửi yêu cầu: `SEND_FRIEND_REQUEST { toUid | toEmail }`.
- Server kiểm tra chặn:
  - `users/{uid}/friends/{toUid}` hoặc `users/{toUid}/friends/{uid}` đã tồn tại → `already_friends`.
  - Đã có pending `users/{toUid}/incoming_requests/{uid}` → `already_requested`.
- Nếu hợp lệ, tạo `users/{toUid}/incoming_requests/{uid} = { createdAt: serverTimestamp }`.
- Xem yêu cầu đến: `FRIEND_REQUESTS` → server đọc `users/{uid}/incoming_requests` và trả danh sách `{fromUid, fromEmail, createdAt}`.
- Chấp nhận: `ACCEPT_REQUEST { fromUid | fromEmail }` → tạo `friends` 2 chiều và xóa pending.
- Từ chối: `REJECT_REQUEST { fromUid | fromEmail }` → xóa pending.

Lưu ý UI:
- Tab “Profile”: nút “Làm mới” sẽ gọi `FRIEND_REQUESTS`. Chấp nhận/Từ chối sẽ tự refresh và update “Bạn bè”.

### 4) Danh sách bạn bè (List Friends)
- Mỗi lần mở tab “Bạn bè” hoặc bấm “Làm mới”, client gửi `LIST_FRIENDS`.
- Server đọc `users/{uid}/friends` (danh sách `{ friendUid: true }`), tra hồ sơ `users/{friendUid}` (bổ sung email nếu thiếu qua Admin) → trả `FRIENDS [{ uid, email, displayName }]`.
- Client hiển thị danh sách; chọn một bạn → bấm “Nhắn tin” để mở chat 1-1.

### 5) Chat 1-1 và lịch sử
- Gửi tin: `SEND_DM { toUid, text, clientMsgId }`.
  - Server viết vào `chats/{threadId}/messages` (với `threadId = min(uidA,uidB)__max(uidA,uidB)`), trả `DM_DELIVERED` cho người gửi.
  - Nếu người nhận online (`uid_to_socket`) → đẩy `DM { fromUid, text, threadId }` realtime.
- Nạp lịch sử: `LOAD_THREAD { peerUid, limit }`.
  - Server đọc `chats/{threadId}/messages`, sort theo `ts` tăng, cắt theo `limit` → trả `DM_HISTORY { messages }`.
- UI 1-1 (tab riêng per bạn) sẽ:
  - Lần đầu mở: gọi `LOAD_THREAD` để hiển thị tin cũ.
  - Khi nhận `DM`: tự mở/focus tab đúng bạn, bổ sung “Friend: …”.

### 6) Kiến trúc code phía Client
- `ChatWindow`: điều phối; gửi CMD; nhận CMD → chuyển tiếp cho `cmd_handlers`.
- Frames UI:
  - `FindFriendFrame`: nhập email, thẻ kết quả, gửi yêu cầu.
  - `UserProfileFrame`: yêu cầu đến, chấp nhận/từ chối, nút “Làm mới”.
  - `FriendsTabFrame`: danh sách bạn, “Nhắn tin”, “Làm mới”.
  - `PrivateChatTab`: giao diện chat 1-1 (transcript, input), nạp lịch sử và gửi tin.
- `cmd_handlers.py`: tập trung xử lý phản hồi từ server, cập nhật state và gọi UI tương ứng.

### 7) Ghi chú lỗi thường gặp (và đã khắc phục)
- `FRIENDS { error: "unauthorized" }`: do chưa lấy được uid trên server tại thời điểm lệnh đến.
  - Khắc phục: fallback uid từ `socket_to_uid[conn]` cho mọi lệnh cần uid.
- Gửi yêu cầu khi đã là bạn hoặc đã pending:
  - Khắc phục: server chặn `already_friends` / `already_requested`; client disable nút khi email đã nằm trong friends.
- RTDB timestamp: dùng `{".sv": "timestamp"}` (không có `db.SERVER_TIMESTAMP` trong Admin Python).


## Protocol (TCP/IP & Message Framing)

### Socket config
- Server cấu hình TCP/IPv4 và lắng nghe port 8080 trong `Server/main.py`:
  - Tạo socket `AF_INET, SOCK_STREAM`, `SO_REUSEADDR=1`.
  - `bind(('0.0.0.0', 8080))`, `listen(5)`, vòng `accept()` tạo thread `handle_client` (file `Server/handler.py`).

- Client tạo kết nối trong `Client/network.py`:
  - `socket(AF_INET, SOCK_STREAM)` → `connect((host, port))`.
  - Sau khi kết nối, client gửi chuỗi handshake `AUTH <idToken>\n`.

### Handshake & auth
- Dòng đầu tiên từ client phải là `AUTH <idToken>\n` (chứa Firebase ID token).
- Server đọc dòng đầu, dùng Firebase Admin verify token trong `handler.py`:
  - Thành công: gửi `AUTH_OK\n`, lưu `conn._chat_uid`, `socket_to_uid[conn]`, `uid_to_socket[uid]`, `socket_to_user[conn]`.
  - Thất bại: gửi `AUTH_ERR <reason>\n` rồi đóng kết nối.

### Framing thông điệp
- Giao thức là dạng text-line, mỗi thông điệp kết thúc bằng `\n`.
- Hai kiểu thông điệp:
  1) Chat broadcast (text thường): bất kỳ dòng nào không bắt đầu bằng `CMD ` sẽ được broadcast tới các client khác (demo kênh công cộng).
  2) Command có tiền tố `CMD `: phần còn lại là JSON một dòng, ví dụ: `CMD {"type":"LIST_FRIENDS"}\n`.
- Server parse theo dòng trong `handler.py`: nếu bắt gặp `CMD ` thì chuyển JSON sang dict và gọi `commands.handle_command_line(...)` (file `Server/commands.py`).

### Command/Response
- Request từ client đều có dạng `CMD {...}\n` và response cũng trở về client với tiền tố `CMD `, ví dụ:
  - Client: `CMD {"type":"FIND_USER","email":"a@gmail.com"}`
  - Server: `CMD {"type":"FIND_USER_RESULT","found":true,"uid":"...","email":"...","displayName":"..."}`

- Một số lệnh chính:
  - `FIND_USER`, `LIST_FRIENDS`, `FRIEND_REQUESTS`, `SEND_FRIEND_REQUEST`, `ACCEPT_REQUEST`, `REJECT_REQUEST`, `SEND_DM`, `LOAD_THREAD`.
  - Xử lý chi tiết trong `Server/commands.py` (đọc/ghi RTDB, push response bằng `conn.sendall(("CMD "+json+"\n").encode(...))`).

### Nhận dữ liệu phía client
- `Client/network.py` chạy `_receive_loop`, tách theo `\n` và callback vào `ChatWindow._on_message_received`.
- `ChatWindow` định tuyến theo `type` trong JSON rồi ủy quyền cho `ui/cmd_handlers.py` để cập nhật state/UI.

## License

MIT
