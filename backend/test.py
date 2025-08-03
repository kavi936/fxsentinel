#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("Current directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))

try:
    import flask
    print("Flask version:", flask.__version__)
except ImportError as e:
    print("Flask not found:", e)

try:
    import gunicorn
    print("Gunicorn found")
except ImportError as e:
    print("Gunicorn not found:", e) 