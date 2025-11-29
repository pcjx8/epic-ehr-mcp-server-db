"""
Test SSE Server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("="*80)
print("TESTING SSE SERVER")
print("="*80)

# Test 1: Health check
print("\n1. Health Check...")
response = requests.get(f"{BASE_URL}/health")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")

# Test 2: Get tools
print("\n2. Get Tools...")
response = requests.get(f"{BASE_URL}/tools")
print(f"   Status: {response.status_code}")
tools = response.json()["tools"]
print(f"   Found {len(tools)} tools:")
for tool in tools:
    print(f"     - {tool['name']}: {tool['description'][:50]}...")

# Test 3: Authenticate
print("\n3. Authenticate...")
with open("oauth_clients_credentials.json") as f:
    creds = json.load(f)[0]

response = requests.post(f"{BASE_URL}/authenticate", json={
    "client_id": creds["client_id"],
    "client_secret": creds["client_secret"],
    "app_id": creds["app_id"]
})
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    auth_data = response.json()
    print(f"   ✅ Authenticated as: {auth_data['client_info']['app_name']}")
    access_token = auth_data["access_token"]
    
    # Test 4: Call a tool
    print("\n4. Call Tool (search_patients)...")
    response = requests.post(f"{BASE_URL}/call", json={
        "tool": "search_patients",
        "arguments": {
            "access_token": access_token,
            "search_term": "John"
        }
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Tool executed successfully")
        print(f"   Result: {result['result']['content'][0]['text'][:100]}...")
else:
    print(f"   ❌ Authentication failed: {response.text}")

print("\n" + "="*80)
print("✅ SSE SERVER TEST COMPLETE")
print("="*80)
