from sqlalchemy.orm import Session
from app.models import (
    Patient, Conversation, SMSLog, AISummary
)
from app.schemas import (
    TriggerSMSRequest, TriggerSMSResponse, ReceiveSMSReplyRequest, ReceiveSMSReplyResponse
)
from app.services.ai_service import ai_service
from app.services.twilio_service import twilio_service
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.config import settings


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
    
    def trigger_sms_conversation(self, request: TriggerSMSRequest) -> TriggerSMSResponse:
        """
        Start a new SMS conversation for a patient.
        AI generates the first question based on patient context.
        """
        # Get patient
        patient = self.db.query(Patient).filter(Patient.patient_id == request.patient_id).first()
        if not patient:
            raise ValueError(f"Patient with ID {request.patient_id} not found")
        
        # Check if patient has an active conversation
        active_conversation = self.db.query(Conversation).filter(
            Conversation.patient_id == patient.id,
            Conversation.status == "active"
        ).first()
        
        if active_conversation:
            # Send the current question via Twilio if it exists
            if active_conversation.current_question and twilio_service.is_configured():
                twilio_result = twilio_service.send_sms(patient.phone_number, active_conversation.current_question)
                if not twilio_result["success"]:
                    print(f"Failed to send SMS via Twilio: {twilio_result.get('error', 'Unknown error')}")
            return TriggerSMSResponse(
                conversation_id=active_conversation.id,
                message="Patient already has an active conversation",
                next_question=active_conversation.current_question
            )
        
        # Create new conversation
        conversation = Conversation(
            patient_id=patient.id,
            status="active",
            qa_history=[],
            question_count=0
        )
        self.db.add(conversation)
        self.db.flush()
        
        # Generate first question using AI
        patient_context = f"Patient Name: {patient.name}, Patient ID: {patient.patient_id}, Medical Context: {patient.medical_context or 'Not provided'}"
        first_question = ai_service.generate_first_question(patient_context)
        
        # Update conversation with first question
        conversation.current_question = first_question
        conversation.question_count = 1
        
        # Log outbound SMS
        sms_log = SMSLog(
            conversation_id=conversation.id,
            direction="outbound",
            message_text=first_question,
            status="sent"
        )
        self.db.add(sms_log)
        
        self.db.commit()
        
        # Send SMS via Twilio
        if twilio_service.is_configured():
            twilio_result = twilio_service.send_sms(patient.phone_number, first_question)
            if not twilio_result["success"]:
                print(f"Failed to send SMS via Twilio: {twilio_result.get('error', 'Unknown error')}")
        else:
            print("Twilio not configured. SMS not sent. Please check your .env file.")
        
        return TriggerSMSResponse(
            conversation_id=conversation.id,
            message="Conversation started successfully",
            next_question=first_question
        )
    
    def receive_sms_reply(self, request: ReceiveSMSReplyRequest) -> ReceiveSMSReplyResponse:
        """
        Process an incoming SMS reply from a patient.
        Validates response, saves Q&A, and generates next question if needed.
        """
        # Get patient
        patient = self.db.query(Patient).filter(Patient.patient_id == request.patient_id).first()
        if not patient:
            raise ValueError(f"Patient with ID {request.patient_id} not found")
        
        # Get active conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.patient_id == patient.id,
            Conversation.status == "active"
        ).first()
        
        if not conversation:
            raise ValueError(f"No active conversation found for patient {request.patient_id}")
        
        if not conversation.current_question:
            raise ValueError("No current question to answer")
        
        # Validate response using AI
        validation_result = ai_service.validate_response(conversation.current_question, request.message_text)
        
        # Log inbound SMS
        sms_log = SMSLog(
            conversation_id=conversation.id,
            direction="inbound",
            message_text=request.message_text,
            status="received",
            received_at=datetime.utcnow()
        )
        self.db.add(sms_log)
        
        if validation_result["is_valid"]:
            # Save Q&A pair to history
            qa_pair = {
                "question": conversation.current_question,
                "response": request.message_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if conversation.qa_history is None:
                conversation.qa_history = []
            conversation.qa_history.append(qa_pair)
            
            # Clear current question
            conversation.current_question = None
            
            # Commit Q&A pair immediately to ensure it's saved
            self.db.commit()
            
            # Generate next question using AI
            patient_context = f"Patient Name: {patient.name}, Patient ID: {patient.patient_id}, Medical Context: {patient.medical_context or 'Not provided'}"
            next_question, should_continue = ai_service.generate_next_question(
                patient_context,
                conversation.qa_history
            )
            
            if should_continue and next_question:
                # Continue conversation
                conversation.current_question = next_question
                conversation.question_count += 1
                
                # Log outbound SMS
                sms_log_next = SMSLog(
                    conversation_id=conversation.id,
                    direction="outbound",
                    message_text=next_question,
                    status="sent"
                )
                self.db.add(sms_log_next)
                
                self.db.commit()
                
                # Send SMS via Twilio
                if twilio_service.is_configured():
                    twilio_result = twilio_service.send_sms(patient.phone_number, next_question)
                    if not twilio_result["success"]:
                        print(f"Failed to send SMS via Twilio: {twilio_result.get('error', 'Unknown error')}")
                
                return ReceiveSMSReplyResponse(
                    conversation_id=conversation.id,
                    message="Response received and validated",
                    is_conversation_complete=False,
                    next_question=next_question
                )
            else:
                # Complete conversation
                self.complete_conversation(conversation.id)
                self.db.commit()
                
                return ReceiveSMSReplyResponse(
                    conversation_id=conversation.id,
                    message="Response received. Conversation complete.",
                    is_conversation_complete=True,
                    next_question=None
                )
        else:
            # Response invalid, rephrase question and ask again
            if validation_result["should_rephrase"]:
                rephrased = ai_service.rephrase_question(conversation.current_question)
                conversation.current_question = rephrased
                
                # Log outbound SMS with rephrased question
                sms_log_rephrase = SMSLog(
                    conversation_id=conversation.id,
                    direction="outbound",
                    message_text=rephrased,
                    status="sent"
                )
                self.db.add(sms_log_rephrase)
                self.db.commit()
                
                # Send SMS via Twilio
                if twilio_service.is_configured():
                    twilio_result = twilio_service.send_sms(patient.phone_number, rephrased)
                    if not twilio_result["success"]:
                        print(f"Failed to send SMS via Twilio: {twilio_result.get('error', 'Unknown error')}")
                
                return ReceiveSMSReplyResponse(
                    conversation_id=conversation.id,
                    message="Response was unclear, question rephrased",
                    is_conversation_complete=False,
                    next_question=rephrased
                )
            else:
                # Just ask the same question again
                sms_log_retry = SMSLog(
                    conversation_id=conversation.id,
                    direction="outbound",
                    message_text=conversation.current_question,
                    status="sent"
                )
                self.db.add(sms_log_retry)
                self.db.commit()
                
                # Send SMS via Twilio
                if twilio_service.is_configured():
                    twilio_result = twilio_service.send_sms(patient.phone_number, conversation.current_question)
                    if not twilio_result["success"]:
                        print(f"Failed to send SMS via Twilio: {twilio_result.get('error', 'Unknown error')}")
                
                return ReceiveSMSReplyResponse(
                    conversation_id=conversation.id,
                    message="Response was unclear, please try again",
                    is_conversation_complete=False,
                    next_question=conversation.current_question
                )
    
    def complete_conversation(self, conversation_id: int):
        """
        Complete a conversation and generate AI summary.
        """
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")

        patient = self.db.query(Patient).filter(Patient.id == conversation.patient_id).first()

        conversation.status = "completed"
        conversation.completed_at = datetime.utcnow()
        conversation.current_question = None

        # Generate AI summary
        summary_data = self._prepare_summary_data(conversation_id)
        ai_result = ai_service.generate_summary(summary_data)

        # Save summary
        ai_summary = AISummary(
            conversation_id=conversation_id,
            summary_text=ai_result["summary_text"],
            patient_responses_summary=ai_result["patient_responses_summary"],
            sentiment_analysis=ai_result["sentiment_analysis"],
            key_insights=ai_result["key_insights"]
        )
        self.db.add(ai_summary)

        # Generate and send thank you message
        thank_you_message = f"Thank you {patient.name}. Your care team appreciates your responses. Take care!"

        # Log thank you SMS
        sms_log = SMSLog(
            conversation_id=conversation_id,
            direction="outbound",
            message_text=thank_you_message,
            status="sent"
        )
        self.db.add(sms_log)
        self.db.commit()

        # Send thank you SMS via Twilio
        if twilio_service.is_configured():
            twilio_result = twilio_service.send_sms(patient.phone_number, thank_you_message)
            if not twilio_result["success"]:
                print(f"Failed to send thank you SMS via Twilio: {twilio_result.get('error', 'Unknown error')}")
    
    def timeout_conversation(self, conversation_id: int):
        """
        Mark a conversation as timed out (no response within timeout period).
        """
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        conversation.status = "timeout"
        conversation.timeout_at = datetime.utcnow()
        conversation.current_question = None
        
        # Generate summary indicating no response
        summary_data = self._prepare_summary_data(conversation_id)
        ai_result = ai_service.generate_summary(summary_data)

        ai_summary = AISummary(
            conversation_id=conversation_id,
            summary_text=f"Conversation timed out after {settings.RESPONSE_TIMEOUT_HOURS} hours with no response. " + ai_result["summary_text"],
            patient_responses_summary=ai_result["patient_responses_summary"],
            sentiment_analysis=ai_result["sentiment_analysis"],
            key_insights=ai_result["key_insights"] + " Patient did not respond within the timeout period."
        )
        self.db.add(ai_summary)
    
    def _prepare_summary_data(self, conversation_id: int) -> Dict:
        """
        Prepare conversation data for AI summary generation.
        """
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        patient = self.db.query(Patient).filter(Patient.id == conversation.patient_id).first()
        
        # Get Q&A pairs from JSON history
        qa_pairs = conversation.qa_history or []
        
        return {
            "qa_pairs": qa_pairs,
            "patient_context": f"Patient Name: {patient.name}, Patient ID: {patient.patient_id}, Medical Context: {patient.medical_context or 'Not provided'}"
        }
    
    def check_timeouts(self):
        """
        Check for conversations that have timed out and mark them as such.
        This should be called periodically (e.g., by a scheduled task).
        """
        timeout_threshold = datetime.utcnow() - timedelta(hours=settings.RESPONSE_TIMEOUT_HOURS)
        
        # Find active conversations
        timed_out_conversations = self.db.query(Conversation).filter(
            Conversation.status == "active"
        ).all()
        
        for conversation in timed_out_conversations:
            # Get the last outbound SMS
            last_sms = self.db.query(SMSLog).filter(
                SMSLog.conversation_id == conversation.id,
                SMSLog.direction == "outbound"
            ).order_by(SMSLog.sent_at.desc()).first()
            
            if last_sms and last_sms.sent_at and last_sms.sent_at < timeout_threshold:
                # Check if there's a pending question (no response received)
                if conversation.current_question:
                    self.timeout_conversation(conversation.id)
