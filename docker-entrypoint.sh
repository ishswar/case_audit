#!/bin/bash
set -e

# Define services
SERVICE="${1:-all}"

# Start backend service
start_backend() {
    echo "Starting FastAPI backend service..."
    cd /app/application_server/backend
    exec uvicorn main:app --host 0.0.0.0 --port 8000
}

# Start frontend service
start_frontend() {
    echo "Starting Streamlit frontend service..."
    cd /app/application_server/frontend
    exec streamlit run main.py --server.port=8501 --server.address=0.0.0.0
}

# Start both services using tmux
start_all() {
    echo "Starting both backend and frontend services..."
    apt-get update && apt-get install -y tmux
    tmux new-session -d -s "backend" "cd /app/application_server/backend && uvicorn main:app --host 0.0.0.0 --port 8000"
    echo "Backend started in tmux session"
    sleep 5  # Give the backend time to start
    cd /app/application_server/frontend
    exec streamlit run main.py --server.port=8501 --server.address=0.0.0.0
}

# Execute the specified service
case "${SERVICE}" in
    backend)
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        start_all
        ;;
    *)
        echo "Unknown service: ${SERVICE}"
        echo "Available services: backend, frontend, all"
        exit 1
        ;;
esac 