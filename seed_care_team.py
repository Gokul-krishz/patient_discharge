"""
Seed script to insert sample care team members
"""
from models.database import Patient, CareTeamMember, SessionLocal
from datetime import datetime

def seed_care_team():
    """Insert 5 sample care team members"""
    db = SessionLocal()
    
    try:
        # First, ensure we have a patient
        patient = db.query(Patient).filter_by(phone_number='+919677863998').first()
        
        if not patient:
            # Create a sample patient
            patient = Patient(
                name='Kishore',
                phone_number='+919677863998',
                created_at=datetime.utcnow()
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            print(f"Created patient: {patient.name} (ID: {patient.id})")
        else:
            print(f"Using existing patient: {patient.name} (ID: {patient.id})")
        
        # Define 5 care team members
        care_team_members = [
            {
                'name': 'Dr. Sarah Johnson',
                'role': 'Nephrologist',
                'phone_number': '+1-555-0101',
                'email': 'sarah.johnson@hospital.com',
                'specialty': 'Nephrology',
                'is_primary': True,
                'notes': 'Primary nephrologist, specializes in chronic kidney disease and dialysis management'
            },
            {
                'name': 'Maria Garcia',
                'role': 'Dialysis Nurse',
                'phone_number': '+1-555-0102',
                'email': 'maria.garcia@hospital.com',
                'specialty': 'Dialysis Care',
                'is_primary': False,
                'notes': 'Manages dialysis sessions, monitors vital signs during treatment'
            },
            {
                'name': 'David Chen',
                'role': 'Dietitian',
                'phone_number': '+1-555-0103',
                'email': 'david.chen@hospital.com',
                'specialty': 'Renal Nutrition',
                'is_primary': False,
                'notes': 'Provides dietary counseling for kidney disease patients, manages fluid and electrolyte balance'
            },
            {
                'name': 'Emily Rodriguez',
                'role': 'Social Worker',
                'phone_number': '+1-555-0104',
                'email': 'emily.rodriguez@hospital.com',
                'specialty': 'Medical Social Work',
                'is_primary': False,
                'notes': 'Assists with insurance, transportation, and psychosocial support'
            },
            {
                'name': 'Dr. Michael Thompson',
                'role': 'Pharmacist',
                'phone_number': '+1-555-0105',
                'email': 'michael.thompson@hospital.com',
                'specialty': 'Clinical Pharmacy',
                'is_primary': False,
                'notes': 'Reviews medications, manages drug interactions, provides medication counseling'
            }
        ]
        
        # Insert care team members
        inserted_count = 0
        for member_data in care_team_members:
            # Check if member already exists
            existing = db.query(CareTeamMember).filter_by(
                patient_id=patient.id,
                email=member_data['email']
            ).first()
            
            if not existing:
                member = CareTeamMember(
                    patient_id=patient.id,
                    **member_data
                )
                db.add(member)
                inserted_count += 1
                print(f"Added: {member_data['name']} - {member_data['role']}")
            else:
                print(f"Skipped (already exists): {member_data['name']}")
        
        db.commit()
        print(f"\n✓ Successfully inserted {inserted_count} care team members")
        
        # Display all care team members for this patient
        print(f"\nCare team for {patient.name}:")
        print("-" * 80)
        members = db.query(CareTeamMember).filter_by(patient_id=patient.id).all()
        for m in members:
            primary = " [PRIMARY]" if m.is_primary else ""
            print(f"{m.id}. {m.name} - {m.role}{primary}")
            print(f"   {m.specialty} | {m.email} | {m.phone_number}")
            print(f"   Notes: {m.notes}")
            print()
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    seed_care_team()
