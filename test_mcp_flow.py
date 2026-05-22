"""
Test MCP Architecture Flow
Demonstrates the new MCP-powered patient outreach workflow
"""
import requests
import json

BASE_URL = "http://localhost:8080/api"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_mcp_status():
    """Test MCP architecture status"""
    print_section("1. Testing MCP Architecture Status")
    
    response = requests.get(f"{BASE_URL}/mcp/status")
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_list_tools():
    """Test listing available MCP tools"""
    print_section("2. Listing Available MCP Tools")
    
    response = requests.get(f"{BASE_URL}/mcp/tools")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal Tools: {data.get('total_tools')}")
        print("\nRegistered Tools:")
        for tool in data.get('tools', []):
            print(f"  - {tool['name']}: {tool['description'][:60]}...")
    
    return response.status_code == 200

def test_mcp_outreach_conversation():
    """Test MCP-powered conversation outreach"""
    print_section("3. Testing MCP Outreach - Conversation Type")
    
    payload = {
        "phone_number": "+917477858611",
        "patient_name": "Test Patient",
        "outreach_type": "conversation",
        "discharge_summary": {
            "patient_name": "Test Patient",
            "hospitalization_reason": "Routine checkup"
        }
    }
    
    print(f"Request Payload:\n{json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    response = requests.post(f"{BASE_URL}/mcp/outreach", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_mcp_outreach_notification():
    """Test MCP-powered notification outreach"""
    print_section("4. Testing MCP Outreach - Notification Type")
    
    payload = {
        "phone_number": "+917477858611",
        "patient_name": "Test Patient",
        "outreach_type": "notification",
        "custom_message": "Your test results are ready. Please contact your doctor."
    }
    
    print(f"Request Payload:\n{json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    response = requests.post(f"{BASE_URL}/mcp/outreach", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_mcp_outreach_form():
    """Test MCP-powered Google Form outreach"""
    print_section("5. Testing MCP Outreach - Google Form Type")
    
    payload = {
        "phone_number": "+917477858611",
        "patient_name": "Test Patient",
        "outreach_type": "form"
    }
    
    print(f"Request Payload:\n{json.dumps(payload, indent=2)}")
    print("\nSending request...")
    print("This will send a Google Form link to the patient via SMS")
    
    response = requests.post(f"{BASE_URL}/mcp/outreach", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_health_check():
    """Test health check with MCP status"""
    print_section("6. Testing Health Check (with MCP status)")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nAPI Status: {data.get('status')}")
        print(f"MCP Architecture Enabled: {data.get('mcp_architecture', {}).get('enabled')}")
        print(f"Registered MCP Tools: {data.get('mcp_architecture', {}).get('registered_tools')}")
    
    return response.status_code == 200

def test_backward_compatibility():
    """Test that old endpoints still work"""
    print_section("7. Testing Backward Compatibility (Old Endpoint)")
    
    payload = {
        "phone_number": "+917477858611",
        "patient_name": "Test Patient"
    }
    
    print(f"Testing old /start-conversation endpoint...")
    print(f"Request Payload:\n{json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/start-conversation", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  MCP ARCHITECTURE FLOW TEST SUITE")
    print("="*70)
    print("\nThis test demonstrates the new MCP architecture:")
    print("  Flask API → AI Agent → MCP Server → Tools → Services")
    print("\nMake sure the Flask app is running: python app.py")
    
    input("\nPress Enter to start tests...")
    
    results = []
    
    # Run tests
    results.append(("MCP Status", test_mcp_status()))
    results.append(("List Tools", test_list_tools()))
    results.append(("MCP Outreach (Conversation)", test_mcp_outreach_conversation()))
    results.append(("MCP Outreach (Notification)", test_mcp_outreach_notification()))
    results.append(("MCP Outreach (Google Form)", test_mcp_outreach_form()))
    results.append(("Health Check", test_health_check()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Print summary
    print_section("TEST SUMMARY")
    print("\nResults:")
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MCP architecture is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Flask app.")
        print("Make sure the app is running: python app.py")
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error running tests: {str(e)}")
