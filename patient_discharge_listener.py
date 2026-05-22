"""
Background listener for patient discharge notifications
Automatically sends SMS when patient is discharged
"""
import json
import time
import select
from datetime import datetime
from models.database import SessionLocal, engine
from services.forms_service import FormsService
from config import Config

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def send_discharge_sms(patient_data):
    """Send SMS to discharged patient"""
    try:
        patient_id = patient_data.get('patient_id')
        name = patient_data.get('name')
        phone = patient_data.get('phone_number')
        hospital = patient_data.get('hospital', 'the hospital')
        
        log(f"Processing discharge for: {name} (ID: {patient_id})")
        
        # Initialize forms service
        forms_service = FormsService(google_form_url=Config.GOOGLE_FORM_URL)
        
        # Send form link via SMS
        result = forms_service.send_form_link(
            phone_number=phone,
            patient_name=name
        )
        
        if result.get('success'):
            log(f"✓ SMS sent successfully to {name} ({phone})")
            log(f"  Message ID: {result.get('message_id')}")
            return True
        else:
            log(f"✗ Failed to send SMS to {name}: {result.get('error')}")
            return False
            
    except Exception as e:
        log(f"✗ Error sending SMS: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def start_listener():
    """Start listening for patient discharge notifications"""
    
    print("=" * 80)
    print("PATIENT DISCHARGE LISTENER - AUTO SMS SENDER")
    print("=" * 80)
    print("Listening for discharged patients...")
    print("SMS will be sent automatically when patient status = 'Discharged'")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)
    
    # Get raw connection for LISTEN
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()
    
    try:
        # Start listening to the channel
        cursor.execute("LISTEN patient_discharged;")
        log("✓ Listening for patient discharge notifications...")
        
        while True:
            # Wait for notification (timeout every 5 seconds to check for interrupts)
            if select.select([raw_conn], [], [], 5) == ([], [], []):
                # Timeout - no notification, just continue
                continue
            
            # Poll for notifications
            raw_conn.poll()
            
            while raw_conn.notifies:
                notify = raw_conn.notifies.pop(0)
                
                try:
                    # Parse the notification payload
                    patient_data = json.loads(notify.payload)
                    action = patient_data.get('action', 'INSERT')
                    
                    log(f"📢 Received notification: {action} - Patient {patient_data.get('name')}")
                    
                    # Send SMS
                    success = send_discharge_sms(patient_data)
                    
                    if success:
                        log(f"✅ Processed successfully!")
                    else:
                        log(f"⚠️  Processing failed - check logs above")
                    
                    print("-" * 80)
                    
                except json.JSONDecodeError as e:
                    log(f"✗ Invalid notification payload: {e}")
                except Exception as e:
                    log(f"✗ Error processing notification: {e}")
                    import traceback
                    traceback.print_exc()
    
    except KeyboardInterrupt:
        log("\nStopping listener...")
        cursor.execute("UNLISTEN patient_discharged;")
        cursor.close()
        raw_conn.close()
        log("✓ Listener stopped")
    
    except Exception as e:
        log(f"✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        cursor.close()
        raw_conn.close()

if __name__ == "__main__":
    start_listener()
