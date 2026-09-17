# PowerShell Setup Script for KubeRCA Agent

Write-Host "=== Initializing Kubernetes RCA Agent Environment (Windows) ===" -ForegroundColor Cyan

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

Write-Host "Installing backend dependencies..."
.\venv\Scripts\pip install -r backend\requirements.txt

if (Get-Command "npm" -ErrorAction SilentlyContinue) {
    if (Test-Path "frontend") {
        Write-Host "Installing frontend packages..."
        Push-Location frontend
        npm install
        Pop-Location
    }
}

Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host "To start backend:  .\venv\Scripts\python -m uvicorn backend.app.main:app --port 8000"
Write-Host "To start frontend: cd frontend; npm run dev"
