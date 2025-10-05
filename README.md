# Tkinter Chat Application

A real-time chat application built with Python Tkinter and Firebase authentication.

## Features

- Real-time text messaging
- Firebase authentication
- Socket-based communication
- Cross-platform support

## Quick Start (Windows/PowerShell)

### Prerequisites

- Python 3.7 or higher
- Git
- Firebase project with Email/Password auth enabled

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

### 4) Configure .env (preferred)

The app now auto-loads `.env` via python-dotenv in both `lib/firebase.py` and `Server/server.py`.

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
python server.py
```

Client (Terminal 2):

```powershell
cd Client
python run.py
```

You should see on server: `Server is listening on port 8080...` and `[Auth] Firebase initialized from environment variable` (or file/default).

### 6) Verify

```powershell
python -c "from lib.firebase import API_KEY; print('Firebase API Key loaded:', 'Yes' if API_KEY else 'No')"
```

Client flow: open login → register/login → chat.

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
├── Server/          # Server application
│   └── server.py    # Socket server with Firebase auth
├── lib/             # Shared libraries
│   ├── firebase.py  # Firebase configuration (loads .env)
│   └── firebase-service.json  # optional local creds (git-ignored)
├── env.example      # sample .env to copy
└── README.md
```

## Troubleshooting

- API key not loaded: check `FIREBASE_WEB_API_KEY` in `.env`
- Firebase init failed: ensure `FIREBASE_SERVICE_ACCOUNT_KEY` JSON is valid or `GOOGLE_APPLICATION_CREDENTIALS` points to an existing file
- Connection refused: server must be running on port 8080; check firewall

## License

MIT
