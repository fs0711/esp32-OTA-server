#!/bin/bash

# Verification Script for Dual-Binding Gunicorn Setup
# Tests both Unix socket (nginx) and localhost HTTP (MQTT auth)

echo "=========================================="
echo "Gunicorn Dual-Binding Verification"
echo "ESP32 OTA Backend"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SOCKET_PATH="/home/esp32ota-backend/esp32ota.sock"
HTTP_HOST="127.0.0.1"
HTTP_PORT="5000"
TEST_ENDPOINT="/api/static-data"

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Test 1: Check if gunicorn is running
echo "1. Checking Gunicorn Service..."
systemctl is-active --quiet esp32-ota
print_status $? "Gunicorn service is running"
echo ""

# Test 2: Check if Unix socket exists
echo "2. Checking Unix Socket..."
if [ -S "$SOCKET_PATH" ]; then
    print_status 0 "Unix socket exists: $SOCKET_PATH"
    ls -la "$SOCKET_PATH"
else
    print_status 1 "Unix socket NOT found: $SOCKET_PATH"
fi
echo ""

# Test 3: Check listening ports/sockets
echo "3. Checking Listening Interfaces..."
echo "Gunicorn should be listening on:"
echo "  - Unix socket: $SOCKET_PATH"
echo "  - TCP: $HTTP_HOST:$HTTP_PORT"
echo ""

if command -v netstat &> /dev/null; then
    echo "Current gunicorn bindings:"
    sudo netstat -tulpn | grep -E "gunicorn|esp32ota" || echo "  (No matches found)"
elif command -v ss &> /dev/null; then
    echo "Current gunicorn bindings:"
    sudo ss -tulpn | grep -E "gunicorn|esp32ota" || echo "  (No matches found)"
else
    echo -e "${YELLOW}⚠${NC} netstat/ss not available, skipping"
fi
echo ""

# Test 4: Test Unix socket connection
echo "4. Testing Unix Socket Connection..."
if [ -S "$SOCKET_PATH" ]; then
    RESPONSE=$(sudo curl -s --unix-socket "$SOCKET_PATH" "http://localhost$TEST_ENDPOINT" 2>&1)
    CURL_EXIT=$?
    
    if [ $CURL_EXIT -eq 0 ] && echo "$RESPONSE" | grep -q "gender\|statuses"; then
        print_status 0 "Unix socket connection successful"
        echo "   Response preview: ${RESPONSE:0:100}..."
    else
        print_status 1 "Unix socket connection failed"
        echo "   Error: $RESPONSE"
    fi
else
    print_status 1 "Cannot test - socket does not exist"
fi
echo ""

# Test 5: Test localhost HTTP connection
echo "5. Testing Localhost HTTP Connection..."
RESPONSE=$(curl -s "http://$HTTP_HOST:$HTTP_PORT$TEST_ENDPOINT" 2>&1)
CURL_EXIT=$?

if [ $CURL_EXIT -eq 0 ] && echo "$RESPONSE" | grep -q "gender\|statuses"; then
    print_status 0 "Localhost HTTP connection successful"
    echo "   Response preview: ${RESPONSE:0:100}..."
else
    print_status 1 "Localhost HTTP connection failed"
    echo "   Error: $RESPONSE"
    echo "   Make sure gunicorn is configured with: bind = ['unix:esp32ota.sock', '127.0.0.1:5000']"
fi
echo ""

# Test 6: Verify external port 5000 is blocked
echo "6. Security Check - External Port Access..."
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
echo "   Server IP: $PUBLIC_IP"
echo "   Testing if port $HTTP_PORT is blocked from external access..."

# Check firewall rules
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | grep -E "^5000.*DENY|^5000.*REJECT" || echo "not_blocked")
    if [ "$UFW_STATUS" != "not_blocked" ]; then
        print_status 0 "UFW blocking port 5000"
    else
        print_status 1 "WARNING: Port 5000 may not be blocked by UFW"
        echo -e "   ${YELLOW}Run: sudo ufw deny 5000/tcp${NC}"
    fi
elif command -v firewall-cmd &> /dev/null; then
    echo "   Using firewalld - check manually: firewall-cmd --list-ports"
elif command -v iptables &> /dev/null; then
    echo "   Using iptables - check manually: sudo iptables -L INPUT -n"
else
    echo -e "   ${YELLOW}⚠${NC} No firewall detected - ensure port 5000 is blocked externally"
fi
echo ""

# Test 7: Test MQTT Auth Endpoint
echo "7. Testing MQTT Auth Endpoint..."
AUTH_RESPONSE=$(curl -s -X POST "http://$HTTP_HOST:$HTTP_PORT/api/mqtt/auth" \
    -d "username=test&password=test" 2>&1)
CURL_EXIT=$?

if [ $CURL_EXIT -eq 0 ]; then
    if echo "$AUTH_RESPONSE" | grep -q "response_code"; then
        print_status 0 "MQTT auth endpoint is accessible"
        echo "   Response: ${AUTH_RESPONSE:0:150}..."
    else
        print_status 1 "MQTT auth endpoint returned unexpected response"
        echo "   Response: $AUTH_RESPONSE"
    fi
else
    print_status 1 "MQTT auth endpoint connection failed"
    echo "   Error: $AUTH_RESPONSE"
fi
echo ""

# Test 8: Check service logs
echo "8. Recent Service Logs..."
echo "Last 5 lines from gunicorn log:"
if [ -f "/var/log/esp32ota/error.log" ]; then
    sudo tail -n 5 /var/log/esp32ota/error.log | sed 's/^/   /'
else
    echo "   (Log file not found)"
fi
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo ""
echo "Expected Configuration:"
echo "  ✓ Nginx → Unix socket ($SOCKET_PATH)"
echo "  ✓ Mosquitto-go-auth → http://$HTTP_HOST:$HTTP_PORT"
echo "  ✓ Port $HTTP_PORT blocked from external access"
echo ""
echo "Next Steps:"
echo "  1. If any tests failed, check /var/log/esp32ota/error.log"
echo "  2. Verify gunicorn.conf.py has dual binding configured"
echo "  3. Restart services: sudo systemctl restart esp32-ota"
echo "  4. Test MQTT authentication: python test_mqtt_auth.py --device-id <id> --access-token <token>"
echo ""
echo "=========================================="
