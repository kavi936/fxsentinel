#!/usr/bin/env python3

import os
import sys
from datetime import datetime

print(f"🔍 Debug Flask Startup - {datetime.now()}")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

# Test basic Flask import
try:
    from flask import Flask
    print("✅ Flask import successful")
except Exception as e:
    print(f"❌ Flask import failed: {e}")
    sys.exit(1)

# Test app import
try:
    print("🔍 Testing app import...")
    import app
    print("✅ App import successful")
except Exception as e:
    print(f"❌ App import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Flask app creation
try:
    print("🔍 Testing Flask app creation...")
    test_app = Flask(__name__)
    print("✅ Flask app creation successful")
except Exception as e:
    print(f"❌ Flask app creation failed: {e}")
    sys.exit(1)

# Test if we can access the app object
try:
    print("🔍 Testing app object access...")
    print(f"App name: {app.app.name}")
    print(f"App debug: {app.app.debug}")
    print("✅ App object access successful")
except Exception as e:
    print(f"❌ App object access failed: {e}")
    import traceback
    traceback.print_exc()

print("🔍 Debug complete")
