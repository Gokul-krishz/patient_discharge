"""
Check specific record and related records
"""
from models.database import FormResponse, SessionLocal

db = SessionLocal()

record_id = 17
r = db.query(FormResponse).filter_by(id=record_id).first()

if r:
    print(f"Record ID {record_id}:")
    print("=" * 70)
    print(f"Patient: {r.patient_name}")
    print(f"Phone: {r.patient_phone}")
    print(f"Form Link Sent: {r.form_link_sent_at}")
    print(f"Submitted: {r.submitted_at}")
    print(f"Created: {r.created_at}")
    print("\nResponses:")
    print(f"  Recently Discharged: {r.recently_discharged}")
    print(f"  Medication Changes: {r.medication_changes}")
    print(f"  Current Symptoms: {r.current_symptoms}")
    print(f"  Care Team Notes: {r.care_team_notes}")
    print(f"  Contact Request: {r.contact_request}")
    print(f"\nRaw Responses: {r.raw_responses}")
    print(f"\nSummary: {r.summary}")
    
    # Check all records for same phone
    print("\n" + "=" * 70)
    print(f"All records for {r.patient_phone}:")
    print("=" * 70)
    
    all_records = db.query(FormResponse).filter_by(patient_phone=r.patient_phone).order_by(FormResponse.id.desc()).all()
    for rec in all_records:
        has_summary = "Yes" if rec.summary else "No"
        print(f"\nID {rec.id}:")
        print(f"  Sent: {rec.form_link_sent_at}")
        print(f"  Submitted: {rec.submitted_at}")
        print(f"  Summary: {has_summary}")
else:
    print(f"Record ID {record_id} NOT FOUND")

db.close()
