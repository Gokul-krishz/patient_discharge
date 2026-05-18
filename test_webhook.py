"""
Test script to verify the forms webhook is working
"""
import requests
import json

# Test payload (simulates what Google Apps Script sends)
payload = {
    "patient_phone": "+919715441374",
    "patient_name": "John Test",
    "submitted_at": "2026-05-16T10:45:00",
    "responses": {
        "feeling_today": "Good",
        "shortness_of_breath": "No",
        "dialysis_attended": "Yes",
        "medications_taken": "Yes",
        "followup_scheduled": "Yes",
        "additional_notes": "Feeling much better"
    }
}

# Test locally first
print("Testing webhook locally...")
response = requests.post(
    'http://localhost:8080/api/forms/webhook',
    json=payload,
    headers={'Content-Type': 'application/json'}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 200:
    print("\n✅ Webhook is working!")
    print("\nNow check the database:")
    print("GET http://localhost:8080/api/forms/responses/+919715441374")
else:
    print("\n❌ Webhook failed!")
