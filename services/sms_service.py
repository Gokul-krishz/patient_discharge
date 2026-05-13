"""
SMS Service for patient communication via Twilio
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from config import Config
from typing import Optional, Dict, Any

class SMSService:
    """Service for sending and managing SMS communications"""
    
    def __init__(self):
        """Initialize Twilio client"""
        try:
            Config.validate_twilio()
            self.client = Client(
                Config.TWILIO_ACCOUNT_SID,
                Config.TWILIO_AUTH_TOKEN
            )
            self.from_number = Config.TWILIO_PHONE_NUMBER
        except Exception as e:
            raise Exception(f"Failed to initialize Twilio: {str(e)}")
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS to a phone number
        
        Args:
            to_number: Recipient phone number (E.164 format: +1234567890)
            message: Message text to send
            
        Returns:
            Dictionary with message details
        """
        try:
            # Validate phone number format
            if not to_number.startswith('+'):
                raise ValueError("Phone number must be in E.164 format (e.g., +1234567890)")
            
            # Send message
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            return {
                'success': True,
                'message_sid': message_obj.sid,
                'status': message_obj.status,
                'to': to_number,
                'from': self.from_number,
                'body': message
            }
            
        except TwilioRestException as e:
            raise Exception(f"Twilio API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error sending SMS: {str(e)}")
    
    def send_discharge_summary_notification(
        self, 
        to_number: str, 
        patient_name: str,
        summary_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send discharge summary notification to patient
        
        Args:
            to_number: Patient phone number
            patient_name: Patient's name
            summary_url: Optional URL to view full summary
            
        Returns:
            Dictionary with message details
        """
        message = f"Hello {patient_name},\n\n"
        message += "Your discharge summary is ready. "
        
        if summary_url:
            message += f"View it here: {summary_url}\n\n"
        
        message += "Reply with any questions about your discharge instructions."
        
        return self.send_sms(to_number, message)
    
    def send_follow_up_reminder(
        self,
        to_number: str,
        patient_name: str,
        appointment_details: str
    ) -> Dict[str, Any]:
        """
        Send follow-up appointment reminder
        
        Args:
            to_number: Patient phone number
            patient_name: Patient's name
            appointment_details: Details about the appointment
            
        Returns:
            Dictionary with message details
        """
        message = f"Hello {patient_name},\n\n"
        message += f"Reminder: {appointment_details}\n\n"
        message += "Reply 'CONFIRM' to confirm or 'RESCHEDULE' if you need to change the appointment."
        
        return self.send_sms(to_number, message)
    
    def get_message_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Get status of a sent message
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Dictionary with message status
        """
        try:
            message = self.client.messages(message_sid).fetch()
            
            return {
                'sid': message.sid,
                'status': message.status,
                'to': message.to,
                'from': message.from_,
                'body': message.body,
                'date_sent': str(message.date_sent),
                'error_code': message.error_code,
                'error_message': message.error_message
            }
        except TwilioRestException as e:
            raise Exception(f"Error fetching message status: {str(e)}")
