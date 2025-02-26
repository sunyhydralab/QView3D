@echo off
setlocal enabledelayedexpansion

:env
for /f "usebackq tokens=1,* delims==" %%a in ("server/.env") do (
    set "%%a=%%b"
)

:build
echo Building docker container
call docker-compose build --build-arg PORT=%FLASK_RUN_PORT%
if errorlevel 1 (
    echo Server failed to build. Exiting...
    exit /b 1
)
goto run

:run
echo Running docker container
call docker run -p %FLASK_RUN_PORT%:%FLASK_RUN_PORT% qview3ddev-app
if errorlevel 1 (
    echo Server failed to start. Exiting...
    exit /b 1
)