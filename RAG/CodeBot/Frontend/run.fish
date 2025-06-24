#!/usr/bin/env fish

echo "=== Starting Streamlit frontend (app.py) ==="
pipenv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0
