#!/bin/bash
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Starting Gunicorn server..."
gunicorn app:app --bind 0.0.0.0:$PORT 