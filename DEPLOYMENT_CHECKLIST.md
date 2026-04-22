# ESP32 OTA Backend - Deployment Checklist
## Dual-Binding Setup for Nginx + MQTT Authentication

## 📋 Pre-Deployment Checklist

### 1. Update Configuration Files
- [x] **gunicorn.conf.py** - Added dual-binding configuration
  ```python
  bind = [
      "unix:esp32ota.sock",      # Nginx reverse proxy
      "127.0.0.1:5000"            # MQTT auth plugin
  ]
  ```

- [x] **mosquitto.conf** - Updated backend connection
  ```conf
  auth_opt_http_host http://127.0.0.1
  auth_opt_http_port 5000
  ```

- [ ] **Nginx config (esp32-ota)** - No changes needed (continues using Unix socket)

### 2. Deploy Configuration Files
```bash
# Backup existing configs
sudo cp /etc/nginx/sites-available/esp32-ota /etc/nginx/sites-available/esp32-ota.backup
sudo cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.backup
cp /home/esp32ota-backend/gunicorn.conf.py /home/esp32ota-backend/gunicorn.conf.py.backup

# Deploy new configs
sudo cp mosquitto.conf /etc/mosquitto/mosquitto.conf
# Update gunicorn.conf.py on server (already in place)
```

### 3. Configure Firewall
```bash
# Using UFW (Ubuntu/Debian)
sudo ufw allow 'Nginx Full'
sudo ufw allow 1883/tcp   # MQTT
sudo ufw deny 5000/tcp    # Block external access to backend port
sudo ufw enable

# Verify
sudo ufw status
```

### 4. Restart Services
```bash
# Restart in order
sudo systemctl restart esp32-ota     # Backend (gunicorn)
sudo systemctl restart nginx          # Web proxy
sudo systemctl restart mosquitto      # MQTT broker

# Check status
sudo systemctl status esp32-ota
sudo systemctl status nginx
sudo systemctl status mosquitto
```

### 5. Verify Deployment
```bash
# Run verification script
chmod +x verify_deployment.sh
sudo ./verify_deployment.sh

# Manual tests
# Test 1: Check gunicorn is listening on both interfaces
sudo netstat -tulpn | grep gunicorn
# Expected output should show:
#   - unix esp32ota.sock
#   - 127.0.0.1:5000

# Test 2: Test Unix socket (nginx path)
sudo curl --unix-socket /home/esp32ota-backend/esp32ota.sock \
    http://localhost/api/static-data

# Test 3: Test localhost HTTP (MQTT auth path)
curl http://127.0.0.1:5000/api/static-data

# Test 4: Verify external access is blocked (should FAIL)
# From another machine:
curl http://your-server-ip:5000/api/static-data
# Expected: Connection refused or timeout
```

### 6. Test MQTT Authentication
```bash
# Generate HMAC password
python generate_mqtt_password.py DV-001 <device-access-token>

# Run comprehensive test
python test_mqtt_auth.py --device-id DV-001 --access-token <token>

# Test with mosquitto client
mosquitto_pub -h localhost -u "DV-001" -P "<hmac-password>" \
    -t "devices/DV-001/test" -m "Hello MQTT"
```

### 7. Monitor Logs
```bash
# Watch all logs simultaneously
# Terminal 1
journalctl -u esp32-ota -f

# Terminal 2
journalctl -u nginx -f

# Terminal 3
journalctl -u mosquitto -f

# Or check recent errors
sudo tail -f /var/log/esp32ota/error.log
sudo tail -f /var/log/nginx/ota.error.log
```

## 🔒 Security Verification

### Critical Security Checks
- [ ] Port 5000 is NOT accessible from external network
  ```bash
  # From external machine (should FAIL)
  curl http://your-server-ip:5000
  ```

- [ ] Firewall is configured and active
  ```bash
  sudo ufw status
  # Should show: Status: active
  # Should show: 5000 DENY or not listed
  ```

- [ ] Mosquitto is on the same server as backend
  ```bash
  # Both should show same hostname
  hostname
  ```

