$ErrorActionPreference = "Stop"

Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/ and enable 'Add Python to PATH'." -ForegroundColor Yellow
    exit 1
}

Write-Host "[2/4] Creating virtual environment (.venv) if needed..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

Write-Host "[3/4] Activating environment and installing dependencies..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
if (Test-Path "requirements.local.txt") {
    & .\.venv\Scripts\python.exe -m pip install -r requirements.local.txt
} else {
    & .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

Write-Host "[4/4] Starting app..." -ForegroundColor Green
& .\.venv\Scripts\python.exe app.py
