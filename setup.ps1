# PowerShell script to set up virtual environment and run setup.py

# Display ASCII art banner
Write-Host @"
 ___       _       _      _    ___   _           _     _              _   
|_ _| _ _ (_) _ _ | |_   /_\  |_ _| / _| ___  __(_) __| |_ __ _ _ _  | |_ 
 | | | '_|| || ' \|  _| / _ \  | | |  _|(_-< (_-< |(_-<  _/ _` | ' \ |  _|
|___||_|  |_||_||_|\__|/_/ \_\|___||_|  /__/ /__/_|/__/\__\__,_|_||_| \__|
                                                                          
"@ -ForegroundColor Cyan

Write-Host "CUDA Detection and Automatic Setup" -ForegroundColor Yellow
Write-Host "===================================" -ForegroundColor Yellow

# Check if virtual environment exists, create if not
if (-not (Test-Path ".\.venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Run the setup script
Write-Host "Running setup script..." -ForegroundColor Green
python setup.py

# End message
Write-Host "Setup complete!" -ForegroundColor Green
