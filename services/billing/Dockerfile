FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Environment
ENV PYTHONPATH=/app
ENV PORT=8000

# Run
CMD ["python", "src/main.py"]