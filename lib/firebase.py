import os

# Attempt to load variables from a local .env file if present
try:
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _dotenv_path = find_dotenv()
    if _dotenv_path:
        load_dotenv(_dotenv_path)
except Exception:
    # python-dotenv not installed or .env not found; ignore silently
    pass

# Get Firebase Web API key from environment variable
# Set this in your environment or .env: FIREBASE_WEB_API_KEY=...
API_KEY: str = os.environ.get('FIREBASE_WEB_API_KEY', '')

if not API_KEY:
    print("Warning: FIREBASE_WEB_API_KEY environment variable not set!")
    print("Please set it in your environment or .env with your Firebase Web API key")


