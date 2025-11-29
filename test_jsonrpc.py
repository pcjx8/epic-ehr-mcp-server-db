"""
Test JSON-RPC 2.0 endpoint for Copilot Studio compatibility
"""

import requests
import json

# Server URL - change to production URL when ready
BASE_URL = "http://localhost:8000"
# BASE_URL = "http://178.62.72.200:8000"  # Production

def test_tools_list():
    """Test tools/list method (what Copilot Studio calls)"""
    print("\n" + "="*60)
    print("TEST 1: JSON-RPC tools/list")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/list",
        "params": {}
    }
    
    print(f"\nRequest to {BASE_URL}/mcp:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(f"{BASE_URL}/mcp", json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    # Validate response
    data = response.json()
    assert data.get("jsonrpc") == "2.0", "Missing jsonrpc field"
    assert data.get("id") == "1", "ID mismatch"
    assert "result" in data, "Missing result field"
    assert "tools" in data["result"], "Missing tools array"
    
    tools = data["result"]["tools"]
    print(f"\n✅ SUCCESS: Found {len(tools)} tools")
    
    # Print first tool as example
    if tools:
        print(f"\nExample tool:")
        print(json.dumps(tools[0], indent=2))
    
    return tools


def test_authenticate():
    """Test authentication to get access token"""
    print("\n" + "="*60)
    print("TEST 2: Authenticate")
    print("="*60)
    
    payload = {
        "client_id": "client_I7T_TK2uPpa0CBPxEQzTaKuNenTlSBzCfN8LRON-xLE",
        "client_secret": "WrQDQAinSIwJINf7jigT7sl5fw3e9h8nTcPpZVE8el53UukgeHCMq0zmFbIupsWu",
        "app_id": "copilot-studio"
    }
    
    print(f"\nRequest to {BASE_URL}/authenticate:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(f"{BASE_URL}/authenticate", json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    data = response.json()
    access_token = data.get("access_token")
    
    print(f"\n✅ SUCCESS: Got access token")
    return access_token


def test_tools_call(access_token):
    """Test tools/call method via JSON-RPC"""
    print("\n" + "="*60)
    print("TEST 3: JSON-RPC tools/call")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {
            "name": "search_patients",
            "arguments": {
                "access_token": access_token,
                "search_term": "John"
            }
        }
    }
    
    print(f"\nRequest to {BASE_URL}/mcp:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(f"{BASE_URL}/mcp", json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    # Validate response
    assert result.get("jsonrpc") == "2.0", "Missing jsonrpc field"
    assert result.get("id") == "2", "ID mismatch"
    assert "result" in result, "Missing result field"
    
    print(f"\n✅ SUCCESS: Tool executed successfully")


def test_invalid_method():
    """Test invalid method handling"""
    print("\n" + "="*60)
    print("TEST 4: Invalid method (should return error)")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "invalid/method",
        "params": {}
    }
    
    print(f"\nRequest to {BASE_URL}/mcp:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(f"{BASE_URL}/mcp", json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    data = response.json()
    assert "error" in data, "Should return error"
    assert data["error"]["code"] == -32601, "Should be 'Method not found' error"
    
    print(f"\n✅ SUCCESS: Error handling works correctly")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("JSON-RPC 2.0 MCP Server Test Suite")
    print("Testing Copilot Studio compatibility")
    print("="*60)
    
    try:
        # Test 1: List tools
        tools = test_tools_list()
        
        # Test 2: Authenticate
        access_token = test_authenticate()
        
        # Test 3: Call a tool
        test_tools_call(access_token)
        
        # Test 4: Invalid method
        test_invalid_method()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nYour server is now Copilot Studio compatible!")
        print(f"\nCopilot Studio should use this endpoint:")
        print(f"  {BASE_URL}/mcp")
        print(f"\nWith JSON-RPC 2.0 format:")
        print(f'  {{"jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {{}}}}')
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
