@echo off
echo ============================================================
echo Project View — Sync & Deploy Helper
echo ============================================================
echo.

if "%~1"=="" (
    echo ERROR: Commit message is required.
    echo Usage: sync_and_deploy.bat "Your commit message"
    exit /b 1
)

echo [1/3] Applying database migrations...
uv run manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Migrations failed. Please check your TiDB connection.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Staging changes for Git...
git add .

echo.
echo [3/3] Committing and Pushing to Render...
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
