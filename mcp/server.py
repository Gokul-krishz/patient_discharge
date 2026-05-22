"""
MCP Server
Manages tool registry and execution
"""
from typing import Dict, Any, List, Optional
import logging
from mcp.tools.base import MCPTool

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server manages tool registration, discovery, and execution.
    Acts as the central hub between AI agents and tools.
    """
    
    def __init__(self):
        """Initialize MCP server with empty tool registry"""
        self.tools: Dict[str, MCPTool] = {}
        self.execution_history: List[Dict[str, Any]] = []
        logger.info("[MCP Server] Initialized")
        print("[MCP Server] Initialized")
    
    def register_tool(self, tool: MCPTool) -> None:
        """
        Register a tool with the MCP server.
        
        Args:
            tool: MCPTool instance to register
            
        Raises:
            ValueError: If tool with same name already registered
        """
        if tool.name in self.tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        
        self.tools[tool.name] = tool
        log_msg = f"[MCP Server] Registered tool: {tool.name}"
        logger.info(log_msg)
        print(log_msg)
    
    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool from the MCP server.
        
        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            log_msg = f"[MCP Server] Unregistered tool: {tool_name}"
            logger.info(log_msg)
            print(log_msg)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools with their schemas.
        
        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self.tools.values()]
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """
        Get a registered tool by name.
        
        Args:
            tool_name: Name of tool to retrieve
            
        Returns:
            MCPTool instance or None if not found
        """
        return self.tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a registered tool with given parameters.
        
        Args:
            tool_name: Name of tool to execute
            **kwargs: Tool-specific parameters
            
        Returns:
            Dict with execution results
            
        Raises:
            ValueError: If tool not found or parameters invalid
            Exception: If tool execution fails
        """
        log_msg = f"[MCP Server] Executing tool: {tool_name}"
        logger.info(log_msg)
        print(log_msg)
        
        # Check if tool exists
        if tool_name not in self.tools:
            available_tools = ', '.join(self.tools.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found. Available tools: {available_tools}"
            )
        
        tool = self.tools[tool_name]
        
        try:
            # Validate parameters
            tool.validate_parameters(**kwargs)
            
            # Execute tool
            result = tool.execute(**kwargs)
            
            # Record execution
            execution_record = {
                'tool_name': tool_name,
                'parameters': kwargs,
                'success': True,
                'result': result
            }
            self.execution_history.append(execution_record)
            
            log_msg = f"[MCP Server] Tool '{tool_name}' executed successfully"
            logger.info(log_msg)
            print(log_msg)
            
            return result
            
        except Exception as e:
            # Record failed execution
            execution_record = {
                'tool_name': tool_name,
                'parameters': kwargs,
                'success': False,
                'error': str(e)
            }
            self.execution_history.append(execution_record)
            
            error_msg = f"[MCP Server] Tool '{tool_name}' execution failed: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            
            raise
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get tool execution history.
        
        Args:
            limit: Optional limit on number of records to return
            
        Returns:
            List of execution records
        """
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history
    
    def clear_history(self) -> None:
        """Clear execution history"""
        self.execution_history = []
        logger.info("[MCP Server] Execution history cleared")
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        Get MCP server status.
        
        Returns:
            Dict with server status information
        """
        return {
            'status': 'running',
            'registered_tools': len(self.tools),
            'tool_names': list(self.tools.keys()),
            'total_executions': len(self.execution_history)
        }
