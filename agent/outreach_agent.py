"""
Outreach Agent
AI Agent that orchestrates patient outreach workflows using MCP tools
"""
import logging
from typing import Dict, Any, Optional
from mcp.server import MCPServer

logger = logging.getLogger(__name__)


class OutreachAgent:
    """
    Outreach Agent orchestrates patient communication workflows.
    Uses MCP Server to execute tools for SMS, conversations, and AI summaries.
    """
    
    def __init__(self, mcp_server: MCPServer):
        """
        Initialize Outreach Agent with MCP Server.
        
        Args:
            mcp_server: Configured MCPServer with registered tools
        """
        self.mcp_server = mcp_server
        self.context: Dict[str, Any] = {}
        
        log_msg = "[AI Agent] Outreach Agent initialized"
        logger.info(log_msg)
        print(log_msg)
    
    def start_patient_outreach(
        self,
        phone_number: str,
        patient_name: str,
        outreach_type: str = "conversation",
        discharge_summary: Optional[Dict] = None,
        custom_message: Optional[str] = None,
        form_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start patient outreach workflow.
        
        This is the main orchestration method that coordinates multiple tools
        to complete a patient outreach workflow.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            outreach_type: Type of outreach ('conversation', 'notification', 'reminder', 'form')
            discharge_summary: Optional discharge summary context
            custom_message: Optional custom message for notifications
            form_url: Optional Google Form URL for form-based outreach
            
        Returns:
            Dict with workflow results
        """
        print("\n" + "="*70)
        print("[AI Agent] Starting patient outreach workflow")
        print("="*70)
        logger.info(f"[AI Agent] Starting outreach for {patient_name} ({outreach_type})")
        
        workflow_result = {
            'agent': 'OutreachAgent',
            'workflow': 'patient_outreach',
            'patient_name': patient_name,
            'phone_number': phone_number,
            'outreach_type': outreach_type,
            'steps_completed': [],
            'success': False
        }
        
        try:
            if outreach_type == "conversation":
                # Workflow: Start structured conversation
                result = self._start_conversation_workflow(
                    phone_number, patient_name, discharge_summary
                )
                workflow_result.update(result)
                
            elif outreach_type == "notification":
                # Workflow: Send notification SMS
                result = self._send_notification_workflow(
                    phone_number, patient_name, custom_message
                )
                workflow_result.update(result)
                
            elif outreach_type == "reminder":
                # Workflow: Send reminder SMS
                result = self._send_reminder_workflow(
                    phone_number, patient_name, custom_message
                )
                workflow_result.update(result)
            
            elif outreach_type == "form":
                # Workflow: Send Google Form link
                result = self._send_form_workflow(
                    phone_number, patient_name, form_url
                )
                workflow_result.update(result)
            
            else:
                raise ValueError(f"Unknown outreach type: {outreach_type}")
            
            workflow_result['success'] = True
            
            print("="*70)
            print("[AI Agent] Outreach workflow completed successfully")
            print("="*70 + "\n")
            logger.info("[AI Agent] Outreach workflow completed")
            
        except Exception as e:
            error_msg = f"[AI Agent] Outreach workflow failed: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            workflow_result['error'] = str(e)
        
        return workflow_result
    
    def _start_conversation_workflow(
        self,
        phone_number: str,
        patient_name: str,
        discharge_summary: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Execute conversation workflow using MCP tools.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            discharge_summary: Optional discharge summary
            
        Returns:
            Dict with workflow results
        """
        print(f"[AI Agent] Executing conversation workflow for {patient_name}")
        logger.info(f"[AI Agent] Starting conversation workflow")
        
        steps = []
        
        # Step 1: Start conversation using MCP tool
        print("[AI Agent] Step 1: Starting structured conversation")
        conversation_result = self.mcp_server.execute_tool(
            "start_conversation",
            phone_number=phone_number,
            patient_name=patient_name,
            discharge_summary=discharge_summary
        )
        steps.append({
            'step': 'start_conversation',
            'tool': 'start_conversation',
            'result': conversation_result
        })
        
        return {
            'steps_completed': steps,
            'conversation_id': conversation_result.get('conversation_id'),
            'first_question_sent': conversation_result.get('first_question_sent'),
            'total_questions': conversation_result.get('total_questions')
        }
    
    def _send_notification_workflow(
        self,
        phone_number: str,
        patient_name: str,
        message: Optional[str]
    ) -> Dict[str, Any]:
        """
        Execute notification workflow using MCP tools.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            message: Notification message
            
        Returns:
            Dict with workflow results
        """
        print(f"[AI Agent] Executing notification workflow for {patient_name}")
        logger.info(f"[AI Agent] Starting notification workflow")
        
        steps = []
        
        # Default message if not provided
        if not message:
            message = (
                f"Hello {patient_name}, your discharge summary is ready. "
                f"Reply with any questions about your discharge instructions."
            )
        
        # Step 1: Send SMS notification using MCP tool
        print("[AI Agent] Step 1: Sending SMS notification")
        sms_result = self.mcp_server.execute_tool(
            "send_sms",
            phone_number=phone_number,
            message=message,
            message_type="notification"
        )
        steps.append({
            'step': 'send_notification',
            'tool': 'send_sms',
            'result': sms_result
        })
        
        return {
            'steps_completed': steps,
            'message_sent': sms_result.get('success'),
            'message_sid': sms_result.get('message_sid')
        }
    
    def _send_reminder_workflow(
        self,
        phone_number: str,
        patient_name: str,
        message: Optional[str]
    ) -> Dict[str, Any]:
        """
        Execute reminder workflow using MCP tools.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            message: Reminder message
            
        Returns:
            Dict with workflow results
        """
        print(f"[AI Agent] Executing reminder workflow for {patient_name}")
        logger.info(f"[AI Agent] Starting reminder workflow")
        
        steps = []
        
        # Default message if not provided
        if not message:
            message = (
                f"Hello {patient_name}, this is a reminder about your upcoming "
                f"follow-up appointment. Please confirm or reschedule if needed."
            )
        
        # Step 1: Send SMS reminder using MCP tool
        print("[AI Agent] Step 1: Sending SMS reminder")
        sms_result = self.mcp_server.execute_tool(
            "send_sms",
            phone_number=phone_number,
            message=message,
            message_type="reminder"
        )
        steps.append({
            'step': 'send_reminder',
            'tool': 'send_sms',
            'result': sms_result
        })
        
        return {
            'steps_completed': steps,
            'message_sent': sms_result.get('success'),
            'message_sid': sms_result.get('message_sid')
        }
    
    def _send_form_workflow(
        self,
        phone_number: str,
        patient_name: str,
        form_url: Optional[str]
    ) -> Dict[str, Any]:
        """
        Execute Google Form workflow using MCP tools.
        
        Args:
            phone_number: Patient phone number
            patient_name: Patient name
            form_url: Optional custom form URL
            
        Returns:
            Dict with workflow results
        """
        print(f"[AI Agent] Executing Google Form workflow for {patient_name}")
        logger.info(f"[AI Agent] Starting form workflow")
        
        steps = []
        
        # Step 1: Send Google Form link using MCP tool
        print("[AI Agent] Step 1: Sending Google Form link via SMS")
        form_result = self.mcp_server.execute_tool(
            "send_form_link",
            phone_number=phone_number,
            patient_name=patient_name,
            form_url=form_url
        )
        steps.append({
            'step': 'send_form_link',
            'tool': 'send_form_link',
            'result': form_result
        })
        
        return {
            'steps_completed': steps,
            'form_link_sent': form_result.get('success'),
            'form_url': form_result.get('form_url'),
            'message_sid': form_result.get('message_sid')
        }
    
    def generate_patient_summary(
        self,
        discharge_text: str,
        summary_type: str = "discharge_report"
    ) -> Dict[str, Any]:
        """
        Generate AI summary for patient data.
        
        Args:
            discharge_text: Text to summarize
            summary_type: Type of summary to generate
            
        Returns:
            Dict with summary results
        """
        print("\n" + "="*70)
        print("[AI Agent] Starting AI summary generation workflow")
        print("="*70)
        logger.info(f"[AI Agent] Generating {summary_type} summary")
        
        try:
            # Use MCP AI Summary Tool
            print("[AI Agent] Calling AI Summary Tool via MCP Server")
            summary_result = self.mcp_server.execute_tool(
                "generate_summary",
                text=discharge_text,
                summary_type=summary_type
            )
            
            print("="*70)
            print("[AI Agent] Summary generation completed")
            print("="*70 + "\n")
            
            return {
                'agent': 'OutreachAgent',
                'workflow': 'generate_summary',
                'success': summary_result.get('success'),
                'summary': summary_result.get('summary'),
                'fields_extracted': summary_result.get('fields_extracted')
            }
            
        except Exception as e:
            error_msg = f"[AI Agent] Summary generation failed: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return {
                'agent': 'OutreachAgent',
                'workflow': 'generate_summary',
                'success': False,
                'error': str(e)
            }
    
    def get_available_tools(self) -> Dict[str, Any]:
        """
        Get list of available MCP tools.
        
        Returns:
            Dict with tool information
        """
        tools = self.mcp_server.list_tools()
        return {
            'agent': 'OutreachAgent',
            'total_tools': len(tools),
            'tools': tools
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get agent and MCP server status.
        
        Returns:
            Dict with status information
        """
        server_status = self.mcp_server.get_server_status()
        return {
            'agent': 'OutreachAgent',
            'status': 'active',
            'mcp_server': server_status,
            'context_size': len(self.context)
        }
