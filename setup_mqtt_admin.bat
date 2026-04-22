@echo off
REM Setup MQTT Admin User for Mosquitto (Windows)
REM Creates password file and ACL for admin user with full access

setlocal

REM Configuration
set AUTH_DIR=C:\ProgramData\mosquitto\auth
set PASSWORD_FILE=%AUTH_DIR%\passwords
set ACL_FILE=%AUTH_DIR%\acl
set ADMIN_USERNAME=admin

echo =========================================
echo MQTT Admin User Setup (Windows)
echo =========================================
echo.

REM Create auth directory if it doesn't exist
if not exist "%AUTH_DIR%" (
    echo Creating auth directory: %AUTH_DIR%
    mkdir "%AUTH_DIR%"
)
"Alchohol@123"
REM Generate admin user password
echo Creating admin user: %ADMIN_USERNAME%
echo You will be prompted to enter a password...
echo.

REM Create password file (mosquitto_passwd will prompt for password)
mosquitto_passwd -c "%PASSWORD_FILE%" %ADMIN_USERNAME%

echo.
echo =========================================
echo Creating ACL file with full access...
echo =========================================

REM Create ACL file giving admin full access to all topics
(
echo # MQTT Access Control List
echo # Admin user has full access to all topics
echo.
echo user %ADMIN_USERNAME%
echo topic readwrite #
) > "%ACL_FILE%"

echo.
echo =========================================
echo Setup Complete!
echo =========================================
echo.
echo Admin user created: %ADMIN_USERNAME%
echo Password file: %PASSWORD_FILE%
echo ACL file: %ACL_FILE%
echo.
echo Test connection:
echo   mosquitto_pub -h localhost -u "%ADMIN_USERNAME%" -P ^<your-password^> -t "test/admin" -m "Hello"
echo.
echo Restart Mosquitto to apply changes:
echo   net stop mosquitto
echo   net start mosquitto
echo.

pause
