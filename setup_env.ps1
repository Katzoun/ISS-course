# Setup script for ISS course virtual environment
# This script creates a virtual environment and installs required packages

Write-Host "Setting up ISS course environment..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Python is not installed or not in PATH. Please install Python first." -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

py -m venv venv

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
py -m pip install --upgrade pip

# Install requirements
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "Requirements installed successfully!" -ForegroundColor Green
} else {
    Write-Host "requirements.txt not found. Installing basic packages..." -ForegroundColor Yellow
    pip install matplotlib numpy jupyter
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To activate the environment in the future, run: .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "To deactivate the environment, run: deactivate" -ForegroundColor Cyan