FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

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

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
