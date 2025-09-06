# 🚀 TrackGuard AI - Production Deployment Guide

This guide covers deploying TrackGuard AI to production environments.

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB minimum, 100GB recommended
- **CPU**: 2+ cores, GPU optional for AI processing
- **Network**: HTTPS/SSL capability

### Software Dependencies
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **Domain**: For SSL certificate setup

## 🐳 Docker Deployment (Recommended)

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Application Deployment
```bash
# Clone repository
git clone https://github.com/SaptarshiMondal123/TrackGuard_AI.git
cd TrackGuard_AI

# Setup environment
cp .env.example .env
nano .env  # Edit configuration

# Deploy services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. SSL/HTTPS Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## ⚙️ Manual Deployment

### 1. Database Setup
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Create database and user
sudo -u postgres psql
CREATE DATABASE trackguard_ai;
CREATE USER trackguard WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE trackguard_ai TO trackguard;
\q

# Import schema
psql -U trackguard -d trackguard_ai -f database/schema.sql

# Install Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
```

### 2. Backend Deployment
```bash
# Install Python dependencies
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/trackguard-api.service
```

**Service Configuration:**
```ini
[Unit]
Description=TrackGuard API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=trackguard
WorkingDirectory=/opt/trackguard/Backend
Environment=PATH=/opt/trackguard/Backend/venv/bin
ExecStart=/opt/trackguard/Backend/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trackguard-api
sudo systemctl start trackguard-api
```

### 3. Frontend Deployment
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Build frontend
cd frontend1
npm install
npm run build

# Copy to web server
sudo cp -r dist/* /var/www/html/trackguard/
```

### 4. Nginx Configuration
```bash
# Install Nginx
sudo apt install nginx -y

# Create site configuration
sudo nano /etc/nginx/sites-available/trackguard
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    root /var/www/html/trackguard;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml+rss text/javascript;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/trackguard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Monitoring & Maintenance

### 1. Health Monitoring
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "$(date): API is healthy"
else
    echo "$(date): API is down, restarting..."
    sudo systemctl restart trackguard-api
fi

# Check database connection
if pg_isready -U trackguard -d trackguard_ai > /dev/null 2>&1; then
    echo "$(date): Database is healthy"
else
    echo "$(date): Database connection failed"
fi
EOF

chmod +x monitor.sh

# Add to cron
crontab -e
# Add: */5 * * * * /path/to/monitor.sh >> /var/log/trackguard-monitor.log
```

### 2. Log Management
```bash
# Setup log rotation
sudo nano /etc/logrotate.d/trackguard
```

```
/var/log/trackguard/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 trackguard trackguard
    postrotate
        systemctl reload trackguard-api
    endscript
}
```

### 3. Backup Strategy
```bash
# Database backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/trackguard"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U trackguard -d trackguard_ai | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# File backup
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /opt/trackguard/Backend/uploads/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup.sh >> /var/log/trackguard-backup.log
```

## 🔒 Security Hardening

### 1. Firewall Configuration
```bash
# Setup UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 5432  # PostgreSQL (only local access)
sudo ufw deny 6379  # Redis (only local access)
```

### 2. Database Security
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/13/main/pg_hba.conf
# Ensure only local connections are allowed

sudo systemctl restart postgresql
```

### 3. Application Security
```bash
# Set secure file permissions
sudo chown -R trackguard:trackguard /opt/trackguard
sudo chmod -R 755 /opt/trackguard
sudo chmod 600 /opt/trackguard/.env

# Setup fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## 📈 Performance Optimization

### 1. Database Optimization
```sql
-- Index optimization
ANALYZE;
REINDEX DATABASE trackguard_ai;

-- Connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

### 2. Redis Configuration
```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Optimize settings
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
```

### 3. Application Scaling
```bash
# Multiple API instances
sudo systemctl stop trackguard-api
sudo cp /etc/systemd/system/trackguard-api.service /etc/systemd/system/trackguard-api-2.service

# Edit port in second service
sudo nano /etc/systemd/system/trackguard-api-2.service
# Change port to 8001

# Start both services
sudo systemctl start trackguard-api
sudo systemctl start trackguard-api-2

# Update Nginx upstream
sudo nano /etc/nginx/sites-available/trackguard
# Add upstream block with both servers
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Reset connections
sudo systemctl restart postgresql
```

#### 2. API Service Issues
```bash
# Check service logs
sudo journalctl -u trackguard-api -f

# Check process
ps aux | grep python

# Manual start for debugging
cd /opt/trackguard/Backend
source venv/bin/activate
python main.py
```

#### 3. Frontend Issues
```bash
# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx configuration
sudo nginx -t

# Rebuild frontend
cd /opt/trackguard/frontend1
npm run build
sudo cp -r dist/* /var/www/html/trackguard/
```

### Performance Issues
```bash
# Monitor system resources
htop
iotop
df -h

# Check database performance
sudo -u postgres psql -d trackguard_ai -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

## 📞 Support

For production deployment support:
- **Email**: support@trackguard.ai
- **Documentation**: [docs.trackguard.ai](https://docs.trackguard.ai)
- **Issues**: [GitHub Issues](https://github.com/SaptarshiMondal123/TrackGuard_AI/issues)

---

**TrackGuard AI** - Enterprise Railway Safety System