"""
Create PostgreSQL trigger to automatically send SMS when patient is discharged
Uses PostgreSQL NOTIFY/LISTEN for real-time event handling
"""
from sqlalchemy import text
from models.database import engine

def create_discharge_trigger():
    """
    Create database trigger that fires when:
    1. New patient is inserted with status='Discharged'
    2. Existing patient status changes to 'Discharged'
    """
    
    print("Creating discharge notification trigger...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Create function that sends notification
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION notify_patient_discharge()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- Only notify if patient is discharged and follow_up is Pending
                    IF NEW.status = 'Discharged' AND (NEW.follow_up = 'Pending' OR NEW.follow_up IS NULL) THEN
                        -- Send notification with patient details as JSON
                        PERFORM pg_notify(
                            'patient_discharged',
                            json_build_object(
                                'patient_id', NEW.id,
                                'name', NEW.name,
                                'phone_number', NEW.phone_number,
                                'hospital', NEW.hospital,
                                'discharge_date', NEW.discharge_date,
                                'action', TG_OP
                            )::text
                        );
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """))
            print("✓ Created notification function")
            
            # Drop existing trigger if exists
            conn.execute(text("""
                DROP TRIGGER IF EXISTS patient_discharge_trigger ON patients;
            """))
            
            # Create trigger for INSERT
            conn.execute(text("""
                CREATE TRIGGER patient_discharge_trigger
                AFTER INSERT OR UPDATE OF status
                ON patients
                FOR EACH ROW
                EXECUTE FUNCTION notify_patient_discharge();
            """))
            print("✓ Created discharge trigger")
            
            trans.commit()
            print("\n✅ Discharge trigger created successfully!")
            print("\nTrigger will fire when:")
            print("  1. New patient inserted with status='Discharged'")
            print("  2. Patient status updated to 'Discharged'")
            print("  3. Patient follow_up is 'Pending' or NULL")
            print("\nNext step: Run the listener to process notifications")
            print("  python patient_discharge_listener.py")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Error: {str(e)}")
            raise

if __name__ == "__main__":
    create_discharge_trigger()
