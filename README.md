# Tkinter Chat Application

A real-time chat application built with Python Tkinter and Firebase authentication.

## Features

- Real-time text messaging
- Firebase authentication
- Socket-based communication
- Cross-platform support

## Setup

### 1. Install Dependencies

```bash
pip install firebase-admin python-dotenv
```

### 2. Firebase Configuration

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Authentication and create a service account
3. Download the service account key JSON file
4. Set up environment variables:

#### Option 1: Environment Variable (Recommended)

Set the `FIREBASE_SERVICE_ACCOUNT_KEY` environment variable with your service account JSON:

```bash
# Windows (PowerShell)
$env:FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project-id",...}'

# Windows (Command Prompt)
set FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project-id",...}

# Linux/Mac
export FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project-id",...}'
```

#### Option 2: File Path

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account file:

```bash
# Windows
set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\service-account-key.json

# Linux/Mac
export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### 3. Running the Application

1. Start the server:
```bash
cd Server
python server.py
```

2. Start the client:
```bash
cd Client
python run.py
```

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
