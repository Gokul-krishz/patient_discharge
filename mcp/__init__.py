"""
MCP (Model Context Protocol) Layer
Provides tool abstraction for AI agent orchestration
"""
from .server import MCPServer
from .registry import ToolRegistry

__all__ = ['MCPServer', 'ToolRegistry']
