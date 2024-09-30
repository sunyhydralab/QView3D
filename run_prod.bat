@echo off
setlocal enabledelayedexpansion

:env
for /f "usebackq tokens=1,* delims==" %%a in ("server/.env") do (
    set "%%a=%%b"
)

:build
echo Building the client...
cd client
call npm run build-only
if errorlevel 1 (
    echo Build failed. Exiting...
    exit /b 1
)
goto run

:run
echo Starting the production server...
cd ../server
call gunicorn --bind=%FLASK_RUN_HOST%:%FLASK_RUN_PORT% --worker-class eventlet -w 1 app:app
if errorlevel 1 (
    echo Server failed to start. Exiting...
    exit /b 1
)