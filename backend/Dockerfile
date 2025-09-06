# Dockerfile for FXSentinel Background Worker
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

# Copy the application code
COPY . .

# Debug: Show what's actually in the container
RUN echo "=== DEBUGGING BUILD CONTEXT ===" && \
    echo "Current directory: $(pwd)" && \
    echo "Files in root:" && \
    ls -la && \
    echo "Looking for app.py:" && \
    find . -name "app.py" -type f && \
    echo "Python files:" && \
    find . -name "*.py" | head -10

# Expose port
EXPOSE 8000

# Start command - run the main Flask app
CMD ["python3", "app.py"]
