#!/bin/bash

# Mosquitto MQTT Broker Setup Script
# For ESP32 OTA Backend with mosquitto-go-auth

set -e  # Exit on error

echo "=========================================="
echo "Mosquitto MQTT Broker Setup"
echo "ESP32 OTA Backend Authentication"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "❌ Cannot detect OS"
    exit 1
fi

echo "✅ Detected OS: $OS"
echo ""

# Install Mosquitto
echo "📦 Installing Mosquitto MQTT Broker..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    apt-get update
    apt-get install -y mosquitto mosquitto-clients
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    yum install -y mosquitto mosquitto-clients
else
    echo "⚠️  Unsupported OS. Please install Mosquitto manually."
    exit 1
fi

# Stop mosquitto to configure it
echo "⏸️  Stopping Mosquitto service..."
systemctl stop mosquitto || true

# Install mosquitto-go-auth
echo ""
echo "📦 Installing mosquitto-go-auth plugin..."
echo "ℹ️  Checking for pre-built binary..."

ARCH=$(uname -m)
GO_AUTH_URL=""

# Try to download pre-built binary
if [ "$ARCH" = "x86_64" ]; then
    GO_AUTH_URL="https://github.com/iegomez/mosquitto-go-auth/releases/latest/download/mosquitto-go-auth-linux-amd64.so"
elif [ "$ARCH" = "aarch64" ]; then
    GO_AUTH_URL="https://github.com/iegomez/mosquitto-go-auth/releases/latest/download/mosquitto-go-auth-linux-arm64.so"
elif [ "$ARCH" = "armv7l" ]; then
    GO_AUTH_URL="https://github.com/iegomez/mosquitto-go-auth/releases/latest/download/mosquitto-go-auth-linux-arm.so"
fi

if [ -n "$GO_AUTH_URL" ]; then
    echo "⬇️  Downloading mosquitto-go-auth from $GO_AUTH_URL"
    wget -q "$GO_AUTH_URL" -O /usr/lib/mosquitto-go-auth.so || {
        echo "⚠️  Failed to download pre-built binary"
        echo "ℹ️  You may need to build from source:"
        echo "   https://github.com/iegomez/mosquitto-go-auth"
    }
    
    if [ -f /usr/lib/mosquitto-go-auth.so ]; then
        chmod +x /usr/lib/mosquitto-go-auth.so
        echo "✅ mosquitto-go-auth installed successfully"
    fi
else
    echo "⚠️  Unsupported architecture: $ARCH"
    echo "ℹ️  Please build mosquitto-go-auth from source:"
    echo "   https://github.com/iegomez/mosquitto-go-auth"
fi

# Backup existing config
if [ -f /etc/mosquitto/mosquitto.conf ]; then
    echo ""
    echo "💾 Backing up existing configuration..."
    cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ Backup created"
fi

# Copy our config file
echo ""
echo "📝 Installing mosquitto configuration..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/mosquitto.conf" ]; then
    cp "$SCRIPT_DIR/mosquitto.conf" /etc/mosquitto/mosquitto.conf
    echo "✅ Configuration installed"
else
    echo "⚠️  mosquitto.conf not found in current directory"
    echo "ℹ️  Please copy mosquitto.conf manually to /etc/mosquitto/mosquitto.conf"
fi

# Create required directories
echo ""
echo "📁 Creating required directories..."
mkdir -p /var/lib/mosquitto
mkdir -p /var/log/mosquitto
chown -R mosquitto:mosquitto /var/lib/mosquitto
chown -R mosquitto:mosquitto /var/log/mosquitto
echo "✅ Directories created"

# Prompt for backend configuration
echo ""
echo "⚙️  Backend Configuration"
echo "=========================================="
echo "ℹ️  The backend should be running on the SAME server"
echo "ℹ️  Gunicorn listens on 127.0.0.1:5000 for MQTT auth"
echo ""
read -p "Enter backend host (default: http://127.0.0.1): " BACKEND_HOST
BACKEND_HOST=${BACKEND_HOST:-http://127.0.0.1}

read -p "Enter backend port (default: 5000): " BACKEND_PORT
BACKEND_PORT=${BACKEND_PORT:-5000}

# Update configuration
echo ""
echo "📝 Updating configuration with backend settings..."
sed -i "s|auth_opt_http_host .*|auth_opt_http_host $BACKEND_HOST|" /etc/mosquitto/mosquitto.conf
sed -i "s|auth_opt_http_port .*|auth_opt_http_port $BACKEND_PORT|" /etc/mosquitto/mosquitto.conf
echo "✅ Configuration updated"

# Enable and start mosquitto
echo ""
echo "🚀 Starting Mosquitto service..."
systemctl enable mosquitto
systemctl start mosquitto

# Check status
sleep 2
if systemctl is-active --quiet mosquitto; then
    echo "✅ Mosquitto is running successfully!"
else
    echo "❌ Mosquitto failed to start. Check logs:"
    echo "   journalctl -u mosquitto -n 50"
    exit 1
fi

# Display summary
echo ""
echo "=========================================="
echo "✅ Installation Complete!"
echo "=========================================="
echo ""
echo "Configuration Details:"
echo "  • Config file: /etc/mosquitto/mosquitto.conf"
echo "  • Backend: $BACKEND_HOST:$BACKEND_PORT"
echo "  • Anonymous access: ENABLED (for testing)"
echo "  • Log: /var/log/mosquitto/mosquitto.log"
echo ""
echo "⚠️  IMPORTANT: For production deployment:"
echo "  1. Edit /etc/mosquitto/mosquitto.conf"
echo "  2. Set allow_anonymous to false"
echo "  3. Enable TLS/SSL encryption"
echo "  4. Restart: sudo systemctl restart mosquitto"
echo ""
echo "📋 Useful Commands:"
echo "  • Check status: sudo systemctl status mosquitto"
echo "  • View logs: sudo journalctl -u mosquitto -f"
echo "  • Restart: sudo systemctl restart mosquitto"
echo "  • Test: mosquitto_pub -h localhost -t test/topic -m 'Hello'"
echo ""
echo "=========================================="