- [ ] TLS/SSL is enabled on nginx
  ```bash
  curl -I https://ota.zvolta.com/api/static-data
  # Should return 200 OK with HTTPS
  ```

- [ ] Anonymous MQTT access is disabled (production only)
  ```bash
  grep "allow_anonymous" /etc/mosquitto/mosquitto.conf
  # For production: should be "false"
  # For testing: can be "true"
  ```

## 🧪 Testing Checklist

### Web Application (via Nginx)
- [ ] HTTPS access works: `https://ota.zvolta.com`
- [ ] API endpoints respond: `https://ota.zvolta.com/api/static-data`
- [ ] File uploads work (test with firmware upload)
- [ ] Authentication works (login/logout)
- [ ] All frontend features functional

### MQTT Authentication
- [ ] Device authentication succeeds with valid HMAC
- [ ] Device authentication fails with invalid HMAC
- [ ] Superuser endpoint responds correctly
- [ ] ACL allows access to device-specific topics
- [ ] ACL denies access to other device topics
- [ ] Anonymous connections work (if enabled for testing)

### Performance
- [ ] Check response times are acceptable
  ```bash
  time curl http://127.0.0.1:5000/api/static-data
  ```

- [ ] Check worker count matches CPU cores
  ```bash
  # In gunicorn.conf.py: workers = (2 x cores) + 1
  nproc  # Show number of CPU cores
  ```

- [ ] Monitor resource usage under load
  ```bash
  htop  # or top
  ```

## 🚨 Troubleshooting Guide

### Gunicorn won't start
```bash
# Check for port conflicts
sudo netstat -tulpn | grep 5000

# Check for socket permission issues
ls -la /home/esp32ota-backend/esp32ota.sock

# Check error logs
sudo tail -n 50 /var/log/esp32ota/error.log

# Test config syntax
gunicorn --check-config -c gunicorn.conf.py wsgi:app
```

### MQTT Authentication fails
```bash
# Test backend is accessible from localhost
curl -X POST http://127.0.0.1:5000/api/mqtt/auth \
    -d "username=test&password=test"

# Check mosquitto logs
journalctl -u mosquitto -n 100

# Test with debug logging
# Edit /etc/mosquitto/mosquitto.conf
# Set: auth_opt_log_level debug
# Restart: sudo systemctl restart mosquitto
```

### Nginx returns 502 Bad Gateway
```bash
# Check Unix socket exists and has correct permissions
ls -la /home/esp32ota-backend/esp32ota.sock

# Check nginx can read socket
sudo -u www-data test -r /home/esp32ota-backend/esp32ota.sock && echo "OK"

# Check gunicorn is running
sudo systemctl status esp32-ota

# Check nginx error log
sudo tail -f /var/log/nginx/ota.error.log
```

### Port 5000 is exposed externally
```bash
# Add firewall rule immediately
sudo ufw deny 5000/tcp
sudo ufw reload

# Verify
sudo ufw status | grep 5000

# Test from external machine (should fail)
curl http://your-server-ip:5000
```

## 📚 Documentation References

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment architecture
- [MQTT_AUTH_README.md](MQTT_AUTH_README.md) - MQTT authentication details
- [MQTT_QUICK_REFERENCE.md](MQTT_QUICK_REFERENCE.md) - Quick command reference

## ✅ Production Readiness Checklist

Before going live:
- [ ] `allow_anonymous false` in mosquitto.conf
- [ ] Firewall blocking port 5000 externally
- [ ] TLS/SSL enabled on nginx (HTTPS)
- [ ] TLS/SSL enabled on mosquitto (port 8883)
- [ ] Rate limiting configured on nginx
- [ ] Log rotation configured
- [ ] Monitoring/alerting set up
- [ ] Backup strategy in place
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Team trained on new deployment

## 📞 Support

If issues persist:
1. Review all logs in chronological order
2. Run `verify_deployment.sh` script
3. Check firewall rules and port bindings
4. Verify all services are running
5. Test each component independently
6. Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting

---

**Last Updated:** Configuration updated for dual-binding support
**Version:** 2.0 with MQTT authentication
