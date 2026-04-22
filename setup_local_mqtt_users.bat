@echo off
REM Setup Script for Local MQTT Users (Windows)
REM Creates password file and ACL configuration for local server clients

echo ==========================================
echo Local MQTT Users Setup for Windows
echo ESP32 OTA Backend
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
where mosquitto_passwd >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: mosquitto_passwd not found in PATH
    echo Please install Mosquitto first
    pause
    exit /b 1
)

REM Find Mosquitto installation directory
for /f "tokens=*" %%i in ('where mosquitto') do set MOSQUITTO_PATH=%%i
for %%i in ("%MOSQUITTO_PATH%") do set MOSQUITTO_DIR=%%~dpi

echo Mosquitto directory: %MOSQUITTO_DIR%
echo.

REM Create auth directory
set AUTH_DIR=%MOSQUITTO_DIR%auth
set PASSWORD_FILE=%AUTH_DIR%\passwords
set ACL_FILE=%AUTH_DIR%\acl

echo Creating authentication directory...
if not exist "%AUTH_DIR%" mkdir "%AUTH_DIR%"
echo [OK] Directory created: %AUTH_DIR%
echo.

REM Create local admin user
echo ==========================================
echo Creating Local Admin User
echo ==========================================
echo.
echo This user will have FULL access to all MQTT topics.
echo Use this for local server monitoring, admin scripts, etc.
echo.

set /p USERNAME="Enter username for local admin (default: admin): "
if "%USERNAME%"=="" set USERNAME=admin

echo.
echo Creating user: %USERNAME%
echo.

REM Create password file
if exist "%PASSWORD_FILE%" (
    echo Password file exists. Adding/updating user...
    mosquitto_passwd "%PASSWORD_FILE%" %USERNAME%
) else (
    echo Creating new password file...
    mosquitto_passwd -c "%PASSWORD_FILE%" %USERNAME%
)

if %errorLevel% neq 0 (
    echo ERROR: Failed to create user
    pause
    exit /b 1
)

echo [OK] User '%USERNAME%' created successfully
echo.

REM Additional users
echo ==========================================
echo Additional Users (Optional)
echo ==========================================
echo.

:ADD_MORE_LOOP
set /p ADD_MORE="Add another user? (y/n): "
if /i "%ADD_MORE%"=="y" (
    set /p EXTRA_USER="Enter username: "
    if not "%EXTRA_USER%"=="" (
        mosquitto_passwd "%PASSWORD_FILE%" !EXTRA_USER!
        if %errorLevel% equ 0 (
            echo [OK] User '!EXTRA_USER!' created
        ) else (
            echo ERROR: Failed to create user
        )
    )
    goto ADD_MORE_LOOP
)

echo.
echo [OK] Password file created
echo.

REM Install ACL configuration
echo Installing ACL configuration...
if exist "mosquitto_acl.conf" (
    copy "mosquitto_acl.conf" "%ACL_FILE%" >nul
    
    REM Add user to ACL
    echo. >> "%ACL_FILE%"
    echo # Added by setup script >> "%ACL_FILE%"
    echo user %USERNAME% >> "%ACL_FILE%"
    echo topic readwrite # >> "%ACL_FILE%"
    
    echo [OK] ACL file installed: %ACL_FILE%
) else (
    echo WARNING: mosquitto_acl.conf not found. Creating basic ACL...
    (
        echo # Mosquitto ACL - Auto-generated
        echo # User: %USERNAME% has full access
        echo user %USERNAME%
        echo topic readwrite #
    ) > "%ACL_FILE%"
    echo [OK] Basic ACL created
)
echo.

REM Display created users
echo ==========================================
echo Created Users
echo ==========================================
echo.
if exist "%PASSWORD_FILE%" (
    echo Users in %PASSWORD_FILE%:
    for /f "tokens=1 delims=:" %%u in (%PASSWORD_FILE%) do echo   • %%u
) else (
    echo No users found
)
echo.

REM Check configuration
echo ==========================================
echo Configuration Check
echo ==========================================
echo.

findstr /C:"auth_opt_backends" "%MOSQUITTO_DIR%mosquitto.conf" | findstr "files" >nul
if %errorLevel% equ 0 (
    echo [OK] Files backend enabled in mosquitto.conf
) else (
    echo WARNING: Files backend not found in mosquitto.conf
    echo Add this to %MOSQUITTO_DIR%mosquitto.conf:
    echo   auth_opt_backends files, http
    echo   auth_opt_password_path %PASSWORD_FILE:\=/%
    echo   auth_opt_acl_path %ACL_FILE:\=/%
)
echo.

REM Update mosquitto.conf paths for Windows
echo Updating mosquitto.conf with Windows paths...
powershell -Command "(gc '%MOSQUITTO_DIR%mosquitto.conf') -replace 'auth_opt_password_path .*', 'auth_opt_password_path %PASSWORD_FILE:\=/%' | Out-File -encoding ASCII '%MOSQUITTO_DIR%mosquitto.conf'"
powershell -Command "(gc '%MOSQUITTO_DIR%mosquitto.conf') -replace 'auth_opt_acl_path .*', 'auth_opt_acl_path %ACL_FILE:\=/%' | Out-File -encoding ASCII '%MOSQUITTO_DIR%mosquitto.conf'"
echo [OK] Configuration updated
echo.

REM Restart Mosquitto
set /p RESTART="Restart Mosquitto service now? (y/n): "
if /i "%RESTART%"=="y" (
    echo Restarting Mosquitto service...
    net stop mosquitto >nul 2>&1
    timeout /t 2 /nobreak >nul
    net start mosquitto
    if %errorLevel% equ 0 (
        echo [OK] Mosquitto restarted successfully
    ) else (
        echo ERROR: Failed to restart Mosquitto
        echo Check Windows Event Viewer for errors
    )
) else (
    echo Remember to restart Mosquitto service:
    echo   net stop mosquitto ^& net start mosquitto
)
echo.

REM Display connection info
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Local MQTT User Configuration:
echo   • Username: %USERNAME%
echo   • Password: (the one you entered)
echo   • Access: Full (all topics)
echo   • Files:
echo       - Passwords: %PASSWORD_FILE%
echo       - ACL: %ACL_FILE%
echo.
echo Connection Examples:
echo.
echo 1. Publish to any topic:
echo    mosquitto_pub -h localhost -u "%USERNAME%" -P "yourpassword" ^
echo      -t "system/test" -m "Hello from server"
echo.
echo 2. Subscribe to all topics:
echo    mosquitto_sub -h localhost -u "%USERNAME%" -P "yourpassword" ^
echo      -t "#" -v
echo.
echo 3. Subscribe to device topics:
echo    mosquitto_sub -h localhost -u "%USERNAME%" -P "yourpassword" ^
echo      -t "devices/#" -v
echo.
echo User Management Commands:
echo   • Add user: mosquitto_passwd %PASSWORD_FILE% username
echo   • Delete user: mosquitto_passwd -D %PASSWORD_FILE% username
echo   • Change password: mosquitto_passwd %PASSWORD_FILE% username
echo.
echo ==========================================
echo.
pause
