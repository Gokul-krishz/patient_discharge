"""
Test script for ADT patient to Patient table workflow
Tests the send-form-link endpoint with patient_id
"""
from models.database import SessionLocal, ADTPatient, Patient, FormResponse
from datetime import datetime

def test_adt_workflow():
    """Test the complete ADT workflow"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("TESTING ADT PATIENT WORKFLOW")
        print("="*70)
        
        # 1. Check ADT patients with 'Admitted' status
        print("\n1. Fetching ADT patients with 'Admitted' status...")
        adt_patients = db.query(ADTPatient).filter_by(status='Admitted').all()
        
        if not adt_patients:
            print("   ❌ No ADT patients with 'Admitted' status found")
            return
        
        print(f"   ✅ Found {len(adt_patients)} ADT patients with 'Admitted' status")
        
        # Display first 3 patients
        print("\n   Sample ADT Patients:")
        for i, patient in enumerate(adt_patients[:3], 1):
            print(f"   {i}. ID: {patient.id}, Name: {patient.name}, Phone: {patient.phone_number}, Status: {patient.status}")
        
        # 2. Select first patient for testing
        test_patient = adt_patients[0]
        print(f"\n2. Selected test patient:")
        print(f"   ID: {test_patient.id}")
        print(f"   Name: {test_patient.name}")
        print(f"   Phone: {test_patient.phone_number}")
        print(f"   Hospital: {test_patient.hospital}")
        print(f"   Status: {test_patient.status}")
        
        # 3. Check if patient exists in Patients table
        print(f"\n3. Checking if patient exists in Patients table...")
        existing_patient = db.query(Patient).filter_by(phone_number=test_patient.phone_number).first()
        if existing_patient:
            print(f"   ⚠️  Patient already exists in Patients table")
            print(f"   Status: {existing_patient.status}, Follow-up: {existing_patient.follow_up}")
        else:
            print(f"   ✅ Patient does not exist in Patients table (will be created)")
        
        # 4. Instructions for API testing
        print("\n" + "="*70)
        print("API TEST INSTRUCTIONS")
        print("="*70)
        print("\nTo test the workflow, send a POST request to:")
        print("   POST http://localhost:5000/api/forms/send-form-link")
        print("\nWith JSON body:")
        print(f"""
{{
    "patient_id": {test_patient.id}
}}
""")
        
        print("\nExpected workflow:")
        print("   1. ✅ ADT patient status updated: 'Admitted' → 'Discharged'")
        print("   2. ✅ ADT patient discharge_date set to current timestamp")
        print("   3. ✅ Patient record created/updated in Patients table")
        print("   4. ✅ Patient status set to 'Discharged'")
        print("   5. ✅ Patient follow_up set to 'Link Sent'")
        print("   6. ✅ SMS sent with Google Form link")
        print("   7. ✅ FormResponse record created")
        
        print("\nWhen patient submits the form:")
        print("   8. ✅ Patient follow_up updated: 'Link Sent' → 'Completed'")
        
        print("\n" + "="*70)
        print("CURL COMMAND FOR TESTING")
        print("="*70)
        print(f"""
curl -X POST http://localhost:5000/api/forms/send-form-link \\
  -H "Content-Type: application/json" \\
  -d '{{"patient_id": {test_patient.id}}}'
""")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def check_workflow_results(patient_id: int):
    """Check the results after running the workflow"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("CHECKING WORKFLOW RESULTS")
        print("="*70)
        
        # Check ADT patient
        adt_patient = db.query(ADTPatient).filter_by(id=patient_id).first()
        if adt_patient:
            print(f"\n1. ADT Patient (ID: {patient_id}):")
            print(f"   Name: {adt_patient.name}")
            print(f"   Status: {adt_patient.status}")
            print(f"   Discharge Date: {adt_patient.discharge_date}")
            
            # Check Patient table
            patient = db.query(Patient).filter_by(phone_number=adt_patient.phone_number).first()
            if patient:
                print(f"\n2. Patient Record:")
                print(f"   ID: {patient.id}")
                print(f"   Name: {patient.name}")
                print(f"   Status: {patient.status}")
                print(f"   Follow-up: {patient.follow_up}")
                print(f"   Hospital: {patient.hospital}")
                
                # Check FormResponse
                form_response = db.query(FormResponse).filter_by(patient_phone=patient.phone_number).order_by(FormResponse.created_at.desc()).first()
                if form_response:
                    print(f"\n3. Form Response:")
                    print(f"   ID: {form_response.id}")
                    print(f"   Link Sent At: {form_response.form_link_sent_at}")
                    print(f"   Submitted At: {form_response.submitted_at or 'Not submitted yet'}")
                else:
                    print(f"\n3. ❌ No FormResponse found")
            else:
                print(f"\n2. ❌ Patient not found in Patients table")
        else:
            print(f"\n❌ ADT Patient with ID {patient_id} not found")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        if len(sys.argv) > 2:
            patient_id = int(sys.argv[2])
            check_workflow_results(patient_id)
        else:
            print("Usage: python test_adt_workflow.py check <patient_id>")
    else:
        test_adt_workflow()
