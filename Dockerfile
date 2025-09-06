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

# Explicitly verify key files are present
RUN echo "=== VERIFYING KEY FILES ===" && \
    ls -la main_app.py && \
    ls -la backend/ && \
    ls -la backend/services/ | head -10

# Add cache-busting label to force rebuild
LABEL build_version="10.0.0"
LABEL build_date="2024-01-15"

# Debug: Show what was actually copied
RUN echo "=== ROOT DIRECTORY ===" && ls -la /app/
RUN echo "=== BACKEND DIRECTORY ===" && ls -la /app/backend/ || echo "BACKEND DIRECTORY NOT FOUND"
RUN echo "=== MAIN APP.PY ===" && ls -la /app/main_app.py || echo "MAIN_APP.PY NOT FOUND"
RUN echo "=== BACKEND SERVICES ===" && ls -la /app/backend/services/ || echo "BACKEND SERVICES NOT FOUND"

# Expose port
EXPOSE 8000

# Start command - run the Flask app from root directory
CMD ["python", "main_app.py"]
