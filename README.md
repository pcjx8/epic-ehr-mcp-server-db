# 🏥 EPIC EHR MCP Server

Production-ready Model Context Protocol (MCP) server for Electronic Health Records with OAuth 2.0 authentication.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Database (First Time Only)

**If you have existing data:**
- Database file `ehr_database.db` is already included
- Run `python seed_database.py` to add OAuth clients

**If starting fresh:**
```bash
python seed_database.py
```

This creates the database schema and OAuth clients.

### 3. Start Server

```bash
python server.py --websocket
```

Server runs on: `ws://0.0.0.0:7777`

**⚠️ IMPORTANT:** The `oauth_clients_credentials.json` file contains your OAuth credentials - keep it secure!

## 🔐 Authentication

Uses **OAuth 2.0 Client Credentials** flow:

```python
# Authenticate
{
  "client_id": "client_abc123...",
  "client_secret": "secret_xyz789...",
  "app_id": "copilot-studio"
}

# Returns access_token for API calls
```

## 📋 Available Tools

- **authenticate** - OAuth 2.0 authentication
- **register_client** - Register new OAuth client
- **validate_token** - Validate access token
- **get_patient** - Get patient by MRN
- **search_patients** - Search patients by name
- **create_patient** - Create new patient
- **get_appointments** - Get patient appointments
- **schedule_appointment** - Schedule new appointment
- **get_medications** - Get patient medications
- **prescribe_medication** - Prescribe new medication
- **get_lab_results** - Get lab results
- **get_vital_signs** - Get vital signs
- **record_vital_signs** - Record new vital signs
- **get_allergies** - Get patient allergies

## 🌐 Deployment

### DigitalOcean Droplet

1. **Create Droplet** (Ubuntu 22.04 LTS)
2. **Clone Repository**
   ```bash
   git clone <your-repo-url>
   cd epic-ehr-mcp-server-db
   ```

3. **Install Python & Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv -y
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with production values
   ```

5. **Upload Database**
   ```bash
   # Upload ehr_database.db and oauth_clients_credentials.json to server
   scp ehr_database.db root@your-droplet:/home/ehrserver/epic-ehr-mcp-server-db/
   scp oauth_clients_credentials.json root@your-droplet:/home/ehrserver/
   ```

6. **Run with systemd** (see DEPLOYMENT.md)

### Environment Variables

```bash
DATABASE_URL=sqlite:///ehr_database.db
JWT_SECRET_KEY=your-production-secret-key
SERVER_HOST=0.0.0.0
SERVER_PORT=7777
```

## 🔒 Security

- OAuth 2.0 client credentials
- JWT tokens (60-minute expiration)
- Client secrets hashed with SHA-256
- Role-based access control
- Scope-based permissions

## 📊 Database Schema

- **oauth_clients** - OAuth client credentials
- **patients** - Patient demographics
- **providers** - Healthcare providers
- **appointments** - Patient appointments
- **medications** - Prescriptions
- **allergies** - Patient allergies
- **vital_signs** - Vital measurements
- **lab_results** - Laboratory results

## 🧪 Testing

```bash
# Test authentication
python -c "from auth import authenticate_client; print(authenticate_client('client_id', 'secret', 'app_id'))"
```

## 📚 Documentation

- **ARCHITECTURE.md** - System architecture
- **DATABASE_SCHEMA.md** - Database schema details
- **DEPLOYMENT.md** - Deployment guide
- **oauth_clients_credentials.json** - OAuth credentials (gitignored)

## 🎯 Microsoft Copilot Studio Integration

This server is designed for Microsoft Copilot Studio MCP integration:

1. Configure MCP connection in Copilot Studio
2. Use WebSocket URL: `ws://your-server:7777`
3. Provide OAuth credentials from `oauth_clients_credentials.json`
4. Copilot Studio auto-discovers all tools

## 📞 Support

- Port: 7777 (WebSocket)
- Protocol: MCP (Model Context Protocol)
- Authentication: OAuth 2.0 Client Credentials

## 📝 License

MIT License - See LICENSE file

---

**Version:** 1.0.0  
**Last Updated:** November 28, 2025
