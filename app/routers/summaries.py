from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AISummaryResponse
from app.models import AISummary, Conversation
from typing import List

router = APIRouter(prefix="/api/summaries", tags=["summaries"])


@router.get("/conversation/{conversation_id}", response_model=AISummaryResponse)
def get_conversation_summary(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the AI summary for a specific conversation.
    """
    summary = db.query(AISummary).filter(AISummary.conversation_id == conversation_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found for this conversation")
    return summary


@router.get("/patient/{patient_id}", response_model=List[AISummaryResponse])
def get_patient_summaries(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all AI summaries for a specific patient.
    """
    from app.models import Patient
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    summaries = db.query(AISummary).join(Conversation).filter(
        Conversation.patient_id == patient.id
    ).all()
    return summaries


@router.get("/", response_model=List[AISummaryResponse])
def list_summaries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all AI summaries with pagination.
    """
    summaries = db.query(AISummary).offset(skip).limit(limit).all()
    return summaries
