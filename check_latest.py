"""
Check latest record
"""
from models.database import FormResponse, SessionLocal

db = SessionLocal()

r = db.query(FormResponse).order_by(FormResponse.id.desc()).first()

if r:
    print("=" * 70)
    print(f"LATEST RECORD: ID {r.id}")
    print("=" * 70)
    print(f"Patient: {r.patient_name}")
    print(f"Phone: {r.patient_phone}")
    print(f"Form Link Sent: {r.form_link_sent_at}")
    print(f"Submitted: {r.submitted_at}")
    print(f"Created: {r.created_at}")
    print(f"\nHas Summary: {'Yes' if r.summary else 'No'}")
    if r.summary:
        print(f"\nSummary Preview:")
        print(r.summary[:200] + "...")
    print("\nResponses:")
    print(f"  Recently Discharged: {r.recently_discharged}")
    print(f"  Medication Changes: {r.medication_changes}")
    print(f"  Current Symptoms: {r.current_symptoms}")
    print(f"  Care Team Notes: {r.care_team_notes}")
    print(f"  Contact Request: {r.contact_request}")
    print("=" * 70)
else:
    print("No records found")

db.close()
