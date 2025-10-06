# Tkinter Chat Application

A real-time chat app using Python Tkinter, Firebase Auth, and a socket server.

## Features

- Real-time messaging
- Firebase Email/Password authentication
- Friend features (UI ready): Find friend by email, send/accept/reject requests
- Modular server with Firebase Admin lookup (FIND_USER)

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

# ONE of the following options
# A) Paste JSON content (single-line or quoted, ensure valid JSON)
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"..."}'

# B) Or point to your JSON file on disk
GOOGLE_APPLICATION_CREDENTIALS=D:\\Learning\\Python\\Chat\\lib\\firebase-service.json
```

Tip: If you use option B, place your downloaded JSON at `lib/firebase-service.json` (git-ignored) and set the absolute path in `.env`.

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

Client flow: login → chat → Find Friend tab.

## Security Notes

- Never commit Firebase service account keys
- Use `.env` or environment variables
- `lib/firebase-service.json` is ignored by Git

## Project Structure

```
Chat/
├── Client/           # Client application
│   ├── ui/          # UI components
│   ├── auth.py      # Authentication logic
│   ├── network.py   # Network communication
│   └── run.py       # Main client entry point
├── Server/          # Server application (modular)
│   ├── main.py                 # Socket config, accept loop
│   ├── handler.py              # Per-connection I/O, AUTH, broadcast, CMD routing
│   ├── commands.py             # Command handlers (FIND_USER, ...)
│   ├── firebase_admin_utils.py # Firebase Admin init, verify, get_user_by_email
│   └── state.py                # Shared in-memory state (clients, locks, socket→user)
├── lib/
│   ├── firebase.py             # Firebase configuration (loads .env)
│   └── firebase-service.json   # optional local creds (git-ignored)
├── env.example                 # sample .env to copy
└── README.md
```

## Friend Features (UI and Server command)

- UI (Client `ui/chat_window.py`):
  - Tab “Tìm bạn”: nhập email, nút Tìm → gửi `CMD FIND_USER` đến server.
  - Khi tìm thấy: hiện thẻ kết quả (tên, email, nút gửi yêu cầu). Nếu trùng email của chính mình, nút gửi bị vô hiệu.
  - Tab “Profile”: hiển thị danh sách yêu cầu (demo tự nạp lần đầu mở tab).

- Server `CMD FIND_USER` (Firebase Admin):
  - Input: `{"type":"FIND_USER","email":"someone@gmail.com"}`
  - Output: `CMD {"type":"FIND_USER_RESULT","found":true|false,"email":"...","displayName":"...","uid":"..."}`

Note: Gửi/duyệt/từ chối yêu cầu hiện là demo UI; cần bổ sung endpoint và DB (Firestore) để lưu thật.

## Troubleshooting

- API key not loaded: check `FIREBASE_WEB_API_KEY` in `.env`
- Firebase init failed: ensure `FIREBASE_SERVICE_ACCOUNT_KEY` JSON is valid or `GOOGLE_APPLICATION_CREDENTIALS` points to an existing file
- Connection refused: server must be running on port 8080; check firewall

## License

MIT
