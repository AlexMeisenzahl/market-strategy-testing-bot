# Deployment Guide

Guide for deploying the Market Strategy Testing Bot to production.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8 or higher
- Root or sudo access
- Domain name (optional, for HTTPS)
- At least 1GB RAM, 10GB disk space

---

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt install git nginx supervisor -y

# Install optional dependencies
sudo apt install certbot python3-certbot-nginx -y  # For SSL
```

### 3. Create Application User

```bash
# Create dedicated user (more secure)
sudo useradd -m -s /bin/bash tradingbot
sudo su - tradingbot
```

---

## Application Setup

### 1. Clone Repository

```bash
cd /home/tradingbot
git clone https://github.com/your-username/market-strategy-testing-bot.git
cd market-strategy-testing-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Application

```bash
# Copy example config
cp config.example.yaml config.yaml

# Edit configuration
nano config.yaml
```

**Important production settings:**
```yaml
paper_trading: true  # Keep true unless you know what you're doing

logging:
  level: INFO
  file: /var/log/tradingbot/bot.log

api_timeout_seconds: 10
max_trades_per_hour: 5
```

### 5. Validate Configuration

```bash
python -m utils.config_validator config.yaml
```

### 6. Initialize Database

```bash
# Run migrations
python -c "from database.settings_models import init_db; init_db()"
```

---

## Running with Gunicorn

### 1. Test Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 dashboard.app:app
```

### 2. Create Systemd Service

Create `/etc/systemd/system/tradingbot-dashboard.service`:

```ini
[Unit]
Description=Trading Bot Dashboard
After=network.target

[Service]
Type=notify
User=tradingbot
Group=tradingbot
WorkingDirectory=/home/tradingbot/market-strategy-testing-bot
Environment="PATH=/home/tradingbot/market-strategy-testing-bot/venv/bin"
ExecStart=/home/tradingbot/market-strategy-testing-bot/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --access-logfile /var/log/tradingbot/access.log \
    --error-logfile /var/log/tradingbot/error.log \
    --log-level info \
    dashboard.app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Create Log Directory

```bash
sudo mkdir -p /var/log/tradingbot
sudo chown tradingbot:tradingbot /var/log/tradingbot
```

### 4. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable tradingbot-dashboard
sudo systemctl start tradingbot-dashboard
sudo systemctl status tradingbot-dashboard
```

---

## Nginx Configuration

### 1. Create Nginx Config

Create `/etc/nginx/sites-available/tradingbot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/tradingbot-access.log;
    error_log /var/log/nginx/tradingbot-error.log;

    # Main application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static {
        alias /home/tradingbot/market-strategy-testing-bot/dashboard/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no auth)
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        access_log off;
    }
}
```

### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/tradingbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL Certificate (HTTPS)

### Using Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
```

Follow the prompts. Certbot will:
- Verify domain ownership
- Generate SSL certificate
- Update Nginx configuration
- Set up automatic renewal

### Verify Auto-Renewal

```bash
sudo certbot renew --dry-run
```

---

## Firewall Configuration

### UFW (Uncomplicated Firewall)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

---

## Monitoring

### 1. Application Logs

```bash
# View dashboard logs
sudo journalctl -u tradingbot-dashboard -f

# View application logs
tail -f /var/log/tradingbot/bot.log
```

### 2. System Resources

```bash
# Check CPU and memory
htop

# Check disk space
df -h

# Check processes
ps aux | grep tradingbot
```

### 3. Health Check

```bash
curl http://localhost:5000/health
curl https://your-domain.com/api/health
```

### 4. Set Up Monitoring (Optional)

**Using systemd-cron:**
```bash
# Create monitoring script
cat > /home/tradingbot/monitor.sh << 'EOF'
#!/bin/bash
STATUS=$(curl -s http://localhost:5000/health | grep -o '"status":"[^"]*' | cut -d'"' -f4)
if [ "$STATUS" != "healthy" ]; then
    echo "Dashboard is unhealthy!" | mail -s "Trading Bot Alert" admin@example.com
fi
EOF

chmod +x /home/tradingbot/monitor.sh

# Add to crontab
crontab -e
```

