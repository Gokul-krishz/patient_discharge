"""
Seed sample patient data for testing the patients API
"""
from datetime import datetime, timedelta
from models.database import Patient, FormResponse, SessionLocal

def seed_sample_data():
    """Create sample patients with different statuses"""
    
    db = SessionLocal()
    
    try:
        # Sample patients data
        patients_data = [
            {
                'name': 'Ramesh Kumar',
                'phone_number': '+919876543210',
                'hospital': 'Apollo Hospitals',
                'admission_date': datetime(2024, 5, 12),
                'discharge_date': datetime(2024, 5, 18),
                'status': 'Discharged'
            },
            {
                'name': 'Sunita Devi',
                'phone_number': '+919123456780',
                'hospital': 'Fortis Hospital',
                'admission_date': datetime(2024, 5, 15),
                'discharge_date': None,
                'status': 'Admitted'
            },
            {
                'name': 'Vijay Sharma',
                'phone_number': '+919988776655',
                'hospital': 'Max Healthcare',
                'admission_date': datetime(2024, 5, 10),
                'discharge_date': datetime(2024, 5, 16),
                'status': 'Discharged'
            },
            {
                'name': 'Anita Patel',
                'phone_number': '+919090909090',
                'hospital': 'Narayana Health',
                'admission_date': datetime(2024, 5, 8),
                'discharge_date': None,
                'status': 'Admitted'
            },
            {
                'name': 'Mohammed Ali',
                'phone_number': '+918888888888',
                'hospital': 'Apollo Hospitals',
                'admission_date': datetime(2024, 5, 5),
                'discharge_date': datetime(2024, 5, 11),
                'status': 'Discharged'
            }
        ]
        
        print("Creating sample patients...")
        
        for patient_data in patients_data:
            # Check if patient already exists
            existing = db.query(Patient).filter_by(phone_number=patient_data['phone_number']).first()
            
            if existing:
                print(f"  - {patient_data['name']} already exists, updating...")
                existing.hospital = patient_data['hospital']
                existing.admission_date = patient_data['admission_date']
                existing.discharge_date = patient_data['discharge_date']
                existing.status = patient_data['status']
                patient = existing
            else:
                print(f"  + Creating {patient_data['name']}...")
                patient = Patient(**patient_data)
                db.add(patient)
                db.flush()  # Get the patient ID
            
            # Create form responses for discharged patients
            if patient_data['status'] == 'Discharged':
                # Check if form response exists
                existing_form = db.query(FormResponse).filter_by(patient_phone=patient_data['phone_number']).first()
                
                if not existing_form:
                    # Some patients have link sent
                    if patient_data['name'] in ['Ramesh Kumar', 'Vijay Sharma']:
                        form_response = FormResponse(
                            patient_id=patient.id,
                            patient_phone=patient_data['phone_number'],
                            patient_name=patient_data['name'],
                            form_link_sent_at=datetime.utcnow() - timedelta(days=1),
                            submitted_at=None
                        )
                        db.add(form_response)
                        print(f"    → Form link sent (pending)")
                    
                    # One patient completed the form
                    if patient_data['name'] == 'Mohammed Ali':
                        form_response = FormResponse(
                            patient_id=patient.id,
                            patient_phone=patient_data['phone_number'],
                            patient_name=patient_data['name'],
                            form_link_sent_at=datetime.utcnow() - timedelta(days=2),
                            submitted_at=datetime.utcnow() - timedelta(hours=12),
                            recently_discharged='Yes, 6 days ago',
                            medication_changes='Yes, new blood pressure medication',
                            current_symptoms='Mild fatigue',
                            care_team_notes='Recovering well',
                            contact_request='No',
                            summary='Patient was discharged 6 days ago with new blood pressure medication. Reports mild fatigue but is recovering well.'
                        )
                        db.add(form_response)
                        print(f"    → Form completed")
        
        db.commit()
        print("\n✅ Sample data created successfully!")
        
        # Show summary
        total_patients = db.query(Patient).count()
        discharged = db.query(Patient).filter_by(status='Discharged').count()
        admitted = db.query(Patient).filter_by(status='Admitted').count()
        
        print(f"\n📊 Summary:")
        print(f"  Total Patients: {total_patients}")
        print(f"  Discharged: {discharged}")
        print(f"  Admitted: {admitted}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_sample_data()
