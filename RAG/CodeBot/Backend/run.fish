#!/usr/bin/env fish
echo "=== Running prep.py to build vectorstore ==="
python prep.py

echo "=== Starting FastAPI server (main.py) ==="
uvicorn main:app --reload --host 0.0.0.0 --port 8000