Add:
```
*/5 * * * * /home/tradingbot/monitor.sh
```

---

## Backup Strategy

### 1. Database Backup

```bash
# Create backup script
cat > /home/tradingbot/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/tradingbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /home/tradingbot/market-strategy-testing-bot/data/settings.db \
   $BACKUP_DIR/settings_$DATE.db

# Backup config
cp /home/tradingbot/market-strategy-testing-bot/config.yaml \
   $BACKUP_DIR/config_$DATE.yaml

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /home/tradingbot/backup.sh
```

### 2. Schedule Backups

```bash
crontab -e
```

Add:
```
0 2 * * * /home/tradingbot/backup.sh
```

### 3. Remote Backup (Optional)

```bash
# Sync to remote server
rsync -avz /home/tradingbot/backups/ user@backup-server:/backups/tradingbot/
```

---

## Performance Optimization

### 1. Gunicorn Workers

Calculate optimal workers:
```python
workers = (2 * CPU_CORES) + 1
```

For 2 CPU cores: 5 workers
For 4 CPU cores: 9 workers

### 2. Database Optimization

```bash
# Regular database maintenance
sqlite3 /home/tradingbot/market-strategy-testing-bot/data/settings.db "VACUUM;"
```

### 3. Log Rotation

Create `/etc/logrotate.d/tradingbot`:

```
/var/log/tradingbot/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 tradingbot tradingbot
    sharedscripts
    postrotate
        systemctl reload tradingbot-dashboard
    endscript
}
```

---

## Security Best Practices

1. **Never expose database directly**
2. **Use strong passwords for all services**
3. **Keep system and dependencies updated**
4. **Enable firewall (UFW)**
5. **Use HTTPS (SSL/TLS)**
6. **Limit SSH access**
7. **Regular security audits**
8. **Monitor logs for suspicious activity**
9. **Keep paper_trading: true**
10. **Never commit secrets to git**

### SSH Hardening

Edit `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
Port 2222  # Change default port
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

---

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status tradingbot-dashboard

# Check logs
sudo journalctl -u tradingbot-dashboard -n 50

# Check configuration
nginx -t
```

### Database errors

```bash
# Backup and recreate database
cp data/settings.db data/settings.db.backup
python -c "from database.settings_models import init_db; init_db()"
```

### High memory usage

```bash
# Reduce Gunicorn workers
# Edit /etc/systemd/system/tradingbot-dashboard.service
# Change --workers to a lower number
sudo systemctl daemon-reload
sudo systemctl restart tradingbot-dashboard
```

### Slow performance

```bash
# Check database size
du -h data/settings.db

# Vacuum database
sqlite3 data/settings.db "VACUUM;"

# Clear old logs
find logs/ -type f -mtime +7 -delete
```

---

## Upgrading

### 1. Backup

```bash
/home/tradingbot/backup.sh
```

### 2. Update Code

```bash
cd /home/tradingbot/market-strategy-testing-bot
git pull origin main
```

### 3. Update Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### 4. Run Migrations

```bash
# If using Alembic
alembic upgrade head
```

### 5. Restart Services

```bash
sudo systemctl restart tradingbot-dashboard
```

### 6. Verify

```bash
curl http://localhost:5000/health
```

---

## Production Checklist

Before going live:

- [ ] Server hardened (firewall, SSH, etc.)
- [ ] SSL certificate installed
- [ ] Database backed up
- [ ] Config validated
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Logs rotating properly
- [ ] Services starting on boot
- [ ] Backup strategy in place
- [ ] Documentation reviewed
- [ ] Emergency contacts listed
- [ ] Rollback plan prepared

---

## Support

For deployment issues:
1. Check service logs
2. Review this guide
3. Verify all prerequisites
4. Test health endpoints
5. Check firewall rules
6. Review Nginx configuration
