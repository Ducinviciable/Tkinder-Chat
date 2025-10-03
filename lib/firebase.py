"""
Firebase configuration module.

This module provides Firebase Web API key configuration.
The API key should be set via environment variable FIREBASE_WEB_API_KEY.
"""

import os

# Get Firebase Web API key from environment variable
# Set this in your environment: FIREBASE_WEB_API_KEY=your_api_key_here
API_KEY: str = os.environ.get('FIREBASE_WEB_API_KEY', '')

if not API_KEY:
    print("Warning: FIREBASE_WEB_API_KEY environment variable not set!")
    print("Please set it with your Firebase Web API key from Firebase console → Project settings → General → Web API Key")


