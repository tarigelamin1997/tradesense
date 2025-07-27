FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire backend directory structure
COPY . /app/

# Set working directory to where main.py actually is
WORKDIR /app/src/backend

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional required packages that might be missing
RUN pip install --no-cache-dir \
    uvicorn \
    fastapi \
    sqlalchemy \
    psycopg2-binary \
    python-jose \
    passlib \
    python-multipart \
    pydantic-settings \
    scikit-learn \
    bcrypt \
    httpx \
    pandas \
    numpy

# Set Python path to include current directory
ENV PYTHONPATH=/app/src/backend

# Set environment variable for port (Railway provides this)
ENV PORT=8000

# Copy start script
COPY src/backend/start.sh /app/src/backend/start.sh
RUN chmod +x /app/src/backend/start.sh

# Run the application (no --reload in production)
CMD ["/app/src/backend/start.sh"]
