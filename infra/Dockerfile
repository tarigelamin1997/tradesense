
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./
COPY core-requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r core-requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY core/ ./core/
COPY analytics/ ./analytics/
COPY connectors/ ./connectors/
COPY models/ ./models/
COPY metrics/ ./metrics/

# Create logs directory
RUN mkdir -p logs backend/logs

# Create non-root user
RUN useradd -m -u 1000 tradesense && \
    chown -R tradesense:tradesense /app
USER tradesense

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)"

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
