"""
SMS Tool
MCP tool for sending SMS messages via existing SMSService
"""
from typing import Dict, Any
from mcp.tools.base import MCPTool
from services.sms_service import SMSService


class SMSTool(MCPTool):
    """
    SMS Tool wraps the existing SMSService for MCP integration.
    Provides SMS sending capabilities to AI agents.
    """
    
    def __init__(self, sms_service: SMSService = None):
        """
        Initialize SMS tool with existing SMSService.
        
        Args:
            sms_service: Existing SMSService instance (optional, will create if None)
        """
        self.sms_service = sms_service or SMSService()
        self.log_execution("Initialized", "SMS Tool ready")
    
    @property
    def name(self) -> str:
        return "send_sms"
    
    @property
    def description(self) -> str:
        return (
            "Send SMS message to a patient via Twilio. "
            "Use this tool to send discharge notifications, follow-up reminders, "
            "or responses to patient questions."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "phone_number": {
                "type": "string",
                "required": True,
                "description": "Patient phone number in E.164 format (e.g., +1234567890)"
            },
            "message": {
                "type": "string",
                "required": True,
                "description": "SMS message text to send"
            },
            "message_type": {
                "type": "string",
                "required": False,
                "description": "Type of message: 'notification', 'question', 'reminder', 'response'"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute SMS sending via existing SMSService.
        
        Args:
            phone_number: Patient phone number
            message: Message text
            message_type: Optional message type
            
        Returns:
            Dict with SMS sending results
        """
        self.validate_parameters(**kwargs)
        
        phone_number = kwargs['phone_number']
        message = kwargs['message']
        message_type = kwargs.get('message_type', 'notification')
        
        self.log_execution(
            "Sending SMS",
            f"to {phone_number}, type: {message_type}"
        )
        
        try:
            # Call existing SMSService
            result = self.sms_service.send_sms(phone_number, message)
            
            self.log_execution(
                "SMS sent successfully",
                f"SID: {result.get('message_sid')}"
            )
            
            return {
                'success': True,
                'tool': self.name,
                'phone_number': phone_number,
                'message_type': message_type,
                'message_sid': result.get('message_sid'),
                'status': result.get('status'),
                'message_preview': message[:50] + '...' if len(message) > 50 else message
            }
            
        except Exception as e:
            self.log_execution("SMS sending failed", str(e))
            return {
                'success': False,
                'tool': self.name,
                'phone_number': phone_number,
                'error': str(e)
            }


class ConversationSMSTool(MCPTool):
    """
    Conversation SMS Tool for structured patient check-in conversations.
    Wraps ConversationAgent functionality.
    """
    
    def __init__(self, conversation_agent=None):
        """
        Initialize conversation SMS tool.
        
        Args:
            conversation_agent: Existing ConversationAgent instance
        """
        from services.conversation_agent import ConversationAgent
        self.conversation_agent = conversation_agent or ConversationAgent()
        self.log_execution("Initialized", "Conversation SMS Tool ready")
    
    @property
    def name(self) -> str:
        return "start_conversation"
    
    @property
    def description(self) -> str:
        return (
            "Start a structured patient check-in conversation via SMS. "
            "Sends a series of health-related questions to the patient."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "phone_number": {
                "type": "string",
                "required": True,
                "description": "Patient phone number"
            },
            "patient_name": {
                "type": "string",
                "required": True,
                "description": "Patient full name"
            },
            "discharge_summary": {
                "type": "object",
                "required": False,
                "description": "Optional discharge summary context"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Start conversation via existing ConversationAgent.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            discharge_summary: Optional discharge summary
            
        Returns:
            Dict with conversation start results
        """
        self.validate_parameters(**kwargs)
        
        phone_number = kwargs['phone_number']
        patient_name = kwargs['patient_name']
        discharge_summary = kwargs.get('discharge_summary')
        
        self.log_execution(
            "Starting conversation",
            f"with {patient_name} at {phone_number}"
        )
        
        try:
            # Call existing ConversationAgent
            result = self.conversation_agent.start_conversation(
                phone_number, patient_name, discharge_summary
            )
            
            self.log_execution(
                "Conversation started",
                f"ID: {result.get('conversation_id')}"
            )
            
            return {
                'success': True,
                'tool': self.name,
                'conversation_id': result.get('conversation_id'),
                'patient_name': patient_name,
                'phone_number': phone_number,
                'first_question_sent': True,
                'total_questions': result.get('total_questions')
            }
            
        except Exception as e:
            self.log_execution("Conversation start failed", str(e))
            return {
                'success': False,
                'tool': self.name,
                'error': str(e)
            }
