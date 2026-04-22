@echo off
REM Mosquitto MQTT Broker Setup Script for Windows
REM For ESP32 OTA Backend with mosquitto-go-auth

echo ==========================================
echo Mosquitto MQTT Broker Setup for Windows
echo ESP32 OTA Backend Authentication
echo ==========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires Administrator privileges
    echo Please run as Administrator
    pause
    exit /b 1
)

REM Check if Mosquitto is installed
where mosquitto >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Mosquitto not found in PATH
    echo.
    echo Please install Mosquitto:
    echo 1. Download from: https://mosquitto.org/download/
    echo 2. Install to default location: C:\Program Files\mosquitto
    echo 3. Add to PATH: C:\Program Files\mosquitto
    echo.
    pause
    exit /b 1
)

echo [OK] Mosquitto found
echo.

REM Find Mosquitto installation directory
for /f "tokens=*" %%i in ('where mosquitto') do set MOSQUITTO_PATH=%%i
for %%i in ("%MOSQUITTO_PATH%") do set MOSQUITTO_DIR=%%~dpi
echo Mosquitto directory: %MOSQUITTO_DIR%
echo.

REM Check for mosquitto-go-auth plugin
echo Checking for mosquitto-go-auth plugin...
if exist "%MOSQUITTO_DIR%mosquitto-go-auth.dll" (
    echo [OK] mosquitto-go-auth plugin found
) else (
    echo WARNING: mosquitto-go-auth.dll not found
    echo.
    echo Please install mosquitto-go-auth:
    echo 1. Download from: https://github.com/iegomez/mosquitto-go-auth/releases
    echo 2. Copy mosquitto-go-auth.dll to: %MOSQUITTO_DIR%
    echo.
    echo Continuing anyway...
)
echo.

REM Backup existing config
echo Backing up existing configuration...
if exist "%MOSQUITTO_DIR%mosquitto.conf" (
    copy "%MOSQUITTO_DIR%mosquitto.conf" "%MOSQUITTO_DIR%mosquitto.conf.backup.%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%" >nul
    echo [OK] Backup created
) else (
    echo No existing config found
)
echo.

REM Copy our config file
echo Installing mosquitto configuration...
if exist "mosquitto.conf" (
    REM Update paths for Windows
    powershell -Command "(gc mosquitto.conf) -replace '/usr/lib/mosquitto-go-auth.so', '%MOSQUITTO_DIR:\=\\%mosquitto-go-auth.dll' -replace '/var/lib/mosquitto/', '%MOSQUITTO_DIR:\=\\%data\\' -replace '/var/log/mosquitto/', '%MOSQUITTO_DIR:\=\\%log\\' | Out-File -encoding ASCII '%MOSQUITTO_DIR%mosquitto.conf'"
    echo [OK] Configuration installed
) else (
    echo ERROR: mosquitto.conf not found in current directory
    echo Please copy mosquitto.conf to: %MOSQUITTO_DIR%
    pause
    exit /b 1
)
echo.

REM Create required directories
echo Creating required directories...
if not exist "%MOSQUITTO_DIR%data\" mkdir "%MOSQUITTO_DIR%data"
if not exist "%MOSQUITTO_DIR%log\" mkdir "%MOSQUITTO_DIR%log"
echo [OK] Directories created
echo.

REM Prompt for backend configuration
echo Backend Configuration
echo ==========================================
echo INFO: The backend should be running on the SAME server
echo INFO: Default is 127.0.0.1:5000 for localhost connections
echo.
set /p BACKEND_HOST="Enter backend host (default: http://127.0.0.1): "
if "%BACKEND_HOST%"=="" set BACKEND_HOST=http://127.0.0.1

set /p BACKEND_PORT="Enter backend port (default: 5000): "
if "%BACKEND_PORT%"=="" set BACKEND_PORT=5000

echo.
echo Updating configuration with backend settings...
powershell -Command "(gc '%MOSQUITTO_DIR%mosquitto.conf') -replace 'auth_opt_http_host .*', 'auth_opt_http_host %BACKEND_HOST%' | Out-File -encoding ASCII '%MOSQUITTO_DIR%mosquitto.conf'"
powershell -Command "(gc '%MOSQUITTO_DIR%mosquitto.conf') -replace 'auth_opt_http_port .*', 'auth_opt_http_port %BACKEND_PORT%' | Out-File -encoding ASCII '%MOSQUITTO_DIR%mosquitto.conf'"
echo [OK] Configuration updated
echo.

REM Install/restart Mosquitto service
echo Installing/restarting Mosquitto service...
sc query mosquitto >nul 2>&1
if %errorLevel% equ 0 (
    echo Stopping existing service...
    net stop mosquitto >nul 2>&1
    sc delete mosquitto >nul 2>&1
)

echo Installing Mosquitto as Windows service...
sc create mosquitto binPath= "\"%MOSQUITTO_DIR%mosquitto.exe\" -c \"%MOSQUITTO_DIR%mosquitto.conf\"" start= auto DisplayName= "Mosquitto MQTT Broker"
if %errorLevel% neq 0 (
    echo ERROR: Failed to install service
    pause
    exit /b 1
)

echo Starting Mosquitto service...
net start mosquitto
if %errorLevel% neq 0 (
    echo ERROR: Failed to start service
    echo Check the event viewer for error details
    pause
    exit /b 1
)

echo [OK] Mosquitto is running!
echo.

REM Display summary
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Configuration Details:
echo   • Config file: %MOSQUITTO_DIR%mosquitto.conf
echo   • Backend: %BACKEND_HOST%:%BACKEND_PORT%
echo   • Anonymous access: ENABLED (for testing)
echo   • Log: %MOSQUITTO_DIR%log\mosquitto.log
echo.
echo WARNING: For production deployment:
echo   1. Edit %MOSQUITTO_DIR%mosquitto.conf
echo   2. Set allow_anonymous to false
echo   3. Enable TLS/SSL encryption
echo   4. Restart service: net stop mosquitto ^& net start mosquitto
echo.
echo Useful Commands:
echo   • Check status: sc query mosquitto
echo   • View config: notepad "%MOSQUITTO_DIR%mosquitto.conf"
echo   • Restart: net stop mosquitto ^& net start mosquitto
echo   • Test: mosquitto_pub -h localhost -t test/topic -m "Hello"
echo.
echo ==========================================
echo.
pause
