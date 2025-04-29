@echo off
echo IrintAI Assistant Resource Optimizer
echo ===============================
echo.
echo Checking for resource-intensive processes...
echo.
powershell -command "Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10 | Format-Table -AutoSize Id, ProcessName, CPU, WorkingSet"
echo.
echo Cleaning up temporary files...
powershell -command "Remove-Item -Path $env:TEMP\* -Recurse -Force -ErrorAction SilentlyContinue"
echo.
echo Checking for large log files in IrintAI Assistant...
dir /s /b "%~dp0..\data\logs\*.log" | findstr /v ""
echo.
echo Would you like to clean up old log files? (Y/N)
set /p clean="Enter your choice: "
if /i "%clean%" == "Y" (
    echo Cleaning up logs older than 7 days...
    forfiles /p "%~dp0..\data\logs" /s /m *.log /d -7 /c "cmd /c del @path" 2>nul
    echo Done cleaning logs.
)
echo.
echo Recommendations to improve system resources:
echo 1. Close unnecessary applications
echo 2. Restart the computer if it has been running for a long time
echo 3. Consider upgrading memory if consistently at high usage
echo 4. Check for malware that might be consuming resources
echo.
echo Press any key to exit...
pause > nul
