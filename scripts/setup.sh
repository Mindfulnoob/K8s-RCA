#!/usr/bin/env bash
set -e

echo "=== Initializing Kubernetes RCA Agent Environment ==="

# 1. Check Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtualenv and installing dependencies..."
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Check Kind cluster (optional)
if command -v kind &> /dev/null; then
    if ! kind get clusters | grep -q "kube-rca-cluster"; then
        echo "Creating Kind cluster 'kube-rca-cluster'..."
        kind create cluster --name kube-rca-cluster --config infra/kind-cluster-config.yaml
        kubectl apply -f infra/k8s/base-services/
    else
        echo "Kind cluster 'kube-rca-cluster' already running."
    fi
else
    echo "Kind not detected in PATH. Agent will run using high-fidelity in-memory simulated cluster provider."
fi

# 3. Setup Frontend if npm is available
if [ -d "frontend" ] && command -v npm &> /dev/null; then
    echo "Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

echo "=== Setup Complete! ==="
echo "To start backend:  python -m uvicorn backend.app.main:app --port 8000"
echo "To start frontend: cd frontend && npm run dev"
