# Deployment Configuration Guide
# ESP32 OTA Backend - Gunicorn + Nginx + Mosquitto

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Traffic                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     Nginx    │  (Port 80/443)
                    │ ota.zvolta.com│
                    └──────┬───────┘
                           │ Unix Socket
                           │ esp32ota.sock
                           ▼
        ┌──────────────────────────────────┐
        │         Gunicorn Workers         │
        │      (Dual Binding Mode)         │
        ├──────────────────────────────────┤
        │  1. unix:esp32ota.sock           │ ← Nginx
        │  2. 127.0.0.1:5000               │ ← MQTT Auth
        └────────────┬─────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
   ┌──────────┐          ┌─────────────┐
   │  Nginx   │          │  Mosquitto  │
   │  Proxy   │          │  go-auth    │
   └──────────┘          └─────────────┘
   Via Unix Socket       Via HTTP
   (Efficient)           (localhost:5000)
```

## Gunicorn Configuration

### Dual Binding Setup
The backend binds to TWO interfaces:

1. **Unix Socket** (`unix:esp32ota.sock`)
   - Used by: Nginx reverse proxy
   - Purpose: Web application traffic
   - Security: File permissions-based access control
   - Performance: Low overhead, no TCP stack

2. **Localhost HTTP** (`127.0.0.1:5000`)
   - Used by: Mosquitto-go-auth plugin
   - Purpose: MQTT authentication requests
   - Security: Localhost only (not exposed externally)
   - Performance: Standard HTTP over loopback

### Configuration File
```python
# gunicorn.conf.py
bind = [
    "unix:esp32ota.sock",      # Nginx reverse proxy
    "127.0.0.1:5000"            # MQTT auth plugin
]
```

## Security Considerations

### ✅ Secure Setup
- `127.0.0.1:5000` is bound to localhost ONLY
- Not accessible from external network
- Firewall should block port 5000 from external access
- Nginx handles SSL/TLS termination
- Mosquitto-go-auth connects via localhost (same server)

### ⚠️ Important Security Rules

1. **Never bind to `0.0.0.0:5000`** - This would expose the backend directly
2. **Firewall Configuration** - Ensure port 5000 is blocked externally
3. **Same Server Deployment** - Mosquitto must run on the same server as the backend
4. **SSL for Public Access** - Always use HTTPS through nginx for web traffic

## Firewall Configuration

### UFW (Ubuntu/Debian)
```bash
# Allow nginx (HTTP/HTTPS)
sudo ufw allow 'Nginx Full'

# Allow MQTT
sudo ufw allow 1883/tcp   # MQTT
sudo ufw allow 8883/tcp   # MQTT over TLS (optional)

# Block direct access to backend port (should be default, but verify)
sudo ufw deny 5000/tcp

# Enable firewall
sudo ufw enable
```

### iptables
```bash
# Allow nginx
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow MQTT
iptables -A INPUT -p tcp --dport 1883 -j ACCEPT
iptables -A INPUT -p tcp --dport 8883 -j ACCEPT

# Block external access to port 5000 (allow only localhost)
iptables -A INPUT -p tcp --dport 5000 ! -s 127.0.0.1 -j DROP
```

### Firewalld (CentOS/RHEL)
```bash
# Allow services
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-port=1883/tcp
firewall-cmd --permanent --add-port=8883/tcp

# Reload
firewall-cmd --reload
```

## Nginx Configuration

### Current Setup (esp32-ota)
```nginx
location / {
    include proxy_params;
    proxy_pass http://unix:/home/esp32ota-backend/esp32ota.sock;
    # ... other settings
}
```

This configuration remains unchanged. Nginx continues to use the Unix socket.

## Mosquitto Configuration

### Backend Connection (mosquitto.conf)
```conf
# Connect to backend via localhost HTTP
auth_opt_http_host http://127.0.0.1
auth_opt_http_port 5000
auth_opt_http_getuser_uri /api/mqtt/auth
auth_opt_http_superuser_uri /api/mqtt/superuser
auth_opt_http_aclcheck_uri /api/mqtt/acl
```

## Deployment Checklist

### Initial Setup
- [ ] Update `gunicorn.conf.py` with dual binding
- [ ] Update `mosquitto.conf` with backend connection
- [ ] Restart gunicorn: `sudo systemctl restart esp32-ota`
- [ ] Restart mosquitto: `sudo systemctl restart mosquitto`
- [ ] Configure firewall (block port 5000 externally)

### Verification
- [ ] Check gunicorn is listening on both interfaces:
  ```bash
  sudo netstat -tulpn | grep gunicorn
  # Should show: unix:esp32ota.sock AND 127.0.0.1:5000
  ```

- [ ] Verify nginx connection (should work as before):
  ```bash
  curl -I https://ota.zvolta.com/api/static-data
  ```

- [ ] Test MQTT authentication:
  ```bash
  python test_mqtt_auth.py --device-id DV-001 --access-token <token>
  ```

- [ ] Verify port 5000 is NOT accessible externally:
  ```bash
  # From another server/machine (should fail):
  curl http://your-server-ip:5000/api/static-data
  ```

- [ ] Verify port 5000 IS accessible locally:
  ```bash
  # On the server itself (should work):
  curl http://127.0.0.1:5000/api/static-data
  ```

### Monitoring
- [ ] Check gunicorn logs: `/var/log/esp32ota/access.log`
- [ ] Check nginx logs: `/var/log/nginx/ota.access.log`
- [ ] Check mosquitto logs: `journalctl -u mosquitto -f`

## Service Restart Commands

```bash
# Restart all services
sudo systemctl restart esp32-ota
sudo systemctl restart nginx
sudo systemctl restart mosquitto

