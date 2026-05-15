from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SMSLogResponse
from app.models import SMSLog, Conversation
from typing import List

router = APIRouter(prefix="/api/logs", tags=["sms-logs"])


@router.get("/conversation/{conversation_id}", response_model=List[SMSLogResponse])
def get_conversation_sms_logs(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all SMS logs for a specific conversation.
    """
    logs = db.query(SMSLog).filter(
        SMSLog.conversation_id == conversation_id
    ).order_by(SMSLog.sent_at).all()
    return logs


@router.get("/patient/{patient_id}", response_model=List[SMSLogResponse])
def get_patient_sms_logs(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all SMS logs for a specific patient.
    """
    from app.models import Patient
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    logs = db.query(SMSLog).join(Conversation).filter(
        Conversation.patient_id == patient.id
    ).order_by(SMSLog.sent_at).all()
    return logs


@router.get("/", response_model=List[SMSLogResponse])
def list_sms_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all SMS logs with pagination.
    """
    logs = db.query(SMSLog).offset(skip).limit(limit).order_by(SMSLog.sent_at.desc()).all()
    return logs
