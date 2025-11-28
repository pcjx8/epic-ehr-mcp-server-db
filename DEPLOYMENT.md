# 🚀 Deployment Guide - DigitalOcean Droplet

## Quick Overview

This guide walks you through deploying the EPIC EHR MCP Server to a DigitalOcean droplet. The deployment includes:

- ✅ MCP Server with WebSocket support
- ✅ OAuth 2.0 authentication
- ✅ SQLite database with 221 patients and full medical records
- ✅ Systemd service for automatic startup
- ✅ Firewall configuration
- ✅ Optional SSL/TLS with Nginx

**Estimated Time:** 30-45 minutes

## Prerequisites

- DigitalOcean account
- GitHub repository with this code (or files ready to upload)
- SSH key configured
- Basic Linux command line knowledge

## Deployment Steps Summary

1. Create DigitalOcean droplet (Ubuntu 22.04)
2. Initial server setup (Python, Git, user creation)
3. Clone repository and install dependencies
4. Configure environment variables
5. Seed database with production data
6. Create systemd service
7. Configure firewall
8. Test connection
9. (Optional) Setup SSL/TLS with Nginx
10. Monitor and maintain

## Step 1: Create Droplet

1. Go to DigitalOcean Dashboard
2. Create Droplet:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($6/month minimum)
   - **CPU:** Regular Intel (1GB RAM minimum)
   - **Datacenter:** Choose closest to users
   - **Authentication:** SSH Key
   - **Hostname:** epic-ehr-mcp-server

3. Wait for droplet creation (1-2 minutes)

## Step 2: Initial Server Setup

```bash
# SSH into droplet
ssh root@your_droplet_ip

# Update system
apt update && apt upgrade -y

# Install Python and essentials
apt install python3 python3-pip python3-venv git nginx -y

# Create application user
adduser ehrserver
usermod -aG sudo ehrserver

# Switch to application user
su - ehrserver
```

## Step 3: Clone Repository

```bash
# Clone your repository
git clone https://github.com/your-username/epic-ehr-mcp-server-db.git
cd epic-ehr-mcp-server-db

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

**Production .env:**
```bash
DATABASE_URL=sqlite:///ehr_database.db
JWT_SECRET_KEY=$(openssl rand -hex 32)
SERVER_HOST=0.0.0.0
SERVER_PORT=7777
LOG_LEVEL=INFO
```

## Step 5: Setup Database

### Option A: Use Pre-Generated seed_database.py (Recommended)

The `seed_database.py` file contains all your production data (221 patients, 49 providers, appointments, medications, etc.). This is the easiest way to deploy with your existing data:

```bash
# On the droplet
cd epic-ehr-mcp-server-db
source venv/bin/activate

# Run the seed script (creates database with all data)
python seed_database.py

# This will:
# - Create ehr_database.db
# - Seed 6 OAuth clients
# - Seed 49 providers
# - Seed 221 patients
# - Seed 108 appointments
# - Seed 260 medications
# - Seed 117 allergies
# - Seed 361 vital signs
# - Seed 207 lab results

# Backup OAuth credentials (IMPORTANT!)
cp oauth_clients_credentials.json ~/oauth_backup.json
chmod 600 ~/oauth_backup.json

# View the credentials (save these securely)
cat oauth_clients_credentials.json
```

**Important:** The `oauth_clients_credentials.json` file contains the client secrets needed to authenticate. Save this file securely - you'll need it to connect clients to the server.

### Option B: Upload Existing Database

If you prefer to upload your local database file instead:

```bash
# From your local machine, upload the database
scp epic-ehr-mcp-server-db/ehr_database.db ehrserver@your_droplet_ip:/home/ehrserver/epic-ehr-mcp-server-db/

# Also upload OAuth credentials if you have them
scp epic-ehr-mcp-server-db/oauth_clients_credentials.json ehrserver@your_droplet_ip:/home/ehrserver/epic-ehr-mcp-server-db/

