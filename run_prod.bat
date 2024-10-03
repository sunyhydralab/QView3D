@echo off
setlocal enabledelayedexpansion

:env
for /f "usebackq tokens=1,* delims==" %%a in ("server/.env") do (
    set "%%a=%%b"
)

:build
echo Running docker container
call PORT=%FLASK_RUN_HOST% docker-compose up --build
if errorlevel 1 (
    echo Server failed to start. Exiting...
    exit /b 1
)