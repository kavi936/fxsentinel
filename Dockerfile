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

# Copy ALL files from current directory to /app
COPY . .

# Force rebuild - increment version
LABEL build_version="11.0.0"
LABEL build_date="2024-01-15"

# Debug: Show what's actually in the container
RUN echo "=== DEBUGGING BUILD CONTEXT ===" && \
    echo "Current directory: $(pwd)" && \
    echo "Files in root:" && \
    ls -la && \
    echo "Looking for main_app.py:" && \
    find . -name "main_app.py" -type f && \
    echo "Looking for backend:" && \
    find . -name "backend" -type d && \
    echo "Python files:" && \
    find . -name "*.py" | head -5

# Expose port
EXPOSE 8000

# Set environment variable for Flask
ENV FLASK_APP=main_app.py
ENV FLASK_ENV=production

# Start the application
CMD ["python", "main_app.py"]