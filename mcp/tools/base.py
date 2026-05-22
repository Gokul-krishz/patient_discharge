"""
Base MCP Tool Interface
Defines the contract for all MCP tools
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MCPTool(ABC):
    """
    Base class for all MCP tools.
    Each tool must implement name, description, parameters, and execute().
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique tool name used for registration and execution.
        Example: 'send_sms', 'generate_summary'
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Human-readable description of what the tool does.
        Used by AI agents to understand tool capabilities.
        """
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """
        JSON schema describing tool parameters.
        Example:
        {
            "phone_number": {
                "type": "string",
                "required": True,
                "description": "Patient phone number in E.164 format"
            }
        }
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict with execution results
            
        Raises:
            ValueError: If required parameters are missing
            Exception: If tool execution fails
        """
        pass
    
    def validate_parameters(self, **kwargs) -> None:
        """
        Validate that required parameters are provided.
        
        Args:
            **kwargs: Parameters to validate
            
        Raises:
            ValueError: If required parameters are missing
        """
        for param_name, param_schema in self.parameters.items():
            if param_schema.get('required', False):
                if param_name not in kwargs:
                    raise ValueError(
                        f"Missing required parameter '{param_name}' for tool '{self.name}'"
                    )
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get complete tool schema for registration.
        
        Returns:
            Dict containing tool metadata
        """
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }
    
    def log_execution(self, action: str, details: Optional[str] = None):
        """
        Log tool execution for debugging and monitoring.
        
        Args:
            action: Action being performed
            details: Optional additional details
        """
        log_msg = f"[MCP {self.name.upper()} Tool] {action}"
        if details:
            log_msg += f" - {details}"
        logger.info(log_msg)
        print(log_msg)
