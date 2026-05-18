"""
Test webhook with actual payload to see the error
"""
import requests
from datetime import datetime

# Simulate a Google Form submission
payload = {
    "patient_phone": "+917477858611",
    "patient_name": "Test Patient",
    "submitted_at": datetime.utcnow().isoformat(),
    "responses": {
        "recently_discharged": "Yes, 2 days ago",
        "medication_changes": "New medication",
        "current_symptoms": "Feeling better",
        "care_team_notes": "All good",
        "contact_request": "Yes"
    }
}

print("=" * 70)
print("TESTING WEBHOOK")
print("=" * 70)

try:
    response = requests.post(
        "http://127.0.0.1:8080/api/forms/webhook",
        json=payload,
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"\nException: {e}")

print("\n" + "=" * 70)
