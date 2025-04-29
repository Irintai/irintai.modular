@echo off
echo =======================================
echo IrintAI Assistant Fix and Verify Suite
echo =======================================
echo.

echo Step 1: Running diagnostic fixes...
powershell -ExecutionPolicy Bypass -File fix_diagnostics.ps1
echo.

echo Step 2: Starting Ollama server if not running...
call start_ollama.bat > nul
echo.

echo Step 3: Verifying diagnostic fixes...
python verify_diagnostics.py
echo.

echo Process complete! Press any key to exit...
pause > nul
