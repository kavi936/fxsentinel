# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY . .

# Expose port (Railway will set the PORT environment variable)
EXPOSE $PORT

# Start the application with proper configuration for Railway
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 2 