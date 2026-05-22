"""
AI Summary Tool
MCP tool for generating AI summaries via existing AIService
"""
from typing import Dict, Any
from mcp.tools.base import MCPTool
from services.ai_service import AIService


class AISummaryTool(MCPTool):
    """
    AI Summary Tool wraps the existing AIService for MCP integration.
    Provides AI-powered summarization capabilities to agents.
    """
    
    def __init__(self, ai_service: AIService = None):
        """
        Initialize AI summary tool with existing AIService.
        
        Args:
            ai_service: Existing AIService instance (optional, will create if None)
        """
        self.ai_service = ai_service or AIService()
        self.log_execution("Initialized", "AI Summary Tool ready")
    
    @property
    def name(self) -> str:
        return "generate_summary"
    
    @property
    def description(self) -> str:
        return (
            "Generate AI-powered summary from patient discharge report text. "
            "Extracts structured information including patient name, medications, "
            "symptoms, diet restrictions, and care team updates."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "text": {
                "type": "string",
                "required": True,
                "description": "Raw discharge report text to summarize"
            },
            "summary_type": {
                "type": "string",
                "required": False,
                "description": "Type of summary: 'discharge_report' or 'form_response'"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute AI summarization via existing AIService.
        
        Args:
            text: Text to summarize
            summary_type: Type of summary to generate
            
        Returns:
            Dict with AI-generated summary
        """
        self.validate_parameters(**kwargs)
        
        text = kwargs['text']
        summary_type = kwargs.get('summary_type', 'discharge_report')
        
        self.log_execution(
            "Generating AI summary",
            f"type: {summary_type}, text length: {len(text)} chars"
        )
        
        try:
            # Call existing AIService
            if summary_type == 'discharge_report':
                summary = self.ai_service.summarize_discharge_report(text)
            else:
                summary = self.ai_service.summarize_discharge_report(text)
            
            self.log_execution(
                "AI summary generated",
                f"extracted {len(summary)} fields"
            )
            
            return {
                'success': True,
                'tool': self.name,
                'summary_type': summary_type,
                'summary': summary,
                'fields_extracted': list(summary.keys()) if isinstance(summary, dict) else []
            }
            
        except Exception as e:
            self.log_execution("AI summary generation failed", str(e))
            return {
                'success': False,
                'tool': self.name,
                'error': str(e)
            }


class FormResponseSummaryTool(MCPTool):
    """
    Form Response Summary Tool for generating summaries from patient form responses.
    """
    
    def __init__(self, ai_service: AIService = None):
        """
        Initialize form response summary tool.
        
        Args:
            ai_service: Existing AIService instance
        """
        self.ai_service = ai_service or AIService()
        self.log_execution("Initialized", "Form Response Summary Tool ready")
    
    @property
    def name(self) -> str:
        return "summarize_form_response"
    
    @property
    def description(self) -> str:
        return (
            "Generate professional care team summary from patient form responses. "
            "Analyzes post-discharge questionnaire answers and creates actionable insights."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "conversation_data": {
                "type": "object",
                "required": True,
                "description": "Patient form responses with Q&A pairs and context"
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute form response summarization.
        
        Args:
            conversation_data: Dict with qa_pairs and patient_context
            
        Returns:
            Dict with AI-generated summary
        """
        self.validate_parameters(**kwargs)
        
        conversation_data = kwargs['conversation_data']
        
        self.log_execution(
            "Generating form response summary",
            f"processing {len(conversation_data.get('qa_pairs', []))} Q&A pairs"
        )
        
        try:
            # Call existing AIService method
            summary = self.ai_service.generate_discharge_summary(conversation_data)
            
            self.log_execution(
                "Form response summary generated",
                "ready for care team"
            )
            
            return {
                'success': True,
                'tool': self.name,
                'summary': summary,
                'details': summary.get('details', ''),
                'action_required': summary.get('action_required', ''),
                'formatted_response': summary.get('formatted_response', '')
            }
            
        except Exception as e:
            self.log_execution("Form response summary failed", str(e))
            return {
                'success': False,
                'tool': self.name,
                'error': str(e)
            }
