from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    medical_context = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="patient")
    care_team_associations = relationship("PatientCareTeam", back_populates="patient")


class CareTeamMember(Base):
    __tablename__ = "care_team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    role = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient_associations = relationship("PatientCareTeam", back_populates="care_team_member")


class PatientCareTeam(Base):
    __tablename__ = "patient_care_team"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    care_team_member_id = Column(Integer, ForeignKey("care_team_members.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('patient_id', 'care_team_member_id', name='_patient_care_team_uc'),)
    
    # Relationships
    patient = relationship("Patient", back_populates="care_team_associations")
    care_team_member = relationship("CareTeamMember", back_populates="patient_associations")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="active", index=True)  # active, completed, timeout, no_response
    qa_history = Column(JSON, default=list)  # Stores Q&A pairs as JSON array
    current_question = Column(Text)  # Current question being asked
    question_count = Column(Integer, default=0)  # Number of questions asked so far
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    timeout_at = Column(DateTime(timezone=True))
    
    # Relationships
    patient = relationship("Patient", back_populates="conversations")
    sms_logs = relationship("SMSLog", back_populates="conversation", cascade="all, delete-orphan")
    ai_summary = relationship("AISummary", back_populates="conversation", uselist=False, cascade="all, delete-orphan")


class SMSLog(Base):
    __tablename__ = "sms_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # outbound, inbound
    message_text = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    received_at = Column(DateTime(timezone=True))
    status = Column(String(50), default="sent")  # sent, delivered, failed, received
    
    # Relationships
    conversation = relationship("Conversation", back_populates="sms_logs")


class AISummary(Base):
    __tablename__ = "ai_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary_text = Column(Text, nullable=False)
    patient_responses_summary = Column(Text)
    sentiment_analysis = Column(Text)
    key_insights = Column(Text)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_notified = Column(Boolean, default=False)
    notified_at = Column(DateTime(timezone=True))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="ai_summary")
