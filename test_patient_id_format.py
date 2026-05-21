"""
Test script to verify patient_id formatting in ADT patients API
"""
from models.database import SessionLocal, ADTPatient

def test_patient_id_format():
    """Test the patient_id formatting"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("TESTING PATIENT_ID FORMAT")
        print("="*70)
        
        patients = db.query(ADTPatient).limit(10).all()
        
        print(f"\nFormatted Patient IDs:\n")
        print(f"{'Numeric ID':<12} {'Patient ID':<15} {'Name':<20} {'Status'}")
        print("-" * 70)
        
        for patient in patients:
            patient_id = f'P{patient.id:06d}'
            print(f"{patient.id:<12} {patient_id:<15} {patient.name:<20} {patient.status}")
        
        print("\n" + "="*70)
        print("API Response Example:")
        print("="*70)
        
        if patients:
            example = patients[0]
            print(f"""
{{
    "patient_id": "P{example.id:06d}",
    "id": {example.id},
    "name": "{example.name}",
    "phone_number": "{example.phone_number}",
    "hospital": "{example.hospital}",
    "status": "{example.status}"
}}
""")
        
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_patient_id_format()
