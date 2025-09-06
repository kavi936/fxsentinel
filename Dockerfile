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
LABEL build_version="4.0.0"
LABEL build_date="2024-01-15"

# Verify the file structure
RUN ls -la /app/
RUN ls -la /app/backend/ || echo "Backend directory not found"

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Start command - run the main Flask app
CMD ["python", "app.py"]
