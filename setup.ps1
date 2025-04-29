# PowerShell script to set up virtual environment and run setup.py

# Display ASCII art banner
Write-Host @"
 ___       _       _      _    ___     _ _         _     _              _   
|_ _| _ _ (_) _ _ | |_   /_\  |_ _|   / __ \ ___  __(_) __| |_ __ _ _ _  | |_ 
 | | | '_|| || ' \|  _| / _ \  | |   |  __  |(_-< (_-< |(_-<  _/ _` | ' \ |  _|
|___||_|  |_||_||_|\__|/_/ \_\|___|  |_|  |_|/__/ /__/_|/__/\__\__,_|_||_| \__|
                                                                          
"@ -ForegroundColor Cyan

Write-Host "CUDA Detection and Automatic Setup" -ForegroundColor Yellow
Write-Host "===================================" -ForegroundColor Yellow

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.10+ and try again." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists, create if not
if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment. Exiting." -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to activate virtual environment. Exiting." -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to upgrade pip. Exiting." -ForegroundColor Red
    exit 1
}

# Run the setup script
Write-Host "Running setup script..." -ForegroundColor Green
python setup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Setup script failed. Please check the output above for errors." -ForegroundColor Red
    exit 1
}

# End message
Write-Host "Setup complete!" -ForegroundColor Green
