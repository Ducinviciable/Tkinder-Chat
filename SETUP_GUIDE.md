# 🚀 Quick Setup Guide

## For New Users - Step by Step

### 1. Clone & Install
```bash
git clone https://github.com/Ducinviciable/Tkinder-Chat.git
cd Tkinder-Chat
pip install firebase-admin python-dotenv
```

### 2. Firebase Setup (5 minutes)

#### Create Firebase Project:
1. Go to https://console.firebase.google.com/
2. Click "Create a project"
3. Name it (e.g., "my-chat-app")
4. Click "Create project"

#### Enable Authentication:
1. Go to "Authentication" → "Sign-in method"
2. Enable "Email/Password"
3. Click "Save"

#### Get API Key:
1. Go to "Project settings" (⚙️ icon)
2. Copy "Web API Key" (starts with AIzaSy...)

#### Create Service Account:
1. Go to "Project settings" → "Service accounts"
2. Click "Generate new private key"
3. Download JSON file
4. **Keep this file secure!**

### 3. Set Environment Variables

**Windows PowerShell:**
```powershell
# Replace with your actual values
$env:FIREBASE_WEB_API_KEY = "AIzaSyYour_Web_API_Key_Here"
$env:FIREBASE_SERVICE_ACCOUNT_KEY = '{"type":"service_account","project_id":"your-project-id",...}'
```

**Windows Command Prompt:**
```cmd
set FIREBASE_WEB_API_KEY=AIzaSyYour_Web_API_Key_Here
set FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project-id",...}
```

**Linux/Mac:**
```bash
export FIREBASE_WEB_API_KEY="AIzaSyYour_Web_API_Key_Here"
export FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project-id",...}'
```

### 4. Run the App

**Terminal 1 (Server):**
```bash
cd Server
python server.py
```

**Terminal 2 (Client):**
```bash
cd Client
python run.py
```

### 5. Test
1. Create account in client
2. Login
3. Start chatting!

## 🔧 Troubleshooting

### "Firebase API Key loaded: No"
- Check if FIREBASE_WEB_API_KEY is set correctly
- Restart terminal after setting environment variables

### "Firebase init failed"
- Check if FIREBASE_SERVICE_ACCOUNT_KEY is set correctly
- Verify JSON format is valid

### "Connection refused"
- Make sure server is running on port 8080
- Check firewall settings

### Authentication errors
- Verify Email/Password is enabled in Firebase Console
- Check service account permissions

## 📞 Need Help?

1. Check the full [README.md](README.md) for detailed instructions
2. Verify all environment variables are set correctly
3. Make sure Firebase project is configured properly
4. Check that all dependencies are installed

## 🎉 Success!

If you see these messages, you're all set:
- Server: "Server is listening on port 8080..."
- Server: "[Auth] Firebase initialized from environment variable"
- Client: Login window opens successfully
