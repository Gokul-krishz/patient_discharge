from twilio.rest import Client
from app.config import settings
from typing import Optional


class TwilioService:
    def __init__(self):
        self.client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
    
    def send_sms(self, to_phone: str, message: str) -> dict:
        """
        Send an SMS message using Twilio.
        
        Args:
            to_phone: Recipient phone number (with country code, e.g., +1234567890)
            message: Message text to send
            
        Returns:
            dict: Response containing status and message_sid
        """
        if not self.client:
            return {
                "success": False,
                "error": "Twilio client not configured. Please check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
            }
        
        if not settings.TWILIO_PHONE_NUMBER:
            return {
                "success": False,
                "error": "Twilio phone number not configured. Please check TWILIO_PHONE_NUMBER."
            }
        
        try:
            formatted_to = to_phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
            if not formatted_to.startswith("+"):
                formatted_to = "+" + formatted_to
            
            message_obj = self.client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=formatted_to
            )
            
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "status": message_obj.status,
                "to": formatted_to,
                "from": settings.TWILIO_PHONE_NUMBER
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def is_configured(self) -> bool:
        """
        Check if Twilio is properly configured.
        """
        return bool(
            self.client and
            settings.TWILIO_ACCOUNT_SID and
            settings.TWILIO_AUTH_TOKEN and
            settings.TWILIO_PHONE_NUMBER
        )


# Singleton instance
twilio_service = TwilioService()
