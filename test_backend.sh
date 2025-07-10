#!/bin/bash
cd /home/tarigelamin/Desktop/tradesense
source venv/bin/activate
cd src/backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 -m uvicorn main:app --port 8000 --host 0.0.0.0