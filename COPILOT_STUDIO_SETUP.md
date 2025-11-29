# Copilot Studio MCP Integration Guide

## The Problem You Had

Your server was returning tools correctly via REST endpoints (`/tools`), but Copilot Studio was showing an empty list `[]`. 

**Why?** Copilot Studio expects **JSON-RPC 2.0** format, not simple REST responses.

## The Solution

Added a `/mcp` endpoint that handles JSON-RPC 2.0 requests with proper format.

---

## Testing the JSON-RPC Endpoint

### 1. Test tools/list (What Copilot Studio Calls)

This is the **exact** request Copilot Studio sends:

```bash
curl -X POST http://178.62.72.200:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/list",
    "params": {}
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "tools": [
      {
        "name": "search_patients",
        "description": "Search for patients by name, MRN, or date of birth",
        "inputSchema": {
          "type": "object",
          "properties": {
            "access_token": {
              "type": "string",
              "description": "OAuth access token"
            },
            "search_term": {
              "type": "string",
              "description": "Search term (name, MRN, or DOB)"
            }
          },
          "required": ["access_token"]
        }
      },
      ... 13 more tools ...
    ]
  }
}
```

### 2. Test Authentication

```bash
curl -X POST http://178.62.72.200:8000/authenticate \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "client_I7T_TK2uPpa0CBPxEQzTaKuNenTlSBzCfN8LRON-xLE",
    "client_secret": "WrQDQAinSIwJINf7jigT7sl5fw3e9h8nTcPpZVE8el53UukgeHCMq0zmFbIupsWu",
    "app_id": "copilot-studio"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "client_info": {
    "client_id": "client_I7T_TK2uPpa0CBPxEQzTaKuNenTlSBzCfN8LRON-xLE",
    "app_id": "copilot-studio"
  }
}
```

### 3. Test tools/call via JSON-RPC

```bash
# First, get the access token from step 2, then:
curl -X POST http://178.62.72.200:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "search_patients",
      "arguments": {
        "access_token": "YOUR_ACCESS_TOKEN_HERE",
        "search_term": "John"
      }
    }
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"patient_id\": 1, \"name\": \"John Smith\", ...}]"
      }
    ]
  }
}
```

---

## Configuring Copilot Studio

### Step 1: Add MCP Connection

1. In Copilot Studio, go to **Settings** → **Generative AI** → **Model Context Protocol**
2. Click **Add Connection**

### Step 2: Configure the Connection

**Connection Name:** EPIC EHR MCP Server

**Endpoint URL:** `http://178.62.72.200:8000/mcp`

**Transport:** HTTP/SSE

**Authentication:** None (we handle auth via access tokens in tool calls)

### Step 3: Test Connection

Click **Test Connection** - you should see:
- ✅ Connection successful
- ✅ 14 tools discovered

### Step 4: Available Tools

After connection, these tools will be available in Copilot Studio:

1. **authenticate** - Get OAuth access token
2. **search_patients** - Search for patients
3. **get_patient** - Get patient details
4. **get_patient_appointments** - Get patient appointments
5. **book_appointment** - Book new appointment
6. **cancel_appointment** - Cancel appointment
7. **get_patient_medications** - Get patient medications
8. **prescribe_medication** - Prescribe new medication
9. **get_patient_allergies** - Get patient allergies
10. **add_allergy** - Add new allergy
11. **get_patient_vitals** - Get vital signs
12. **record_vitals** - Record new vitals
13. **get_patient_labs** - Get lab results
14. **order_lab** - Order new lab test

---

## Authentication Flow in Copilot

### Option 1: Authenticate Once Per Session

In your Copilot topic, add this at the start:

```
Call action: authenticate
  client_id: client_I7T_TK2uPpa0CBPxEQzTaKuNenTlSBzCfN8LRON-xLE
  client_secret: WrQDQAinSIwJINf7jigT7sl5fw3e9h8nTcPpZVE8el53UukgeHCMq0zmFbIupsWu
  app_id: copilot-studio

Store result in: Topic.AccessToken
```

Then use `Topic.AccessToken` in all subsequent tool calls.

### Option 2: Pre-authenticate

Store the access token in a global variable and refresh it when expired.

---

## Troubleshooting

### Issue: Copilot shows "No tools found"

**Check 1:** Verify the endpoint returns JSON-RPC 2.0 format
```bash
curl -X POST http://178.62.72.200:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}'
```

Should return:
- `"jsonrpc": "2.0"` ✅
- `"id": "1"` ✅
- `"result": { "tools": [...] }` ✅

**Check 2:** Verify the endpoint URL in Copilot Studio
- Must be: `http://178.62.72.200:8000/mcp`
- NOT: `http://178.62.72.200:8000/tools`

**Check 3:** Check server logs
```bash
# On your DigitalOcean droplet
sudo journalctl -u sse-server -f
```

### Issue: Tools found but calls fail

**Check:** Access token is being passed correctly
- Each tool call needs `access_token` in arguments
- Token expires after 1 hour
- Re-authenticate if you get 401 errors

### Issue: Connection timeout

**Check:** Firewall allows port 8000
```bash
sudo ufw status
sudo ufw allow 8000/tcp
```

---

## Python Test Script

Run the comprehensive test:

```bash
cd epic-ehr-mcp-server-db
python test_jsonrpc.py
```

This will test:
1. ✅ JSON-RPC tools/list
2. ✅ Authentication
3. ✅ JSON-RPC tools/call
4. ✅ Error handling

---

## Key Differences: REST vs JSON-RPC

### ❌ Old REST Endpoint (doesn't work with Copilot)

```bash
curl http://178.62.72.200:8000/tools
```

Returns:
```json
[
  {"name": "search_patients", "description": "...", ...}
]
```

### ✅ New JSON-RPC Endpoint (works with Copilot)

```bash
curl -X POST http://178.62.72.200:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}}'
```

Returns:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "tools": [
      {"name": "search_patients", "description": "...", ...}
    ]
  }
}
```

The difference:
- JSON-RPC wraps everything in `{"jsonrpc": "2.0", "id": "...", "result": {...}}`
- Uses `method` parameter to specify action
- Returns structured error responses

---

## Next Steps

1. **Test the endpoint:**
   ```bash
   python test_jsonrpc.py
   ```

2. **Configure Copilot Studio:**
   - Endpoint: `http://178.62.72.200:8000/mcp`
   - Test connection
   - Verify 14 tools appear

3. **Build your first topic:**
   - Authenticate at start
   - Use tools in conversation flow
   - Handle errors gracefully

4. **Monitor logs:**
   ```bash
   sudo journalctl -u sse-server -f
   ```

---

## Support

If tools still don't appear in Copilot Studio:

1. Run `python test_jsonrpc.py` and share output
2. Check Copilot Studio connection logs
3. Verify endpoint URL is exactly: `http://178.62.72.200:8000/mcp`
4. Ensure server is running: `sudo systemctl status sse-server`

The JSON-RPC endpoint is now fully compatible with Microsoft Copilot Studio! 🎉
