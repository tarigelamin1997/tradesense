FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set the working directory to where main.py is located
WORKDIR /app/src/backend

# Expose the port
EXPOSE 8000

# Run the application using Railway's PORT environment variable
CMD uvicorn main:app --host 0.0.0.0 --port $PORT