#!/bin/bash

echo "Testing Docker build locally..."

# Build the Docker image
cd /home/tarigelamin/Desktop/tradesense
docker build -f src/backend/Dockerfile -t tradesense-test .

# Run the container
echo "Running container..."
docker run --rm -p 8000:8000 \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/tradesense" \
  -e JWT_SECRET_KEY="test-secret-key" \
  -e ENVIRONMENT="development" \
  -e PORT=8000 \
  tradesense-test