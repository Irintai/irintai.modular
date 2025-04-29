
@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo IrintAI Assistant Documentation - Auto-Deployment to GitHub Pages
echo ========================================================

REM Ask user for repository name
set /p repo_name="Enter your GitHub repository name (e.g., IrintAI-Assistant-docs): "
set /p github_username="Enter your GitHub username: Irintai"

REM Confirm presence of Git
where git >nul 2>nul
if errorlevel 1 (
    echo Git is not installed or not in PATH. Please install Git first.
    pause
    exit /b
)

echo Initializing local repository...
git init

echo Adding all files...
git add .

echo Committing changes...
git commit -m "Deploy IrintAI Assistant Documentation update"

echo Adding GitHub remote...
git remote add origin https://github.com/!github_username!/!repo_name!.git

echo Setting main branch...
git branch -M main

echo Pushing to GitHub...
git push -u origin main

echo ========================================================
echo Deployment complete!
echo Now go to your repository Settings > Pages to enable GitHub Pages.
echo ========================================================
pause
exit
