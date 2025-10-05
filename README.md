# Tkinter Chat Application

A real-time chat application built with Python Tkinter and Firebase authentication.

## Features

- Real-time text messaging
- Firebase authentication
- Socket-based communication
- Cross-platform support

## Quick Start Guide

### Prerequisites

- Python 3.7 or higher
- Git
- Firebase account

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ducinviciable/Tkinder-Chat.git
cd Tkinder-Chat
```

### Step 2: Install Dependencies

```bash
pip install firebase-admin python-dotenv
```

### Step 3: Firebase Setup

#### 3.1 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name (e.g., "my-chat-app")
4. Enable Google Analytics (optional)
5. Click "Create project"

#### 3.2 Enable Authentication

1. In Firebase Console, go to "Authentication" → "Sign-in method"
2. Enable "Email/Password" provider
3. Click "Save"

#### 3.3 Get Firebase Web API Key

1. Go to "Project settings" (gear icon)
2. In "General" tab, find "Web API Key"
3. Copy the API key (starts with "AIzaSy...")

#### 3.4 Create Service Account

1. Go to "Project settings" → "Service accounts"
2. Click "Generate new private key"
3. Download the JSON file
4. **Keep this file secure - never share it publicly!**

### Step 4: Configure Environment Variables

#### 🚀 Quick Setup (Recommended for Beginners)

Use our automated setup script:

```bash
python setup_env.py
```

This script will guide you through the entire configuration process step by step.

#### Manual Setup

Choose one of the following methods:

#### Method 1: Environment Variables (Recommended)

**Windows (PowerShell):**
```powershell
# Set Firebase Web API Key
$env:FIREBASE_WEB_API_KEY = "AIzaSyYour_Web_API_Key_Here"

# Set Firebase Service Account (replace with your actual JSON content)
$env:FIREBASE_SERVICE_ACCOUNT_KEY = '{"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"...","universe_domain":"googleapis.com"}'
```

**Windows (Command Prompt):**
```cmd
set FIREBASE_WEB_API_KEY=AIzaSyYour_Web_API_Key_Here
set FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project-id",...}
```

**Linux/Mac:**
```bash
export FIREBASE_WEB_API_KEY="AIzaSyYour_Web_API_Key_Here"
export FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project-id",...}'
```

#### Method 2: Using .env File (Alternative)

1. Copy `env.example` to `.env`:
```bash
cp env.example .env
```

2. Edit `.env` file with your actual values:
```env
FIREBASE_WEB_API_KEY=AIzaSyYour_Web_API_Key_Here
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project-id",...}
```

3. Install python-dotenv and modify code to load .env file:
```bash
pip install python-dotenv
```

### Step 5: Running the Application

#### 5.1 Start the Server

Open a terminal/command prompt and run:
```bash
cd Server
python server.py
```

You should see:
```
Server is listening on port 8080...
```

#### 5.2 Start the Client

Open another terminal/command prompt and run:
```bash
cd Client
python run.py
```

#### 5.3 Test the Application

1. The client should open a login window
2. Create a new account or sign in with existing credentials
3. Once authenticated, you'll see the chat window
4. Type messages and press Enter to send them
5. Open multiple client instances to test multi-user chat

### Step 6: Verification

To verify your setup is working correctly:

1. **Check Firebase API Key:**
```bash
python -c "from lib.firebase import API_KEY; print('Firebase API Key loaded:', 'Yes' if API_KEY else 'No')"
```

2. **Check Server Firebase Connection:**
Look for this message in server console:
```
[Auth] Firebase initialized from environment variable
```

3. **Test Authentication:**
Try creating a new account in the client - it should work without errors.

## Security Notes

- **Never commit Firebase service account keys to version control**
- Use environment variables or secure file storage for credentials
- The `firebase-service.json` file is ignored by Git for security reasons

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
│   └── firebase.py  # Firebase configuration
└── README.md        # This file
```

## Troubleshooting

### Firebase Authentication Issues

1. Ensure your service account has the correct permissions
2. Check that the project ID matches your Firebase project
3. Verify that Authentication is enabled in Firebase Console

### Connection Issues

1. Make sure the server is running on port 8080
2. Check firewall settings
3. Verify network connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.