# SSH into droplet
ssh ehrserver@your_droplet_ip
cd epic-ehr-mcp-server-db

# Backup credentials
cp oauth_clients_credentials.json ~/oauth_backup.json
chmod 600 ~/oauth_backup.json
```

### Option C: Fresh Empty Database (For Testing)

If you want to start with an empty database:

```bash
# On the droplet
cd epic-ehr-mcp-server-db
source venv/bin/activate

# Initialize empty database
python -c "from database import init_database; init_database()"

# You can add data later through the API or by running seed_database.py
```

### Verify Database Setup

```bash
# Check database file exists
ls -lh ehr_database.db

# Check OAuth credentials exist
ls -lh oauth_clients_credentials.json

# Quick database check
python -c "from database import get_db_session; from models import Patient; session = get_db_session(); print(f'Patients: {session.query(Patient).count()}'); session.close()"
```

## Step 6: Create Systemd Service

```bash
# Exit to root
exit

# Create service file
sudo nano /etc/systemd/system/ehr-mcp-server.service
```

**Service file content:**
```ini
[Unit]
Description=EPIC EHR MCP Server
After=network.target

[Service]
Type=simple
User=ehrserver
WorkingDirectory=/home/ehrserver/epic-ehr-mcp-server-db
Environment="PATH=/home/ehrserver/epic-ehr-mcp-server-db/venv/bin"
ExecStart=/home/ehrserver/epic-ehr-mcp-server-db/venv/bin/python server.py --websocket
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable ehr-mcp-server

# Start service
sudo systemctl start ehr-mcp-server

# Check status
sudo systemctl status ehr-mcp-server
```

## Step 7: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow WebSocket port
sudo ufw allow 7777/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Step 8: Test Connection

### From Your Local Machine

**Option 1: Using the test client**

```bash
# Copy test_server.py and oauth_clients_credentials.json to your local machine
# Then run:
python test_server.py
```

**Option 2: Using wscat**

```bash
# Install wscat
npm install -g wscat

# Connect to server
wscat -c ws://your_droplet_ip:7777
```

**Option 3: Using Python**

Create a test script:

```python
import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://your_droplet_ip:7777"
    
    # Load credentials
    with open("oauth_clients_credentials.json") as f:
        creds = json.load(f)[0]
    
    async with websockets.connect(uri) as ws:
        # Test authentication
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "authenticate",
                "arguments": {
                    "client_id": creds["client_id"],
                    "client_secret": creds["client_secret"],
                    "app_id": creds["app_id"]
                }
            }
        }
        
        await ws.send(json.dumps(request))
        response = await ws.recv()
        print("Response:", response)

asyncio.run(test_connection())
```

### Verify Server is Running

```bash
# On the droplet, check service status
sudo systemctl status ehr-mcp-server

# Check if port is listening
sudo netstat -tlnp | grep 7777

# View recent logs
sudo journalctl -u ehr-mcp-server -n 50

# Test locally on droplet
curl -i http://localhost:7777
```

## Step 9: Setup SSL/TLS (Optional but Recommended)

### Using Nginx as Reverse Proxy

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Configure Nginx
sudo nano /etc/nginx/sites-available/ehr-mcp-server
```

**Nginx configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:7777;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ehr-mcp-server /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Step 10: Monitoring & Logs

```bash
# View logs
sudo journalctl -u ehr-mcp-server -f

# Check service status
sudo systemctl status ehr-mcp-server

# Restart service
sudo systemctl restart ehr-mcp-server

# Stop service
sudo systemctl stop ehr-mcp-server
```

## Maintenance

### Update Code

```bash
# SSH into droplet
ssh ehrserver@your_droplet_ip
cd epic-ehr-mcp-server-db

# Pull latest changes
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Exit and restart service
exit
sudo systemctl restart ehr-mcp-server

# Verify it's running
sudo systemctl status ehr-mcp-server
```

