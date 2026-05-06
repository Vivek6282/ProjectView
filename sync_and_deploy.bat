@echo off
echo ============================================================
echo Project View — Sync & Deploy Helper
echo ============================================================
echo.

echo [1/3] Applying database migrations...
uv run manage.py makemigrations accounts
uv run manage.py migrate accounts
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
git commit -m "Implement cinematic welcome, role-based tutorials, and mandatory onboarding"
git push
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
