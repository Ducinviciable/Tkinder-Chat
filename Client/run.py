#!/usr/bin/env python3
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Now import and run main
from Chat.Client.main import main

if __name__ == '__main__':
    main()