### Update Database with New Data

If you've updated your local database and want to deploy the changes:

```bash
# On your local machine, export the database to seed file
cd epic-ehr-mcp-server-db
python export_data_to_seed.py

# This generates a new seed_database.py with all current data

# Commit and push to GitHub
git add seed_database.py
git commit -m "Update database seed with latest data"
git push

# On the droplet, pull and re-seed
ssh ehrserver@your_droplet_ip
cd epic-ehr-mcp-server-db
sudo systemctl stop ehr-mcp-server

# Backup current database
cp ehr_database.db ehr_database_backup_$(date +%Y%m%d).db

# Pull new seed file
git pull

# Re-seed database
source venv/bin/activate
rm ehr_database.db  # Remove old database
python seed_database.py  # Create new database with updated data

# Restart service
exit
sudo systemctl start ehr-mcp-server
```

### Backup Database

```bash
# Create backups directory
mkdir -p ~/backups

# Backup database
cp /home/ehrserver/epic-ehr-mcp-server-db/ehr_database.db ~/backups/ehr_database_$(date +%Y%m%d).db

# Backup OAuth credentials
cp /home/ehrserver/oauth_backup.json ~/backups/oauth_$(date +%Y%m%d).json

# Download backup to local machine (from your local machine)
scp ehrserver@your_droplet_ip:~/backups/ehr_database_$(date +%Y%m%d).db ./backups/
```

### Automated Backups

```bash
# Create backup script
nano ~/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
cp /home/ehrserver/epic-ehr-mcp-server-db/ehr_database.db $BACKUP_DIR/ehr_database_$DATE.db

# Keep only last 7 days
find $BACKUP_DIR -name "ehr_database_*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Make executable
chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ehrserver/backup.sh
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u ehr-mcp-server -n 50

# Check permissions
ls -la /home/ehrserver/epic-ehr-mcp-server-db/

# Test manually
su - ehrserver
cd epic-ehr-mcp-server-db
source venv/bin/activate
python server.py --websocket
```

### Port already in use

```bash
# Check what's using port 7777
sudo lsof -i :7777

# Kill process if needed
sudo kill -9 <PID>
```

### Database locked

```bash
# Stop service
sudo systemctl stop ehr-mcp-server

# Check for locks
fuser /home/ehrserver/epic-ehr-mcp-server-db/ehr_database.db

# Restart service
sudo systemctl start ehr-mcp-server
```

## Security Checklist

- [ ] Changed JWT_SECRET_KEY in .env
- [ ] Backed up oauth_clients_credentials.json
- [ ] Configured firewall (ufw)
- [ ] Setup SSL/TLS with certbot
- [ ] Regular backups configured
- [ ] Monitoring setup
- [ ] Strong SSH key authentication
- [ ] Disabled root SSH login
- [ ] Updated all packages

## Performance Tuning

### For High Traffic

```bash
# Increase file descriptors
sudo nano /etc/security/limits.conf
# Add:
# ehrserver soft nofile 65536
# ehrserver hard nofile 65536
```

### Database Optimization

```python
# Use PostgreSQL for production
DATABASE_URL=postgresql://user:password@localhost/ehr_db
```

## Monitoring

### Setup Monitoring (Optional)

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor resources
htop

# Monitor network
nethogs

# Monitor disk I/O
iotop
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `sudo systemctl start ehr-mcp-server` | Start server |
| `sudo systemctl stop ehr-mcp-server` | Stop server |
| `sudo systemctl restart ehr-mcp-server` | Restart server |
| `sudo systemctl status ehr-mcp-server` | Check status |
| `sudo journalctl -u ehr-mcp-server -f` | View logs |
| `sudo ufw status` | Check firewall |

---

**Server URL:** `ws://your_droplet_ip:7777`  
**With SSL:** `wss://your-domain.com`  
**Port:** 7777
