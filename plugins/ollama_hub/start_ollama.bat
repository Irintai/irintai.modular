@echo off
echo Starting Ollama service...
powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing; if($response.StatusCode -eq 200) { Write-Host 'Ollama is already running'; exit 0 } } catch {}"
if %ERRORLEVEL% EQU 0 goto :already_running

for %%p in (
  "C:\Program Files\Ollama\ollama.exe"
  "C:\Ollama\ollama.exe"
  "%USERPROFILE%\Ollama\ollama.exe"
  "%LOCALAPPDATA%\Ollama\ollama.exe"
) do (
  if exist %%p (
    echo Found Ollama at %%p
    echo Adding Ollama directory to PATH
    for %%d in (%%p\..) do set "OLLAMA_DIR=%%~fd"
    set "PATH=%PATH%;%OLLAMA_DIR%"
    echo Starting Ollama service...
    start /B ollama serve
    echo Ollama service started.
    echo Waiting for the service to initialize...
    timeout /t 5 /nobreak > nul
    goto :end
  )
)

echo Ollama executable not found. Please install Ollama from https://ollama.ai
goto :end

:already_running
echo Ollama is already running.
:end
echo.
echo You can now use IrintAI Assistant.
echo Press any key to exit...
pause > nul
