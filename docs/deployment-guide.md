# Deployment Guide - Python Learning Studio

## Overview

This guide provides step-by-step instructions for deploying Python Learning Studio to production environments.

## Prerequisites

- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Nginx (recommended)
- SSL Certificate
- Domain name

## Production Environment Setup

### 1. Server Preparation

#### System Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB+ (8GB recommended)
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 20.04 LTS or similar

#### Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.12 python3.12-venv python3.12-dev -y
sudo apt install postgresql postgresql-contrib redis-server nginx -y
sudo apt install git curl wget -y

# Install system libraries
sudo apt install libpq-dev libjpeg-dev libpng-dev libfreetype6-dev -y
```

### 2. Database Setup

#### PostgreSQL Configuration
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE learning_community;
CREATE USER learning_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE learning_community TO learning_user;
ALTER USER learning_user CREATEDB;
\q
```

#### Redis Configuration
```bash
# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis connection
redis-cli ping
```

### 3. Application Deployment

#### Clone and Setup Application
```bash
# Create application directory
sudo mkdir -p /opt/learning_studio
sudo chown $USER:$USER /opt/learning_studio
cd /opt/learning_studio

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

#### Environment Configuration
```bash
# Create production environment file
cat > .env << EOF
# Django Settings
SECRET_KEY=your_very_long_and_secure_secret_key_here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgres://learning_user:your_secure_password@localhost:5432/learning_community

# Redis
REDIS_URL=redis://localhost:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# OpenAI API (Optional)
OPENAI_API_KEY=your_openai_api_key_here

# Wagtail Admin URL
WAGTAILADMIN_BASE_URL=https://yourdomain.com
EOF

# Set secure permissions
chmod 600 .env
```

#### Database Migration
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Create cache table
python manage.py createcachetable
```

### 4. Web Server Configuration

#### Gunicorn Configuration
```bash
# Create gunicorn configuration
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
keepalive = 2
timeout = 30
user = "www-data"
group = "www-data"
tmp_upload_dir = None
chdir = "/opt/learning_studio"
pythonpath = "/opt/learning_studio"
raw_env = [
    "DJANGO_SETTINGS_MODULE=learning_community.settings.production",
]
EOF
```

#### Systemd Service
```bash
# Create systemd service file
sudo cat > /etc/systemd/system/learning-studio.service << EOF
[Unit]
Description=Python Learning Studio
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/learning_studio
Environment=PATH=/opt/learning_studio/venv/bin
ExecStart=/opt/learning_studio/venv/bin/gunicorn --config gunicorn.conf.py learning_community.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable learning-studio
sudo systemctl start learning-studio
```

#### Nginx Configuration
```bash
# Create nginx configuration
sudo cat > /etc/nginx/sites-available/learning-studio << EOF
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Static Files
    location /static/ {
        alias /opt/learning_studio/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media Files
    location /media/ {
        alias /opt/learning_studio/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    # Security
    location = /robots.txt {
        allow all;
        log_not_found off;
        access_log off;
    }

    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/learning-studio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL Certificate Setup

#### Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

### 6. Background Tasks (Optional)

#### Celery Configuration
```bash
# Create celery configuration
cat > celery.conf.py << EOF
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True
EOF

# Create celery systemd service
sudo cat > /etc/systemd/system/celery.service << EOF
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/opt/learning_studio
Environment=PATH=/opt/learning_studio/venv/bin
ExecStart=/opt/learning_studio/venv/bin/celery -A learning_community worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start celery (if needed)
sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery
```

## Security Hardening

### 1. Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. File Permissions
```bash
# Set proper permissions
sudo chown -R www-data:www-data /opt/learning_studio
sudo chmod -R 755 /opt/learning_studio
sudo chmod 600 /opt/learning_studio/.env
```

### 3. Database Security
```bash
# Secure PostgreSQL
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'secure_postgres_password';"

# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/pg_hba.conf
# Change 'local all all peer' to 'local all all md5'

sudo systemctl restart postgresql
```

## Monitoring and Logging

### 1. Log Configuration
```bash
# Create log directory
sudo mkdir -p /var/log/learning_studio
sudo chown www-data:www-data /var/log/learning_studio

# Configure log rotation
sudo cat > /etc/logrotate.d/learning-studio << EOF
/var/log/learning_studio/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload learning-studio
    endscript
}
EOF
```

### 2. Health Checks
```bash
# Create health check script
cat > health_check.sh << EOF
#!/bin/bash
curl -f http://localhost:8000/health/ || exit 1
EOF

chmod +x health_check.sh
```

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
cat > backup_db.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/db"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

pg_dump -h localhost -U learning_user -d learning_community > \$BACKUP_DIR/backup_\$DATE.sql
gzip \$BACKUP_DIR/backup_\$DATE.sql

# Keep only last 7 days
find \$BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_db.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /opt/learning_studio/backup_db.sh
```

### 2. Media Files Backup
```bash
# Create media backup script
cat > backup_media.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/media"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

tar -czf \$BACKUP_DIR/media_\$DATE.tar.gz -C /opt/learning_studio media/

# Keep only last 7 days
find \$BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup_media.sh
```

## Maintenance

### 1. Regular Updates
```bash
# Create update script
cat > update_app.sh << EOF
#!/bin/bash
cd /opt/learning_studio
source venv/bin/activate

# Pull latest changes
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart learning-studio
sudo systemctl restart nginx
EOF

chmod +x update_app.sh
```

### 2. System Monitoring
```bash
# Monitor services
sudo systemctl status learning-studio
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server

# Check logs
sudo journalctl -u learning-studio -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /opt/learning_studio/logs/django.log
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start
```bash
# Check service status
sudo systemctl status learning-studio

# Check logs
sudo journalctl -u learning-studio -n 50

# Common fixes
sudo systemctl restart learning-studio
```

#### 2. Database Connection Issues
```bash
# Test database connection
python manage.py dbshell

# Check PostgreSQL status
sudo systemctl status postgresql

# Reset database user password
sudo -u postgres psql -c "ALTER USER learning_user PASSWORD 'new_password';"
```

#### 3. Static Files Not Loading
```bash
# Recollect static files
python manage.py collectstatic --noinput

# Check nginx configuration
sudo nginx -t
sudo systemctl restart nginx
```

#### 4. Permission Errors
```bash
# Fix file permissions
sudo chown -R www-data:www-data /opt/learning_studio
sudo chmod -R 755 /opt/learning_studio
```

## Performance Optimization

### 1. Database Optimization
```bash
# PostgreSQL tuning (add to postgresql.conf)
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
max_connections = 100
```

### 2. Redis Optimization
```bash
# Redis tuning (add to redis.conf)
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### 3. Nginx Optimization
```bash
# Add to nginx configuration
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

This deployment guide provides a comprehensive setup for production deployment of Python Learning Studio.
