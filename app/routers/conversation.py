from fastapi import APIRouter, Depends, HTTPException, Form, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    TriggerSMSRequest, TriggerSMSResponse,
    ReceiveSMSReplyRequest, ReceiveSMSReplyResponse,
    ConversationResponse
)
from app.services.conversation_service import ConversationService
from typing import List
from app.models import Patient

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("/trigger", response_model=TriggerSMSResponse)
def trigger_sms_conversation(
    request: TriggerSMSRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger a new SMS conversation for a patient.
    AI generates the first question based on patient context.
    """
    try:
        service = ConversationService(db)
        return service.trigger_sms_conversation(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/reply", response_model=ReceiveSMSReplyResponse)
def receive_sms_reply(
    request: ReceiveSMSReplyRequest,
    db: Session = Depends(get_db)
):
    """
    Process an incoming SMS reply from a patient.
    This endpoint validates the response and generates the next question using AI.
    """
    try:
        service = ConversationService(db)
        return service.receive_sms_reply(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific conversation including Q&A history.
    """
    from app.models import Conversation
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/patient/{patient_id}", response_model=List[ConversationResponse])
def get_patient_conversations(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all conversations for a specific patient.
    """
    from app.models import Conversation
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    conversations = db.query(Conversation).filter(
        Conversation.patient_id == patient.id
    ).all()
    return conversations


@router.post("/webhook/twilio")
def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Twilio webhook endpoint to receive incoming SMS messages from patients.
    Twilio sends the message to this endpoint when a patient replies.
    """
    try:
        # Find patient by phone number (Twilio sends phone in format +1234567890)
        phone_number = From
        patient = db.query(Patient).filter(Patient.phone_number == phone_number).first()

        if not patient:
            # Return TwiML response to acknowledge receipt even if patient not found
            return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")

        # Process the reply using existing logic
        request = ReceiveSMSReplyRequest(
            patient_id=patient.patient_id,
            message_text=Body
        )
        service = ConversationService(db)
        service.receive_sms_reply(request)

        # Return TwiML response to acknowledge receipt
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")

    except Exception as e:
        # Always return TwiML response even on error to avoid Twilio retries
        print(f"Error processing Twilio webhook: {str(e)}")
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
