"""
Tool Registry
Centralized registration of all MCP tools
"""
import logging
from mcp.server import MCPServer
from mcp.tools.sms_tool import SMSTool, ConversationSMSTool
from mcp.tools.ai_summary_tool import AISummaryTool, FormResponseSummaryTool
from mcp.tools.forms_tool import SendFormTool, ProcessFormResponseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Tool Registry manages initialization and registration of all MCP tools.
    Provides a centralized way to set up the MCP server with all available tools.
    """
    
    @staticmethod
    def create_and_register_tools(
        mcp_server: MCPServer,
        sms_service=None,
        ai_service=None,
        conversation_agent=None,
        forms_service=None
    ) -> MCPServer:
        """
        Create and register all MCP tools with the server.
        
        Args:
            mcp_server: MCPServer instance to register tools with
            sms_service: Optional existing SMSService instance
            ai_service: Optional existing AIService instance
            conversation_agent: Optional existing ConversationAgent instance
            forms_service: Optional existing FormsService instance
            
        Returns:
            MCPServer with all tools registered
        """
        print("[Tool Registry] Registering MCP tools...")
        logger.info("[Tool Registry] Starting tool registration")
        
        # Register SMS Tool
        try:
            sms_tool = SMSTool(sms_service=sms_service)
            mcp_server.register_tool(sms_tool)
        except Exception as e:
            logger.warning(f"[Tool Registry] Failed to register SMS Tool: {e}")
            print(f"[Tool Registry] Warning: SMS Tool registration failed - {e}")
        
        # Register Conversation SMS Tool
        try:
            conversation_sms_tool = ConversationSMSTool(conversation_agent=conversation_agent)
            mcp_server.register_tool(conversation_sms_tool)
        except Exception as e:
            logger.warning(f"[Tool Registry] Failed to register Conversation SMS Tool: {e}")
            print(f"[Tool Registry] Warning: Conversation SMS Tool registration failed - {e}")
        
        # Register AI Summary Tool
        try:
            ai_summary_tool = AISummaryTool(ai_service=ai_service)
            mcp_server.register_tool(ai_summary_tool)
        except Exception as e:
            logger.warning(f"[Tool Registry] Failed to register AI Summary Tool: {e}")
            print(f"[Tool Registry] Warning: AI Summary Tool registration failed - {e}")
        
        # Register Form Response Summary Tool
        try:
            form_summary_tool = FormResponseSummaryTool(ai_service=ai_service)
            mcp_server.register_tool(form_summary_tool)
        except Exception as e:
            logger.warning(f"[Tool Registry] Failed to register Form Response Summary Tool: {e}")
            print(f"[Tool Registry] Warning: Form Response Summary Tool registration failed - {e}")
        
        # Register Send Form Tool
        try:
            send_form_tool = SendFormTool(forms_service=forms_service)
            mcp_server.register_tool(send_form_tool)
        except Exception as e:
            logger.warning(f"[Tool Registry] Failed to register Send Form Tool: {e}")
            print(f"[Tool Registry] Warning: Send Form Tool registration failed - {e}")
        
        # Register Process Form Response Tool
        try:
            process_form_tool = ProcessFormResponseTool(forms_service=forms_service)
            mcp_server.register_tool(process_form_tool)
        except Exception as e:
            logger.warning(f"[Tool Registry] Failed to register Process Form Response Tool: {e}")
            print(f"[Tool Registry] Warning: Process Form Response Tool registration failed - {e}")
        
        # Log registration summary
        registered_tools = mcp_server.list_tools()
        print(f"[Tool Registry] Successfully registered {len(registered_tools)} tools")
        for tool in registered_tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")
        
        logger.info(f"[Tool Registry] Registered {len(registered_tools)} tools")
        
        return mcp_server
    
    @staticmethod
    def get_tool_descriptions() -> str:
        """
        Get human-readable descriptions of all available tools.
        
        Returns:
            Formatted string with tool descriptions
        """
        descriptions = [
            "Available MCP Tools:",
            "",
            "1. send_sms - Send SMS messages to patients",
            "2. start_conversation - Start structured patient check-in conversation",
            "3. generate_summary - Generate AI summary from discharge reports",
            "4. summarize_form_response - Summarize patient form responses for care team",
            "5. send_form_link - Send Google Form link to patients via SMS",
            "6. process_form_response - Process submitted form and notify care team",
        ]
        return "\n".join(descriptions)