# Check status
sudo systemctl status esp32-ota
sudo systemctl status nginx
sudo systemctl status mosquitto

# View logs
journalctl -u esp32-ota -f
journalctl -u nginx -f
journalctl -u mosquitto -f
```

## Troubleshooting

### Gunicorn won't start
```bash
# Check for port conflicts
sudo netstat -tulpn | grep 5000

# Check socket file permissions
ls -la /home/esp32ota-backend/esp32ota.sock

# Check gunicorn error log
tail -f /var/log/esp32ota/error.log
```

### MQTT Auth fails
```bash
# Test backend directly from localhost
curl -X POST http://127.0.0.1:5000/api/mqtt/auth \
  -d "username=DV-001&password=test"

# Check if gunicorn is listening on localhost:5000
sudo netstat -tulpn | grep 5000

# Check mosquitto logs for connection errors
journalctl -u mosquitto -n 100
```

### Nginx connection issues
```bash
# Test Unix socket connection
sudo curl --unix-socket /home/esp32ota-backend/esp32ota.sock \
  http://localhost/api/static-data

# Check socket permissions
ls -la /home/esp32ota-backend/esp32ota.sock

# Verify nginx user can access socket
sudo -u www-data test -r /home/esp32ota-backend/esp32ota.sock && echo "OK"
```

## Performance Tuning

### Gunicorn Workers
Current: 10 workers
```python
# Recommended formula: (2 x CPU cores) + 1
# For 4 cores: workers = 9
# For 8 cores: workers = 17
```

### Connection Limits
Adjust based on load:
```python
# gunicorn.conf.py
worker_class = 'sync'  # or 'gevent' for async
worker_connections = 1000
timeout = 300
keepalive = 5
```

### Nginx Tuning
```nginx
# Worker connections
events {
    worker_connections 2048;
}

# Timeouts
proxy_connect_timeout 60s;
proxy_send_timeout 3600s;
proxy_read_timeout 3600s;
```

## Security Best Practices

1. **Use environment variables** for sensitive config
2. **Enable rate limiting** on nginx for auth endpoints
3. **Monitor authentication attempts** for suspicious activity
4. **Keep software updated** (gunicorn, nginx, mosquitto)
5. **Use TLS/SSL** for all external connections
6. **Regular security audits** of logs and configurations
7. **Principle of least privilege** for file permissions
8. **Implement fail2ban** for brute force protection

## Backup Configuration

```bash
# Backup configurations
sudo cp /etc/nginx/sites-available/esp32-ota /etc/nginx/sites-available/esp32-ota.backup
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup
cp /home/esp32ota-backend/gunicorn.conf.py /home/esp32ota-backend/gunicorn.conf.py.backup

# Create backup script
#!/bin/bash
BACKUP_DIR="/var/backups/esp32ota/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"
cp /etc/nginx/sites-available/esp32-ota "$BACKUP_DIR/"
cp /etc/mosquitto/mosquitto.conf "$BACKUP_DIR/"
cp /home/esp32ota-backend/gunicorn.conf.py "$BACKUP_DIR/"
```

## Additional Resources

- Gunicorn Docs: https://docs.gunicorn.org/
- Nginx Docs: https://nginx.org/en/docs/
- Mosquitto Docs: https://mosquitto.org/documentation/
- mosquitto-go-auth: https://github.com/iegomez/mosquitto-go-auth
