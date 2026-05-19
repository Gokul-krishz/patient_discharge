"""
SQLAlchemy database models for patient conversations
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text,
    DateTime, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from config import Config


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    hospital = Column(String(255), nullable=True)
    admission_date = Column(DateTime, nullable=True)
    discharge_date = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=True)  # 'Admitted', 'Discharged'
    follow_up = Column(String(50), nullable=True)  # 'Pending', 'Link Sent', 'Completed'
    discharge_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversations = relationship('Conversation', back_populates='patient')
    care_team_members = relationship('CareTeamMember', back_populates='patient')
    form_responses = relationship('FormResponse', back_populates='patient')


class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    status = Column(String(50), default='active')  # active, completed, paused
    current_question_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    patient = relationship('Patient', back_populates='conversations')
    messages = relationship('Message', back_populates='conversation')


class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    direction = Column(String(10), nullable=False)  # 'outbound' or 'inbound'
    content = Column(Text, nullable=False)
    question_key = Column(String(100), nullable=True)  # which agent question this maps to
    twilio_sid = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship('Conversation', back_populates='messages')


class FormResponse(Base):
    __tablename__ = 'form_responses'

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True)
    patient_phone = Column(String(20), nullable=False)
    patient_name = Column(String(255), nullable=True)
    form_link_sent_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    # Individual health question answers
    recently_discharged = Column(Text, nullable=True)
    medication_changes = Column(Text, nullable=True)
    current_symptoms = Column(Text, nullable=True)
    care_team_notes = Column(Text, nullable=True)
    contact_request = Column(Text, nullable=True)
    # Full raw response JSON from Google Forms
    raw_responses = Column(JSON, nullable=True)
    # AI-generated summary
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    patient = relationship('Patient', back_populates='form_responses')


class CareTeamMember(Base):
    __tablename__ = 'care_team_members'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)  # e.g., 'Nephrologist', 'Nurse', 'Dietitian'
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    specialty = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False)  # Primary care team member
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    patient = relationship('Patient', back_populates='care_team_members')


# Database engine and session setup
engine = create_engine(Config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
