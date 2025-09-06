# Dockerfile for FXSentinel Main App
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

# Copy the entire application code
COPY . .

# Add cache-busting label to force rebuild
LABEL build_version="8.0.0"
LABEL build_date="2024-01-15"

# Debug: Show what was actually copied
RUN echo "=== ROOT DIRECTORY ===" && ls -la /app/
RUN echo "=== BACKEND DIRECTORY ===" && ls -la /app/backend/ || echo "BACKEND DIRECTORY NOT FOUND"
RUN echo "=== BACKEND APP.PY ===" && ls -la /app/backend/app.py || echo "APP.PY NOT FOUND"

# Expose port
EXPOSE 8000

# Start command - run the Flask app from root directory
CMD ["python", "main_app.py"]
