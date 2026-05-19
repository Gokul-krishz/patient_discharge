"""
Update follow_up status for existing patients based on their form responses
"""
from models.database import Patient, FormResponse, SessionLocal

def update_follow_up_status():
    """Update follow_up status for all existing patients"""
    
    db = SessionLocal()
    
    try:
        print("Updating follow_up status for existing patients...")
        
        patients = db.query(Patient).all()
        
        for patient in patients:
            # Get latest form response
            latest_form = (
                db.query(FormResponse)
                .filter_by(patient_phone=patient.phone_number)
                .order_by(FormResponse.created_at.desc())
                .first()
            )
            
            if latest_form:
                if latest_form.submitted_at:
                    patient.follow_up = 'Completed'
                    print(f"  ✓ {patient.name}: Completed")
                elif latest_form.form_link_sent_at:
                    patient.follow_up = 'Link Sent'
                    print(f"  ✓ {patient.name}: Link Sent")
                else:
                    patient.follow_up = 'Pending'
                    print(f"  ✓ {patient.name}: Pending")
            else:
                patient.follow_up = 'Pending'
                print(f"  ✓ {patient.name}: Pending (no form response)")
        
        db.commit()
        print("\n✅ Follow-up status updated successfully!")
        
        # Show summary
        pending = db.query(Patient).filter_by(follow_up='Pending').count()
        link_sent = db.query(Patient).filter_by(follow_up='Link Sent').count()
        completed = db.query(Patient).filter_by(follow_up='Completed').count()
        
        print(f"\n📊 Summary:")
        print(f"  Pending: {pending}")
        print(f"  Link Sent: {link_sent}")
        print(f"  Completed: {completed}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_follow_up_status()
