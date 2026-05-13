"""
Conversation Agent Service
Manages structured patient check-in conversations via SMS
"""
from datetime import datetime
from typing import Optional, Dict, Any
from models.database import Patient, Conversation, Message, SessionLocal
from services.sms_service import SMSService

# Ordered list of agent questions sent to the patient
AGENT_QUESTIONS = [
    {
        "key": "feeling_after_discharge",
        "text": "Hi {name}! 👋 I'm your discharge care assistant. How are you feeling after your discharge? (e.g., Good, Fair, Poor)"
    },
    {
        "key": "shortness_of_breath",
        "text": "Are you experiencing any shortness of breath or difficulty breathing? (Reply YES or NO)"
    },
    {
        "key": "dialysis_session",
        "text": "Did you attend your dialysis session as scheduled? (Reply YES, NO, or NOT APPLICABLE)"
    },
    {
        "key": "medications_regular",
        "text": "Are you taking all your medications regularly as prescribed? (Reply YES or NO)"
    },
    {
        "key": "nephrology_followup",
        "text": "Have you scheduled your nephrology follow-up appointment? (Reply YES, NO, or SCHEDULED)"
    },
]


class ConversationAgent:
    """Manages patient check-in conversations"""

    def __init__(self):
        self.sms_service = SMSService()

    def _get_db(self):
        return SessionLocal()

    def get_or_create_patient(self, phone_number: str, name: str, discharge_summary: Optional[Dict] = None) -> Patient:
        """Get existing patient or create a new one"""
        db = self._get_db()
        try:
            patient = db.query(Patient).filter_by(phone_number=phone_number).first()
            if not patient:
                patient = Patient(
                    name=name,
                    phone_number=phone_number,
                    discharge_summary=discharge_summary
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
            elif discharge_summary:
                patient.discharge_summary = discharge_summary
                db.commit()
            return patient
        finally:
            db.close()

    def start_conversation(self, phone_number: str, patient_name: str, discharge_summary: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Start a new check-in conversation with a patient.
        Saves patient, creates conversation, sends first question via SMS.
        """
        db = self._get_db()
        try:
            # Get or create patient
            patient = db.query(Patient).filter_by(phone_number=phone_number).first()
            if not patient:
                patient = Patient(
                    name=patient_name,
                    phone_number=phone_number,
                    discharge_summary=discharge_summary
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)

            # Create new conversation
            conversation = Conversation(
                patient_id=patient.id,
                status='active',
                current_question_index=0
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

            # Send first question
            first_question = AGENT_QUESTIONS[0]
            message_text = first_question['text'].format(name=patient_name)

            sms_result = self.sms_service.send_sms(phone_number, message_text)

            # Store outbound message
            msg = Message(
                conversation_id=conversation.id,
                direction='outbound',
                content=message_text,
                question_key=first_question['key'],
                twilio_sid=sms_result.get('message_sid')
            )
            db.add(msg)
            db.commit()

            return {
                'conversation_id': conversation.id,
                'patient_id': patient.id,
                'patient_name': patient_name,
                'phone_number': phone_number,
                'status': 'started',
                'first_question': message_text,
                'total_questions': len(AGENT_QUESTIONS)
            }
        finally:
            db.close()

    def handle_patient_reply(self, phone_number: str, reply_text: str) -> Dict[str, Any]:
        """
        Process incoming SMS reply from patient.
        Stores response and sends next question or completes conversation.
        """
        db = self._get_db()
        try:
            # Find patient
            patient = db.query(Patient).filter_by(phone_number=phone_number).first()
            if not patient:
                return {'status': 'unknown_patient', 'message': 'No active patient found for this number.'}

            # Find active conversation
            conversation = (
                db.query(Conversation)
                .filter_by(patient_id=patient.id, status='active')
                .order_by(Conversation.created_at.desc())
                .first()
            )
            if not conversation:
                return {'status': 'no_active_conversation', 'message': 'No active conversation found.'}

            current_index = conversation.current_question_index
            answered_question = AGENT_QUESTIONS[current_index]

            # Store patient's inbound reply
            inbound_msg = Message(
                conversation_id=conversation.id,
                direction='inbound',
                content=reply_text,
                question_key=answered_question['key']
            )
            db.add(inbound_msg)

            next_index = current_index + 1

            if next_index < len(AGENT_QUESTIONS):
                # Send next question
                next_question = AGENT_QUESTIONS[next_index]
                message_text = next_question['text'].format(name=patient.name)

                sms_result = self.sms_service.send_sms(phone_number, message_text)

                outbound_msg = Message(
                    conversation_id=conversation.id,
                    direction='outbound',
                    content=message_text,
                    question_key=next_question['key'],
                    twilio_sid=sms_result.get('message_sid')
                )
                db.add(outbound_msg)

                conversation.current_question_index = next_index
                db.commit()

                return {
                    'status': 'next_question_sent',
                    'question_number': next_index + 1,
                    'total_questions': len(AGENT_QUESTIONS),
                    'next_question': message_text
                }
            else:
                # All questions answered - complete the conversation
                farewell = f"Thank you {patient.name}! 🙏 We've recorded all your responses. Your care team will review them. Stay well and reach out if you need anything!"
                self.sms_service.send_sms(phone_number, farewell)

                farewell_msg = Message(
                    conversation_id=conversation.id,
                    direction='outbound',
                    content=farewell,
                    question_key='farewell'
                )
                db.add(farewell_msg)

                conversation.status = 'completed'
                conversation.completed_at = datetime.utcnow()
                db.commit()

                return {
                    'status': 'completed',
                    'message': 'All questions answered. Conversation completed.',
                    'total_questions': len(AGENT_QUESTIONS)
                }
        finally:
            db.close()

    def get_conversation_summary(self, conversation_id: int) -> Dict[str, Any]:
        """
        Get full conversation with all Q&A pairs.
        """
        db = self._get_db()
        try:
            conversation = db.query(Conversation).filter_by(id=conversation_id).first()
            if not conversation:
                return {'error': 'Conversation not found'}

            patient = db.query(Patient).filter_by(id=conversation.patient_id).first()
            messages = db.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()

            # Build structured Q&A pairs
            qa_pairs = []
            outbound = [m for m in messages if m.direction == 'outbound' and m.question_key != 'farewell']
            inbound = [m for m in messages if m.direction == 'inbound']

            for i, q_msg in enumerate(outbound):
                answer = inbound[i].content if i < len(inbound) else "No response yet"
                qa_pairs.append({
                    'question_key': q_msg.question_key,
                    'question': q_msg.content,
                    'answer': answer,
                    'answered_at': inbound[i].timestamp.isoformat() if i < len(inbound) else None
                })

            return {
                'conversation_id': conversation_id,
                'patient_name': patient.name,
                'phone_number': patient.phone_number,
                'status': conversation.status,
                'started_at': conversation.created_at.isoformat(),
                'completed_at': conversation.completed_at.isoformat() if conversation.completed_at else None,
                'progress': f"{len(inbound)}/{len(AGENT_QUESTIONS)} questions answered",
                'responses': qa_pairs
            }
        finally:
            db.close()

    def get_all_conversations(self, phone_number: Optional[str] = None) -> list:
        """Get all conversations, optionally filtered by patient phone number"""
        db = self._get_db()
        try:
            query = db.query(Conversation)
            if phone_number:
                patient = db.query(Patient).filter_by(phone_number=phone_number).first()
                if patient:
                    query = query.filter_by(patient_id=patient.id)
            conversations = query.order_by(Conversation.created_at.desc()).all()

            results = []
            for conv in conversations:
                patient = db.query(Patient).filter_by(id=conv.patient_id).first()
                total_replies = db.query(Message).filter_by(
                    conversation_id=conv.id, direction='inbound'
                ).count()
                results.append({
                    'conversation_id': conv.id,
                    'patient_name': patient.name,
                    'phone_number': patient.phone_number,
                    'status': conv.status,
                    'progress': f"{total_replies}/{len(AGENT_QUESTIONS)} questions answered",
                    'started_at': conv.created_at.isoformat(),
                    'completed_at': conv.completed_at.isoformat() if conv.completed_at else None
                })
            return results
        finally:
            db.close()
