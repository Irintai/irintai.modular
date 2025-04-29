
@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo IrintAI Assistant Project - Auto-Packager
echo ========================================================

REM Ask user for version number
set /p version="Enter the version number (e.g., 2.0): "
set zipname=IrintAI_Assistant_Offline_Viewer_v!version!.zip

echo Creating package: !zipname!

REM Create a temporary packaging folder
set packdir=package_temp
mkdir "!packdir!"

REM Copy necessary files
copy /Y irintai_architecture_diagram_full_offline.html "!packdir!"
copy /Y launch_irintai_viewer.bat "!packdir!"
copy /Y launch_irintai_viewer_smart.bat "!packdir!"
copy /Y VERSION.txt "!packdir!"
copy /Y README.txt "!packdir!"
copy /Y mermaid.min.js "!packdir!"

REM Zip the folder (assumes powershell is available)
powershell -Command "Compress-Archive -Path '!packdir!\*' -DestinationPath '!zipname!'"

REM Cleanup
rmdir /S /Q "!packdir!"

echo ========================================================
echo Packaging complete: !zipname!
echo ========================================================
pause
exit
