#!/bin/bash
# Setup MQTT Admin User for Mosquitto
# Creates password file and ACL for admin user with full access

set -e

# Configuration
AUTH_DIR="/etc/mosquitto/auth"
PASSWORD_FILE="${AUTH_DIR}/passwords"
ACL_FILE="${AUTH_DIR}/acl"
ADMIN_USERNAME="admin"

echo "========================================="
echo "MQTT Admin User Setup"
echo "========================================="
echo ""

# Create auth directory if it doesn't exist
if [ ! -d "$AUTH_DIR" ]; then
    echo "Creating auth directory: $AUTH_DIR"
    sudo mkdir -p "$AUTH_DIR"
fi

# Generate admin user password
echo "Creating admin user: $ADMIN_USERNAME"
echo "You will be prompted to enter a password..."
echo ""

# Create password file (mosquitto_passwd will prompt for password)
sudo mosquitto_passwd -c "$PASSWORD_FILE" "$ADMIN_USERNAME"

# Set proper permissions on password file
sudo chmod 600 "$PASSWORD_FILE"
sudo chown mosquitto:mosquitto "$PASSWORD_FILE" 2>/dev/null || true

echo ""
echo "========================================="
echo "Creating ACL file with full access..."
echo "========================================="

# Create ACL file giving admin full access to all topics
sudo bash -c "cat > $ACL_FILE" <<EOF
# MQTT Access Control List
# Admin user has full access to all topics

user $ADMIN_USERNAME
topic readwrite #
EOF

# Set proper permissions on ACL file
sudo chmod 644 "$ACL_FILE"
sudo chown mosquitto:mosquitto "$ACL_FILE" 2>/dev/null || true

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Admin user created: $ADMIN_USERNAME"
echo "Password file: $PASSWORD_FILE"
echo "ACL file: $ACL_FILE"
echo ""
echo "Test connection:"
echo "  mosquitto_pub -h localhost -u \"$ADMIN_USERNAME\" -P \"<your-password>\" -t \"test/admin\" -m \"Hello\""
echo ""
echo "Restart Mosquitto to apply changes:"
echo "  sudo systemctl restart mosquitto"
echo ""
