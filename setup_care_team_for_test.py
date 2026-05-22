"""
Setup Care Team Members for Testing
Assigns care team members to a test patient for notification testing
"""
from models.database import SessionLocal, Patient, CareTeamMember

def setup_care_team(patient_phone: str, care_team_data: list):
    """
    Setup care team members for a patient
    
    Args:
        patient_phone: Patient phone number
        care_team_data: List of dicts with name, role, email, phone_number
    """
    db = SessionLocal()
    
    try:
        # Find or create patient
        patient = db.query(Patient).filter_by(phone_number=patient_phone).first()
        
        if not patient:
            print(f"❌ Patient with phone {patient_phone} not found!")
            print("Creating patient...")
            patient = Patient(
                name="Test Patient",
                phone_number=patient_phone
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            print(f"✅ Created patient: {patient.name} (ID: {patient.id})")
        else:
            print(f"✅ Found patient: {patient.name} (ID: {patient.id})")
        
        # Remove existing care team members for this patient
        existing_members = db.query(CareTeamMember).filter_by(patient_id=patient.id).all()
        for member in existing_members:
            db.delete(member)
        db.commit()
        print(f"🗑️  Removed {len(existing_members)} existing care team members")
        
        # Add new care team members
        print("\n📋 Adding care team members:")
        for member_data in care_team_data:
            member = CareTeamMember(
                patient_id=patient.id,
                name=member_data['name'],
                role=member_data['role'],
                email=member_data.get('email'),
                phone_number=member_data.get('phone_number'),
                is_primary=member_data.get('is_primary', False)
            )
            db.add(member)
            print(f"  ✅ {member.name} ({member.role})")
            print(f"     Email: {member.email}")
            print(f"     Phone: {member.phone_number}")
        
        db.commit()
        
        # Verify
        care_team = db.query(CareTeamMember).filter_by(patient_id=patient.id).all()
        print(f"\n✅ Successfully added {len(care_team)} care team members!")
        
        return patient.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("="*70)
    print("CARE TEAM SETUP FOR TESTING")
    print("="*70)
    
    # Test patient phone number
    TEST_PATIENT_PHONE = "+917477858611"
    
    # Care team members to add
    care_team = [
        {
            "name": "Dr. Gokul Kumar",
            "role": "Primary Physician",
            "email": "gokul.kumar@kanini.com",
            "phone_number": "+919715441374",
            "is_primary": True
        },
        {
            "name": "Nurse Abhishek",
            "role": "Care Coordinator",
            "email": "abhishek.kumar@kanini.com",
            "phone_number": "+917477858610",
            "is_primary": False
        }
    ]
    
    print(f"\nPatient Phone: {TEST_PATIENT_PHONE}")
    print(f"Care Team Members to Add: {len(care_team)}\n")
    
    patient_id = setup_care_team(TEST_PATIENT_PHONE, care_team)
    
    print("\n" + "="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print(f"\nPatient ID: {patient_id}")
    print(f"Care Team Members: {len(care_team)}")
    print("\n📧 When the patient submits the form, these care team members will receive:")
    print("  • Email notification with full AI summary")
    print("  • SMS notification with brief summary")
    print("\n🧪 Next Step: Send form link to patient and test!")
    print(f"\ncurl -X POST http://localhost:8080/api/mcp/outreach \\")
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"phone_number": "{TEST_PATIENT_PHONE}", "patient_name": "Test Patient", "outreach_type": "form"}}\'')
