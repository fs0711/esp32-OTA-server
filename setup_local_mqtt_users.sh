#!/bin/bash

# Setup Script for Local MQTT Users
# Creates password file and ACL configuration for local server clients

set -e  # Exit on error

echo "=========================================="
echo "Local MQTT Users Setup"
echo "ESP32 OTA Backend"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Check if mosquitto is installed
if ! command -v mosquitto_passwd &> /dev/null; then
    echo "❌ mosquitto_passwd not found. Please install mosquitto first."
    exit 1
fi

# Create auth directory
AUTH_DIR="/etc/mosquitto/auth"
PASSWORD_FILE="$AUTH_DIR/passwords"
ACL_FILE="$AUTH_DIR/acl"

echo "📁 Creating authentication directory..."
mkdir -p "$AUTH_DIR"
chmod 755 "$AUTH_DIR"
echo "✅ Directory created: $AUTH_DIR"
echo ""

# Create/update password file
echo "=========================================="
echo "Creating Local Admin User"
echo "=========================================="
echo ""
echo "This user will have FULL access to all MQTT topics."
echo "Use this for local server monitoring, admin scripts, etc."
echo ""

read -p "Enter username for local admin (default: admin): " USERNAME
USERNAME=${USERNAME:-admin}

echo ""
echo "Creating user: $USERNAME"
echo ""

# Use mosquitto_passwd to create user
if [ -f "$PASSWORD_FILE" ]; then
    echo "Password file exists. Adding/updating user..."
    mosquitto_passwd -b "$PASSWORD_FILE" "$USERNAME" || {
        echo "Creating password interactively..."
        mosquitto_passwd "$PASSWORD_FILE" "$USERNAME"
    }
else
    echo "Creating new password file..."
    echo "Enter password for $USERNAME:"
    mosquitto_passwd -c "$PASSWORD_FILE" "$USERNAME"
fi

if [ $? -eq 0 ]; then
    echo "✅ User '$USERNAME' created successfully"
else
    echo "❌ Failed to create user"
    exit 1
fi

echo ""
echo "=========================================="
echo "Additional Users (Optional)"
echo "=========================================="
echo ""

while true; do
    read -p "Add another user? (y/n): " ADD_MORE
    case $ADD_MORE in
        [Yy]* )
            read -p "Enter username: " EXTRA_USER
            if [ -n "$EXTRA_USER" ]; then
                echo "Enter password for $EXTRA_USER:"
                mosquitto_passwd "$PASSWORD_FILE" "$EXTRA_USER"
                if [ $? -eq 0 ]; then
                    echo "✅ User '$EXTRA_USER' created"
                else
                    echo "❌ Failed to create user"
                fi
            fi
            ;;
        [Nn]* ) break;;
        * ) echo "Please answer y or n.";;
    esac
done

# Set correct permissions
chmod 640 "$PASSWORD_FILE"
chown mosquitto:mosquitto "$PASSWORD_FILE"
echo ""
echo "✅ Password file permissions set"

# Copy ACL file
echo ""
echo "📝 Installing ACL configuration..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -f "$SCRIPT_DIR/mosquitto_acl.conf" ]; then
    cp "$SCRIPT_DIR/mosquitto_acl.conf" "$ACL_FILE"
    
    # Add created users to ACL if not already there
    if ! grep -q "user $USERNAME" "$ACL_FILE"; then
        echo "" >> "$ACL_FILE"
        echo "# Added by setup script" >> "$ACL_FILE"
        echo "user $USERNAME" >> "$ACL_FILE"
        echo "topic readwrite #" >> "$ACL_FILE"
    fi
    
    chmod 644 "$ACL_FILE"
    chown mosquitto:mosquitto "$ACL_FILE"
    echo "✅ ACL file installed: $ACL_FILE"
else
    echo "⚠️  mosquitto_acl.conf not found. Creating basic ACL..."
    cat > "$ACL_FILE" << EOF
# Mosquitto ACL - Auto-generated
# User: $USERNAME has full access
user $USERNAME
topic readwrite #
EOF
    chmod 644 "$ACL_FILE"
    chown mosquitto:mosquitto "$ACL_FILE"
    echo "✅ Basic ACL created"
fi

# Display user list
echo ""
echo "=========================================="
echo "Created Users"
echo "=========================================="
echo ""
if [ -f "$PASSWORD_FILE" ]; then
    echo "Users in $PASSWORD_FILE:"
    cut -d: -f1 "$PASSWORD_FILE" | while read user; do
        echo "  • $user"
    done
else
    echo "No users found"
fi

# Test configuration
echo ""
echo "=========================================="
echo "Testing Configuration"
echo "=========================================="
echo ""

# Check if mosquitto.conf has files backend enabled
if grep -q "auth_opt_backends.*files" /etc/mosquitto/mosquitto.conf; then
    echo "✅ Files backend enabled in mosquitto.conf"
else
    echo "⚠️  WARNING: Files backend not found in mosquitto.conf"
    echo "   Add this to /etc/mosquitto/mosquitto.conf:"
    echo "   auth_opt_backends files, http"
    echo "   auth_opt_password_path $PASSWORD_FILE"
    echo "   auth_opt_acl_path $ACL_FILE"
fi

# Restart mosquitto
echo ""
read -p "Restart Mosquitto now? (y/n): " RESTART
case $RESTART in
    [Yy]* )
        echo "Restarting Mosquitto..."
        systemctl restart mosquitto
        sleep 2
        if systemctl is-active --quiet mosquitto; then
            echo "✅ Mosquitto restarted successfully"
        else
            echo "❌ Mosquitto failed to start"
            echo "Check logs: journalctl -u mosquitto -n 50"
            exit 1
        fi
        ;;
    * )
        echo "⚠️  Remember to restart Mosquitto:"
        echo "   sudo systemctl restart mosquitto"
        ;;
esac

# Display connection info
echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Local MQTT User Configuration:"
echo "  • Username: $USERNAME"
echo "  • Password: (the one you entered)"
echo "  • Access: Full (all topics)"
echo "  • Files: "
echo "      - Passwords: $PASSWORD_FILE"
echo "      - ACL: $ACL_FILE"
echo ""
echo "Connection Examples:"
echo ""
echo "1. Publish to any topic:"
echo "   mosquitto_pub -h localhost -u \"$USERNAME\" -P \"yourpassword\" \\"
echo "     -t \"system/test\" -m \"Hello from server\""
echo ""
echo "2. Subscribe to all topics:"
echo "   mosquitto_sub -h localhost -u \"$USERNAME\" -P \"yourpassword\" \\"
echo "     -t \"#\" -v"
echo ""
echo "3. Subscribe to device topics:"
echo "   mosquitto_sub -h localhost -u \"$USERNAME\" -P \"yourpassword\" \\"
echo "     -t \"devices/#\" -v"
echo ""
echo "4. Using in Python:"
echo "   import paho.mqtt.client as mqtt"
echo "   client = mqtt.Client()"
echo "   client.username_pw_set(\"$USERNAME\", \"yourpassword\")"
echo "   client.connect(\"localhost\", 1883, 60)"
echo ""
echo "User Management Commands:"
echo "  • Add user: sudo mosquitto_passwd $PASSWORD_FILE username"
echo "  • Delete user: sudo mosquitto_passwd -D $PASSWORD_FILE username"
echo "  • Change password: sudo mosquitto_passwd $PASSWORD_FILE username"
echo "  • List users: cut -d: -f1 $PASSWORD_FILE"
echo ""
echo "=========================================="
