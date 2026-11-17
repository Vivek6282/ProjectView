@echo off
echo ============================================================
echo Project View - Sync and Deploy Helper
echo ============================================================
echo.

if "%~1"=="" (
    echo ERROR: Commit message is required.
    echo Usage: sync_and_deploy.bat "Your commit message"
    exit /b 1
)

echo [1/2] Checking for unreviewed untracked files...
set "HAS_UNTRACKED="
for /f "delims=" %%i in ('git status --porcelain ^| findstr /r "^\?\?"') do (
    set "HAS_UNTRACKED=1"
)

if defined HAS_UNTRACKED (
    echo.
    echo ERROR: Untracked files detected that have not been reviewed:
    git status -s
    echo.
    echo Please review and stage them with 'git add ^<file^>' or add them to .gitignore before deploying.
    pause
    exit /b 1
)

echo.
echo [2/2] Committing and Pushing to Render...
git add -A
git commit -m "%~1"
git push -u origin HEAD
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Git push failed. Please check your internet or Render credentials.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================================
echo SUCCESS! Your changes are being deployed to Render.
echo ============================================================
pause
