# 📦 GitHub Setup Guide

## Quick Setup

### 1. Initialize Git Repository

```bash
cd epic-ehr-mcp-server-db
git init
```

### 2. Add Files

```bash
git add .
```

### 3. Commit

```bash
git commit -m "Initial commit - Production ready EHR MCP Server with OAuth 2.0"
```

### 4. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `epic-ehr-mcp-server`
3. Description: "Production-ready MCP server for EHR with OAuth 2.0 authentication"
4. **Private** repository (recommended for healthcare data)
5. Don't initialize with README (we have one)
6. Click "Create repository"

### 5. Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/epic-ehr-mcp-server.git
git branch -M main
git push -u origin main
```

---

## ⚠️ Important: Verify .gitignore

Before pushing, verify these files are NOT included:

```bash
# Check what will be committed
git status

# These should NOT appear:
# - ehr_database.db
# - oauth_clients_credentials.json
# - .env
# - __pycache__/
```

If they appear, they're being tracked. Remove them:

```bash
git rm --cached ehr_database.db
git rm --cached oauth_clients_credentials.json
git rm --cached .env
git commit -m "Remove sensitive files"
```

---

## 📋 What Gets Pushed

✅ **Included:**
- Source code (.py files)
- Documentation (.md files)
- Requirements (requirements.txt)
- Configuration templates (.env.example)
- Git ignore rules (.gitignore)

❌ **Excluded (gitignored):**
- Database files (*.db)
- OAuth credentials (oauth_clients_credentials.json)
- Environment variables (.env)
- Python cache (__pycache__/)
- IDE files (.vscode/, .idea/)

---

## 🔐 Security Best Practices

### Never Commit:
- ❌ Database files
- ❌ OAuth credentials
- ❌ API keys
- ❌ Passwords
- ❌ JWT secrets

### Always Use:
- ✅ .gitignore
- ✅ Environment variables
- ✅ .env.example (template only)
- ✅ Private repositories for healthcare

---

## 🚀 Clone on DigitalOcean Droplet

```bash
# SSH into droplet
ssh root@your_droplet_ip

# Clone repository
git clone https://github.com/YOUR_USERNAME/epic-ehr-mcp-server.git
cd epic-ehr-mcp-server

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with production values

# Seed database
python seed_production.py

# Start server
python server.py --websocket
```

---

## 🔄 Update Deployment

When you make changes:

```bash
# On local machine
git add .
git commit -m "Description of changes"
git push

# On droplet
cd epic-ehr-mcp-server
git pull
source venv/bin/activate
pip install -r requirements.txt  # If dependencies changed
sudo systemctl restart ehr-mcp-server
```

---

## 📝 Recommended Repository Settings

### Branch Protection
- Require pull request reviews
- Require status checks to pass
- Restrict who can push to main

### Secrets (for CI/CD)
- Add secrets in Settings → Secrets
- Never hardcode in code

### Collaborators
- Add team members with appropriate permissions
- Use teams for organization

---

## 🏷️ Tagging Releases

```bash
# Tag version
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# List tags
git tag

# Checkout specific version
git checkout v1.0.0
```

---

## 📚 Repository Structure

```
epic-ehr-mcp-server/
├── .git/                        # Git repository
├── .gitignore                   # Ignore rules
├── README.md                    # Main documentation
├── DEPLOYMENT.md                # Deployment guide
├── ARCHITECTURE.md              # System architecture
├── DATABASE_SCHEMA.md           # Database schema
├── PRODUCTION_READY.md          # Production checklist
├── GITHUB_SETUP.md              # This file
├── server.py                    # MCP server
├── auth.py                      # OAuth authentication
├── database.py                  # Database layer
├── models.py                    # Data models
├── tools.py                     # Tool implementations
├── seed_production.py           # Seeding script
├── test_server.py               # Test suite
├── requirements.txt             # Dependencies
└── .env.example                 # Environment template
```

---

## ✅ Verification Checklist

Before pushing:

- [ ] .gitignore is configured
- [ ] No database files in git
- [ ] No credentials in git
- [ ] No .env files in git
- [ ] README.md is complete
- [ ] Documentation is up to date
- [ ] Tests pass locally
- [ ] Requirements.txt is current

---

## 🆘 Troubleshooting

### "Permission denied (publickey)"

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy and add to GitHub Settings → SSH Keys
```

### "Repository not found"

```bash
# Check remote URL
git remote -v

# Update if needed
git remote set-url origin https://github.com/YOUR_USERNAME/epic-ehr-mcp-server.git
```

### Accidentally committed sensitive file

```bash
# Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch oauth_clients_credentials.json" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

---

**Ready to push!** 🚀
