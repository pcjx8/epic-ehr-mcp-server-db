# 🚀 Deployment Options

## Two Ways to Deploy Your Database

### Option 1: Upload Existing Database (Recommended) ✅

**Use this if:** You have production data on your local machine

**Steps:**
1. Push code to GitHub (without database file - it's gitignored)
2. Clone repository on droplet
3. Upload `ehr_database.db` from local machine to droplet
4. Run `python seed_database.py` to add OAuth clients
5. Start server

**Advantages:**
- ✅ All your existing data (221 patients, 49 providers, etc.)
- ✅ No data loss
- ✅ Production-ready immediately

**Commands:**
```bash
# On droplet
git clone <your-repo-url>
cd epic-ehr-mcp-server-db
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# From local machine (separate terminal)
scp ehr_database.db root@your-droplet-ip:/home/ehrserver/epic-ehr-mcp-server-db/

# Back on droplet
python seed_database.py  # Adds OAuth clients
python server.py --websocket
```

---

### Option 2: Fresh Database (For Testing) 🆕

**Use this if:** You want to start fresh or test the deployment

**Steps:**
1. Push code to GitHub
2. Clone repository on droplet
3. Run `python seed_database.py` (creates empty database + OAuth clients)
4. Start server
5. Add data through API later

**Advantages:**
- ✅ Clean start
- ✅ Good for testing
- ✅ Can add data via API

**Commands:**
```bash
# On droplet
git clone <your-repo-url>
cd epic-ehr-mcp-server-db
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed fresh database
python seed_database.py  # Creates schema + OAuth clients

# Start server
python server.py --websocket
```

---

## What `seed_database.py` Does

1. **Initializes Database Schema**
   - Creates all tables (patients, providers, appointments, etc.)
   - Sets up relationships and indexes

2. **Seeds OAuth Clients**
   - Creates 6 OAuth clients:
     - Microsoft Copilot Studio (doctor)
     - Hospital EHR Application (doctor)
     - Patient Portal (patient)
     - Laboratory Integration (system)
     - Pharmacy System (system)
     - Nurse Station (nurse)

3. **Checks Existing Data**
   - Detects if database already has data
   - Shows current record counts
   - Adds OAuth clients without duplicating data

4. **Saves Credentials**
   - Creates `oauth_clients_credentials.json`
   - Contains client_id and client_secret for each OAuth client
   - ⚠️ Must be backed up securely!

---

## Comparison

| Feature | Option 1: Upload DB | Option 2: Fresh DB |
|---------|--------------------|--------------------|
| **Data** | All existing data | Empty (OAuth only) |
| **Setup Time** | 5 minutes | 2 minutes |
| **Production Ready** | ✅ Immediately | ❌ Need to add data |
| **Best For** | Production | Testing/Development |
| **Data Transfer** | Upload 1 file | None needed |

---

## After Deployment

Both options result in:
- ✅ Server running on port 7777
- ✅ OAuth 2.0 authentication configured
- ✅ 6 OAuth clients ready to use
- ✅ Database schema created
- ✅ Ready for Copilot Studio integration

**Next Steps:**
1. Test connection: `python test_server.py`
2. Configure systemd service (see DEPLOYMENT.md)
3. Setup firewall
4. Connect Microsoft Copilot Studio

---

## Security Notes

### Files to Upload (Option 1):
- ✅ `ehr_database.db` - Contains all patient data
- ⚠️ Use secure transfer (scp with SSH keys)
- ⚠️ Backup before uploading

### Files Generated on Droplet:
- `oauth_clients_credentials.json` - OAuth secrets
- ⚠️ Backup immediately after generation
- ⚠️ Never commit to git

### Files in Git:
- ✅ All `.py` files
- ✅ Documentation
- ✅ `.env.example`
- ❌ NOT `ehr_database.db`
- ❌ NOT `oauth_clients_credentials.json`

---

## Troubleshooting

### "Database already contains data"
- ✅ This is normal if you uploaded `ehr_database.db`
- ✅ Script will add OAuth clients without affecting existing data

### "No OAuth clients found"
- ❌ Run `python seed_database.py` again
- ✅ Check `oauth_clients_credentials.json` was created

### "Connection refused"
- ❌ Check server is running: `python server.py --websocket`
- ❌ Check firewall allows port 7777
- ❌ Check server binds to 0.0.0.0 (not localhost)

---

**Recommended:** Use Option 1 (Upload Existing Database) for production deployment.
