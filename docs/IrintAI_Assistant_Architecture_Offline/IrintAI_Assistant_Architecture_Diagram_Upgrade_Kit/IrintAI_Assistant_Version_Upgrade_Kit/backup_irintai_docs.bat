
@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo IrintAI Assistant Documentation - Auto-Backup Script
echo ========================================================

REM Set backup folder and zip name with timestamp
set datetime=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set datetime=%datetime: =0%
set backup_zip=IrintAI_Assistant_Docs_Backup_!datetime!.zip

echo Creating backup file: !backup_zip!

REM Use PowerShell to zip the entire documentation folder
powershell -Command "Compress-Archive -Path * -DestinationPath '!backup_zip!'"

echo ========================================================
echo Backup complete: !backup_zip!
echo ========================================================
pause
exit
