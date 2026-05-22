"""
Forms Tool
MCP tool for Google Forms workflow - send form link and process responses
"""
from typing import Dict, Any
from mcp.tools.base import MCPTool
from services.forms_service import FormsService
from config import Config


class SendFormTool(MCPTool):
    """
    Send Form Tool wraps the FormsService for sending Google Form links.
    Provides form link sending capabilities to AI agents.
    """
    
    def __init__(self, forms_service: FormsService = None):
        """
        Initialize Send Form tool with existing FormsService.
        
        Args:
            forms_service: Existing FormsService instance (optional, will create if None)
        """
        google_form_url = getattr(Config, 'GOOGLE_FORM_URL', None)
        self.forms_service = forms_service or FormsService(google_form_url=google_form_url)
        self.log_execution("Initialized", "Send Form Tool ready")
    
    @property
    def name(self) -> str:
        return "send_form_link"
    
    @property
    def description(self) -> str:
        return (
            "Send Google Form link to patient via SMS for post-discharge health questionnaire. "
            "Use this tool to collect structured patient feedback after discharge."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "phone_number": {
                "type": "string",
                "required": True,
                "description": "Patient phone number in E.164 format (e.g., +1234567890)"
            },
            "patient_name": {
                "type": "string",
                "required": True,
                "description": "Patient full name"
            },
            "form_url": {
                "type": "string",
                "required": False,
                "description": "Optional custom Google Form URL (uses default if not provided)"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute form link sending via existing FormsService.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            form_url: Optional custom form URL
            
        Returns:
            Dict with form link sending results
        """
        self.validate_parameters(**kwargs)
        
        phone_number = kwargs['phone_number']
        patient_name = kwargs['patient_name']
        form_url = kwargs.get('form_url')
        
        self.log_execution(
            "Sending Google Form link",
            f"to {patient_name} at {phone_number}"
        )
        
        try:
            # Call existing FormsService
            result = self.forms_service.send_form_link(
                phone_number=phone_number,
                patient_name=patient_name,
                form_url=form_url
            )
            
            self.log_execution(
                "Form link sent successfully",
                f"Message SID: {result.get('message_sid')}"
            )
            
            return {
                'success': True,
                'tool': self.name,
                'phone_number': phone_number,
                'patient_name': patient_name,
                'form_url': result.get('form_url'),
                'message_sid': result.get('message_sid'),
                'message_sent': result.get('success', False)
            }
            
        except Exception as e:
            self.log_execution("Form link sending failed", str(e))
            return {
                'success': False,
                'tool': self.name,
                'phone_number': phone_number,
                'error': str(e)
            }


class ProcessFormResponseTool(MCPTool):
    """
    Process Form Response Tool for handling submitted Google Form responses.
    Generates AI summary and notifies care team.
    """
    
    def __init__(self, forms_service: FormsService = None):
        """
        Initialize Process Form Response tool.
        
        Args:
            forms_service: Existing FormsService instance
        """
        google_form_url = getattr(Config, 'GOOGLE_FORM_URL', None)
        self.forms_service = forms_service or FormsService(google_form_url=google_form_url)
        self.log_execution("Initialized", "Process Form Response Tool ready")
    
    @property
    def name(self) -> str:
        return "process_form_response"
    
    @property
    def description(self) -> str:
        return (
            "Process submitted Google Form response, generate AI summary, "
            "and notify care team members. Use this when a patient submits the form."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "payload": {
                "type": "object",
                "required": True,
                "description": "Form submission payload with patient info and responses"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute form response processing.
        
        Args:
            payload: Form submission data
            
        Returns:
            Dict with processing results including AI summary
        """
        self.validate_parameters(**kwargs)
        
        payload = kwargs['payload']
        patient_name = payload.get('patient_name', 'Unknown')
        
        self.log_execution(
            "Processing form response",
            f"for patient: {patient_name}"
        )
        
        try:
            # Call existing FormsService to save and process
            result = self.forms_service.save_form_response(payload)
            
            self.log_execution(
                "Form response processed",
                f"Summary generated and care team notified"
            )
            
            return {
                'success': True,
                'tool': self.name,
                'patient_name': patient_name,
                'response_id': result.get('response_id'),
                'summary_generated': result.get('summary_generated', False),
                'summary': result.get('summary'),
                'care_team_notified': result.get('care_team_notified', False),
                'notifications': result.get('notifications')
            }
            
        except Exception as e:
            self.log_execution("Form response processing failed", str(e))
            return {
                'success': False,
                'tool': self.name,
                'error': str(e)
            }
