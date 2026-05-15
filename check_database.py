"""
Check the database for existing data.
"""
import psycopg2
from app.config import settings

def check_database():
    """Check what's in the database."""
    
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Check patients
        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()
        print(f"Patients ({len(patients)}):")
        for p in patients:
            print(f"  ID: {p[0]}, Patient ID: {p[1]}, Phone: {p[2]}, Name: {p[3]}")
        
        # Check conversations
        cursor.execute("SELECT id, patient_id, status, question_count, started_at FROM conversations")
        conversations = cursor.fetchall()
        print(f"\nConversations ({len(conversations)}):")
        for c in conversations:
            print(f"  ID: {c[0]}, Patient ID: {c[1]}, Status: {c[2]}, Questions: {c[3]}, Started: {c[4]}")
        
        # Check SMS logs
        cursor.execute("SELECT id, conversation_id, direction, message_text, status FROM sms_logs LIMIT 10")
        sms_logs = cursor.fetchall()
        print(f"\nSMS Logs (last 10):")
        for s in sms_logs:
            print(f"  ID: {s[0]}, Conv ID: {s[1]}, Direction: {s[2]}, Status: {s[4]}")
            print(f"    Message: {s[3][:50]}...")
        
        # Check AI summaries
        cursor.execute("SELECT id, conversation_id, summary_text FROM ai_summaries")
        summaries = cursor.fetchall()
        print(f"\nAI Summaries ({len(summaries)}):")
        for s in summaries:
            print(f"  ID: {s[0]}, Conv ID: {s[1]}")
            print(f"    Summary: {s[2][:50]}...")
            
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_database()
