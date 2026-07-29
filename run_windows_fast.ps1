param(
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"

Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/ and enable 'Add Python to PATH'." -ForegroundColor Yellow
    exit 1
}

$venvPython = ".\.venv\Scripts\python.exe"
$depsMarker = ".\.venv\.deps_installed"
$requirements = "requirements.local.txt"
if (-not (Test-Path $requirements)) {
    $requirements = "requirements.txt"
}

$needsInstall = $false

Write-Host "[2/4] Ensuring virtual environment..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    $needsInstall = $true
}

if ($InstallDeps) {
    $needsInstall = $true
}

if (-not (Test-Path $depsMarker)) {
    $needsInstall = $true
}

if ((Test-Path $depsMarker) -and (Test-Path $requirements)) {
    $reqTime = (Get-Item $requirements).LastWriteTimeUtc
    $markerTime = (Get-Item $depsMarker).LastWriteTimeUtc
    if ($reqTime -gt $markerTime) {
        $needsInstall = $true
    }
}

if ($needsInstall) {
    Write-Host "[3/4] Installing/updating dependencies..." -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt
    New-Item -Path $depsMarker -ItemType File -Force | Out-Null
} else {
    Write-Host "[3/4] Skipping dependency install (already up to date)." -ForegroundColor DarkGreen
}

Write-Host "[4/4] Starting app..." -ForegroundColor Green
& $venvPython app.py
