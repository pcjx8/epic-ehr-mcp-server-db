"""
Test Script for MCP Server
Tests all tools to ensure they work correctly
"""

import asyncio
import websockets
import json


class MCPTestClient:
    def __init__(self, url="ws://localhost:7777"):
        self.url = url
        self.ws = None
        self.request_id = 0
        self.access_token = None
    
    async def connect(self):
        """Connect to server"""
        self.ws = await websockets.connect(self.url)
        print(f"✅ Connected to {self.url}")
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.ws:
            await self.ws.close()
            print("✅ Disconnected")
    
    async def send_request(self, method, params=None):
        """Send JSON-RPC request"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        await self.ws.send(json.dumps(request))
        response = await self.ws.recv()
        return json.loads(response)
    
    async def authenticate(self, client_id, client_secret, app_id):
        """Authenticate with OAuth"""
        print(f"\n🔐 Authenticating...")
        response = await self.send_request("tools/call", {
            "name": "authenticate",
            "arguments": {
                "client_id": client_id,
                "client_secret": client_secret,
                "app_id": app_id
            }
        })
        
        if "result" in response:
            result = json.loads(response["result"]["content"][0]["text"])
            if result["status"] == "success":
                self.access_token = result["access_token"]
                print(f"✅ Authenticated as: {result['client_info']['app_name']}")
                print(f"   Role: {result['client_info']['role']}")
                return True
        
        print(f"❌ Authentication failed")
        return False
    
    async def call_tool(self, tool_name, **kwargs):
        """Call a tool"""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        kwargs["access_token"] = self.access_token
        
        response = await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": kwargs
        })
        
        if "result" in response:
            return json.loads(response["result"]["content"][0]["text"])
        return {"status": "error", "message": "Unknown error"}


async def test_all_tools():
    """Test all MCP tools"""
    print("\n" + "="*80)
    print("MCP SERVER TEST SUITE")
    print("="*80)
    
    # Load credentials
    try:
        with open("oauth_clients_credentials.json", "r") as f:
            credentials = json.load(f)
            creds = credentials[0]  # Use first client
    except FileNotFoundError:
        print("❌ Error: oauth_clients_credentials.json not found")
        print("   Run: python seed_production.py first")
        return
    
    client = MCPTestClient()
    
    try:
        # Connect
        await client.connect()
        
        # Authenticate
        authenticated = await client.authenticate(
            creds["client_id"],
            creds["client_secret"],
            creds["app_id"]
        )
        
        if not authenticated:
            return
        
        # Test 1: Search Patients
        print("\n📋 Test 1: Search Patients")
        result = await client.call_tool("search_patients", search_term="John")
        if result.get("status") == "success":
            print(f"✅ Found {result['count']} patients")
            if result['count'] > 0:
                print(f"   First: {result['patients'][0]['name']}")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        # Test 2: Get Patient
        print("\n👤 Test 2: Get Patient")
        result = await client.call_tool("get_patient", mrn="MRN001")
        if result.get("status") == "success":
            patient = result["patient"]
            print(f"✅ Patient: {patient['first_name']} {patient['last_name']}")
            print(f"   DOB: {patient['dob']}")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        # Test 3: Get Appointments
        print("\n📅 Test 3: Get Appointments")
        result = await client.call_tool("get_appointments", mrn="MRN001")
        if result.get("status") == "success":
            print(f"✅ Found {len(result['appointments'])} appointments")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        # Test 4: Get Medications
        print("\n💊 Test 4: Get Medications")
        result = await client.call_tool("get_medications", mrn="MRN001")
        if result.get("status") == "success":
            print(f"✅ Found {len(result['medications'])} medications")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        # Test 5: Get Allergies
        print("\n🚨 Test 5: Get Allergies")
        result = await client.call_tool("get_allergies", mrn="MRN002")
        if result.get("status") == "success":
            print(f"✅ Found {len(result['allergies'])} allergies")
            if result['allergies']:
                print(f"   First: {result['allergies'][0]['allergen']}")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        # Test 6: Get Vital Signs
        print("\n🩺 Test 6: Get Vital Signs")
        result = await client.call_tool("get_vital_signs", mrn="MRN001")
        if result.get("status") == "success":
            print(f"✅ Found {len(result['vital_signs'])} vital sign records")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        # Test 7: Get Lab Results
        print("\n🔬 Test 7: Get Lab Results")
        result = await client.call_tool("get_lab_results", mrn="MRN001")
        if result.get("status") == "success":
            print(f"✅ Found {len(result['lab_results'])} lab results")
        else:
            print(f"❌ Failed: {result.get('message')}")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETE!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_all_tools())
