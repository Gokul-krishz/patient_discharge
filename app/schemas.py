from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Patient schemas
class PatientBase(BaseModel):
    patient_id: str
    phone_number: str
    name: str
    medical_context: Optional[str] = None


class PatientCreate(PatientBase):
    care_team_member_ids: Optional[List[int]] = []


class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Care Team schemas
class CareTeamMemberBase(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None
    role: Optional[str] = None


class CareTeamMemberCreate(CareTeamMemberBase):
    pass


class CareTeamMemberResponse(CareTeamMemberBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Conversation schemas
class ConversationBase(BaseModel):
    patient_id: int


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    status: str
    qa_history: Optional[List[dict]] = None
    current_question: Optional[str] = None
    question_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# SMS Log schemas
class SMSLogBase(BaseModel):
    conversation_id: int
    direction: str
    message_text: str
    status: str = "sent"


class SMSLogCreate(SMSLogBase):
    pass


class SMSLogResponse(SMSLogBase):
    id: int
    sent_at: datetime
    received_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# AI Summary schemas
class AISummaryBase(BaseModel):
    conversation_id: int
    summary_text: str
    patient_responses_summary: Optional[str] = None
    sentiment_analysis: Optional[str] = None
    key_insights: Optional[str] = None


class AISummaryResponse(AISummaryBase):
    id: int
    generated_at: datetime
    is_notified: bool
    notified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Trigger SMS endpoint schema
class TriggerSMSRequest(BaseModel):
    patient_id: str


class TriggerSMSResponse(BaseModel):
    conversation_id: int
    message: str
    next_question: Optional[str] = None


# Receive SMS reply endpoint schema
class ReceiveSMSReplyRequest(BaseModel):
    patient_id: str
    message_text: str


class ReceiveSMSReplyResponse(BaseModel):
    conversation_id: int
    message: str
    is_conversation_complete: bool
    next_question: Optional[str] = None
