"""
Action Logger Service
Simple service to log patient actions for audit trail and workflow visualization
"""
from datetime import datetime
from sqlalchemy import text
from models.database import engine
import json


class ActionLogger:
    """Service to log patient actions"""
    
    @staticmethod
    def log_action(patient_id: int, action: str, metadata: dict = None):
        """
        Log a patient action
        
        Args:
            patient_id: ID of the patient
            action: Action description (e.g., "SMS Sent", "Form Link Sent", "Conversation Started")
            metadata: Additional data (phone, message content, form URL, etc.)
        
        Returns:
            int: ID of the created log entry
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO patient_action_logs (patient_id, action, metadata, timestamp)
                    VALUES (:patient_id, :action, :metadata, :timestamp)
                    RETURNING id;
                """), {
                    'patient_id': patient_id,
                    'action': action,
                    'metadata': json.dumps(metadata) if metadata else None,
                    'timestamp': datetime.now()
                })
                conn.commit()
                log_id = result.scalar()
                print(f"[ACTION LOG] Patient {patient_id}: {action}")
                return log_id
        except Exception as e:
            print(f"[ACTION LOG ERROR] Failed to log action: {str(e)}")
            return None
    
    @staticmethod
    def get_patient_logs(patient_id: int, limit: int = 50):
        """
        Get action logs for a specific patient
        
        Args:
            patient_id: ID of the patient
            limit: Maximum number of logs to return
        
        Returns:
            list: List of log entries
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, action, metadata, timestamp
                    FROM patient_action_logs
                    WHERE patient_id = :patient_id
                    ORDER BY timestamp DESC
                    LIMIT :limit;
                """), {'patient_id': patient_id, 'limit': limit})
                
                logs = []
                for row in result:
                    metadata = row[2]
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    elif metadata is None:
                        metadata = {}
                    
                    logs.append({
                        'id': row[0],
                        'action': row[1],
                        'metadata': metadata,
                        'timestamp': row[3].isoformat() if row[3] else None
                    })
                return logs
        except Exception as e:
            print(f"[ACTION LOG ERROR] Failed to get logs: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_logs(limit: int = 100):
        """
        Get recent action logs across all patients
        
        Args:
            limit: Maximum number of logs to return
        
        Returns:
            list: List of log entries with patient info
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        pal.id,
                        pal.patient_id,
                        p.name as patient_name,
                        p.phone_number,
                        pal.action,
                        pal.metadata,
                        pal.timestamp
                    FROM patient_action_logs pal
                    LEFT JOIN patients p ON pal.patient_id = p.id
                    ORDER BY pal.timestamp DESC
                    LIMIT :limit;
                """), {'limit': limit})
                
                logs = []
                for row in result:
                    metadata = row[5]
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    elif metadata is None:
                        metadata = {}
                    
                    logs.append({
                        'id': row[0],
                        'patient_id': row[1],
                        'patient_name': row[2],
                        'phone_number': row[3],
                        'action': row[4],
                        'metadata': metadata,
                        'timestamp': row[6].isoformat() if row[6] else None
                    })
                return logs
        except Exception as e:
            print(f"[ACTION LOG ERROR] Failed to get recent logs: {str(e)}")
            return []
    
    @staticmethod
    def get_logs_by_action(action: str, limit: int = 50):
        """
        Get logs filtered by action type
        
        Args:
            action: Action type to filter by
            limit: Maximum number of logs to return
        
        Returns:
            list: List of log entries
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        pal.id,
                        pal.patient_id,
                        p.name as patient_name,
                        pal.action,
                        pal.metadata,
                        pal.timestamp
                    FROM patient_action_logs pal
                    LEFT JOIN patients p ON pal.patient_id = p.id
                    WHERE pal.action = :action
                    ORDER BY pal.timestamp DESC
                    LIMIT :limit;
                """), {'action': action, 'limit': limit})
                
                logs = []
                for row in result:
                    metadata = row[4]
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    elif metadata is None:
                        metadata = {}
                    
                    logs.append({
                        'id': row[0],
                        'patient_id': row[1],
                        'patient_name': row[2],
                        'action': row[3],
                        'metadata': metadata,
                        'timestamp': row[5].isoformat() if row[5] else None
                    })
                return logs
        except Exception as e:
            print(f"[ACTION LOG ERROR] Failed to get logs by action: {str(e)}")
            return []


# Example usage and common action types
ACTION_TYPES = {
    'SMS_SENT': 'SMS Sent',
    'FORM_LINK_SENT': 'Form Link Sent',
    'CONVERSATION_STARTED': 'Conversation Started',
    'CONVERSATION_COMPLETED': 'Conversation Completed',
    'FORM_SUBMITTED': 'Form Submitted',
    'AI_SUMMARY_GENERATED': 'AI Summary Generated',
    'PATIENT_CREATED': 'Patient Created',
    'PATIENT_UPDATED': 'Patient Updated',
    'CARE_TEAM_ASSIGNED': 'Care Team Assigned',
    'FOLLOW_UP_SCHEDULED': 'Follow-up Scheduled',
    'NOTIFICATION_SENT': 'Notification Sent'
}
