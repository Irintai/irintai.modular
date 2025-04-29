@echo off
echo IrintAI Assistant Network Diagnostics
echo =============================
echo.
echo Checking internet connectivity...
ping -n 4 8.8.8.8
echo.
echo Checking DNS resolution...
nslookup google.com
nslookup ollama.ai
nslookup api.github.com
echo.
echo Checking proxy settings...
netsh winhttp show proxy
echo.
echo Checking firewall status...
netsh advfirewall show allprofiles state
echo.
echo Attempting to access Ollama API...
powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing -TimeoutSec 5; Write-Host "Response: $($response.StatusCode) $($response.StatusDescription)"; Write-Host $response.Content } catch { Write-Host "Error: $_" }"
echo.
echo Would you like to reset network settings? (Y/N)
set /p reset="Enter your choice: "
if /i "%reset%" == "Y" (
    echo Resetting network settings...
    ipconfig /flushdns
    netsh winsock reset
    echo Network settings reset. A system restart is recommended.
)
echo.
echo Press any key to exit...
pause > nul
