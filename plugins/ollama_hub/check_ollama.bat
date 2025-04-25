@echo off
echo Checking Ollama installation...
echo.
echo Trying format 1: ollama --version
ollama --version 2>nul
if %ERRORLEVEL% EQU 0 goto :found

echo Trying format 2: ollama -v
ollama -v 2>nul
if %ERRORLEVEL% EQU 0 goto :found

echo Trying format 3: ollama version
ollama version 2>nul
if %ERRORLEVEL% EQU 0 goto :found

echo Checking if Ollama is running...
echo Checking http://localhost:11434/api/version
powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing; if($response.StatusCode -eq 200) { Write-Host 'Ollama API is responding'; exit 0 } else { Write-Host 'Ollama API returned status code: ' $response.StatusCode; exit 1 } } catch { Write-Host 'Ollama API not responding: ' $_.Exception.Message; exit 1 }"
if %ERRORLEVEL% EQU 0 goto :running

echo Ollama not found or not running.
goto :notfound

:found
echo Ollama is installed. Checking if it is running...
powershell -command "try { $response = Invoke-WebRequest -Uri http://localhost:11434/api/version -UseBasicParsing; if($response.StatusCode -eq 200) { Write-Host 'Ollama API is responding'; exit 0 } else { Write-Host 'Ollama API returned status code: ' $response.StatusCode; exit 1 } } catch { Write-Host 'Ollama API not responding: ' $_.Exception.Message; exit 1 }"
if %ERRORLEVEL% EQU 0 goto :running
echo Ollama is installed but not running. Starting Ollama service...
start /B ollama serve
timeout /t 5 /nobreak > nul
goto :end

:running
echo Ollama is running properly!
goto :end

:notfound
echo Checking common Ollama installation paths...
if exist "C:\Program Files\Ollama\ollama.exe" (
  echo Found Ollama at C:\Program Files\Ollama\ollama.exe
  echo Adding C:\Program Files\Ollama to PATH for this session
  set "PATH=%PATH%;C:\Program Files\Ollama"
  echo Starting Ollama service...
  start /B ollama serve
  timeout /t 5 /nobreak > nul
  goto :end
)

if exist "C:\Ollama\ollama.exe" (
  echo Found Ollama at C:\Ollama\ollama.exe
  echo Adding C:\Ollama to PATH for this session
  set "PATH=%PATH%;C:\Ollama"
  echo Starting Ollama service...
  start /B ollama serve
  timeout /t 5 /nobreak > nul
  goto :end
)

if exist "%USERPROFILE%\Ollama\ollama.exe" (
  echo Found Ollama at %USERPROFILE%\Ollama\ollama.exe
  echo Adding %USERPROFILE%\Ollama to PATH for this session
  set "PATH=%PATH%;%USERPROFILE%\Ollama"
  echo Starting Ollama service...
  start /B ollama serve
  timeout /t 5 /nobreak > nul
  goto :end
)

if exist "%LOCALAPPDATA%\Ollama\ollama.exe" (
  echo Found Ollama at %LOCALAPPDATA%\Ollama\ollama.exe
  echo Adding %LOCALAPPDATA%\Ollama to PATH for this session
  set "PATH=%PATH%;%LOCALAPPDATA%\Ollama"
  echo Starting Ollama service...
  start /B ollama serve
  timeout /t 5 /nobreak > nul
  goto :end
)

echo Ollama not found. Please install it from https://ollama.ai
:end
