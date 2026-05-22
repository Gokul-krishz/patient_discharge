# MCP Architecture Implementation

## 🎯 Overview

This document describes the **Model Context Protocol (MCP)** architecture implementation in the patient discharge management system.

### What is MCP?

MCP provides a standardized way for AI agents to interact with tools and services. Instead of directly calling services, the agent uses a tool abstraction layer that makes the system more modular, testable, and extensible.

## 🏗️ Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    FLASK API LAYER                           │
│  /api/mcp/outreach (NEW)                                     │
│  /api/start-conversation (OLD - still works)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI AGENT LAYER                             │
│  OutreachAgent                                               │
│  • Orchestrates workflows                                    │
│  • Decides which tools to use                                │
│  • Manages conversation context                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP SERVER                                 │
│  • Tool registry                                             │
│  • Tool discovery                                            │
│  • Tool execution                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP TOOLS                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  SMS Tool    │  │ Conversation │  │ AI Summary   │      │
│  │              │  │  SMS Tool    │  │    Tool      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXISTING SERVICES                          │
│  SMSService, ConversationAgent, AIService                    │
│  (No changes to existing service code)                       │
└─────────────────────────────────────────────────────────────┘
```

## 📁 New Files Created

### 1. MCP Core Infrastructure

```
mcp/
├── __init__.py                 # MCP module exports
├── server.py                   # MCP Server implementation
├── registry.py                 # Tool registration
└── tools/
    ├── __init__.py            # Tools module exports
    ├── base.py                # Base MCPTool class
    ├── sms_tool.py            # SMS tool implementation
    └── ai_summary_tool.py     # AI summary tool implementation
```

### 2. AI Agent Layer

```
agent/
├── __init__.py                # Agent module exports
└── outreach_agent.py          # Outreach orchestrator
```

### 3. Test & Documentation

```
test_mcp_flow.py               # MCP flow test suite
MCP_ARCHITECTURE.md            # This file
```

## 🔧 Key Components

### MCPTool Base Class

All tools inherit from `MCPTool` and implement:

```python
class MCPTool(ABC):
    @property
    def name(self) -> str:
        """Tool name for registration"""
        
    @property
    def description(self) -> str:
        """What the tool does"""
        
    @property
    def parameters(self) -> Dict[str, Any]:
        """Parameter schema"""
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
```

### MCP Server

Manages tool lifecycle:

```python
mcp_server = MCPServer()
mcp_server.register_tool(sms_tool)
result = mcp_server.execute_tool("send_sms", phone_number="+1234567890", message="Hello")
```

### Outreach Agent

Orchestrates workflows using MCP tools:

```python
agent = OutreachAgent(mcp_server)
result = agent.start_patient_outreach(
    phone_number="+1234567890",
    patient_name="John Doe",
    outreach_type="conversation"
)
```

## 🚀 Available Tools

### 1. SMS Tool (`send_sms`)

**Purpose**: Send SMS messages to patients

**Parameters**:
- `phone_number` (required): Patient phone number
- `message` (required): Message text
- `message_type` (optional): Type of message

**Example**:
```python
mcp_server.execute_tool(
    "send_sms",
    phone_number="+919715441374",
    message="Your discharge summary is ready",
    message_type="notification"
)
```

### 2. Conversation SMS Tool (`start_conversation`)

**Purpose**: Start structured patient check-in conversation

**Parameters**:
- `phone_number` (required): Patient phone number
- `patient_name` (required): Patient name
- `discharge_summary` (optional): Discharge context

**Example**:
```python
mcp_server.execute_tool(
    "start_conversation",
    phone_number="+919715441374",
    patient_name="John Doe"
)
```

### 3. AI Summary Tool (`generate_summary`)

**Purpose**: Generate AI summary from discharge reports

**Parameters**:
- `text` (required): Text to summarize
- `summary_type` (optional): Type of summary

**Example**:
```python
mcp_server.execute_tool(
    "generate_summary",
    text="Patient discharge report...",
    summary_type="discharge_report"
)
```

### 4. Form Response Summary Tool (`summarize_form_response`)

**Purpose**: Summarize patient form responses

**Parameters**:
- `conversation_data` (required): Form responses with Q&A pairs

## 📡 API Endpoints

### New MCP Endpoints

#### 1. Start MCP Outreach

```http
POST /api/mcp/outreach
Content-Type: application/json

{
  "phone_number": "+919715441374",
  "patient_name": "John Doe",
  "outreach_type": "conversation",
  "discharge_summary": {...},
  "custom_message": "Optional message"
}
```

**Outreach Types**:
- `conversation`: Start structured Q&A conversation
- `notification`: Send one-time notification
- `reminder`: Send appointment reminder

#### 2. List MCP Tools

```http
GET /api/mcp/tools
```

Returns list of all registered MCP tools with their schemas.

#### 3. MCP Status

```http
GET /api/mcp/status
```

Returns MCP server and agent status.

### Existing Endpoints (Still Work!)

All existing endpoints continue to work:
- `/api/start-conversation` - Direct conversation start
- `/api/send-sms` - Direct SMS sending
- `/api/discharge-summary` - AI summary generation

## 🔄 Flow Comparison

### Old Flow (Direct Service Calls)

```
POST /api/start-conversation
  ↓
Flask Route Handler
  ↓
conversation_agent.start_conversation()
  ↓
sms_service.send_sms()
  ↓
Twilio API
```

### New Flow (MCP Architecture)

```
POST /api/mcp/outreach
  ↓
Flask Route Handler
  ↓
outreach_agent.start_patient_outreach()
  ↓
mcp_server.execute_tool("start_conversation")
  ↓
ConversationSMSTool.execute()
  ↓
conversation_agent.start_conversation()
  ↓
sms_service.send_sms()
  ↓
Twilio API
```

## 📊 Logging

The MCP architecture provides detailed logging:

```
[MCP Server] Initialized
[Tool Registry] Registering MCP tools...
[MCP Server] Registered tool: send_sms
[MCP Server] Registered tool: start_conversation
[MCP Server] Registered tool: generate_summary
[MCP Server] Registered tool: summarize_form_response
[Tool Registry] Successfully registered 4 tools
[AI Agent] Outreach Agent initialized

======================================================================
[AI Agent] Starting patient outreach workflow
======================================================================
[AI Agent] Executing conversation workflow for John Doe
[AI Agent] Step 1: Starting structured conversation
[MCP Server] Executing tool: start_conversation
[MCP START_CONVERSATION Tool] Starting conversation - with John Doe at +919715441374
[MCP START_CONVERSATION Tool] Conversation started - ID: 1
[MCP Server] Tool 'start_conversation' executed successfully
======================================================================
[AI Agent] Outreach workflow completed successfully
======================================================================
```

## 🧪 Testing

### Run Test Suite

```bash
# Start Flask app
python app.py

# In another terminal, run tests
python test_mcp_flow.py
```

### Manual Testing with cURL

```bash
# Test MCP status
curl http://localhost:8080/api/mcp/status

# Test list tools
curl http://localhost:8080/api/mcp/tools

# Test MCP outreach
curl -X POST http://localhost:8080/api/mcp/outreach \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919715441374",
    "patient_name": "Test Patient",
    "outreach_type": "conversation"
  }'

# Test backward compatibility
curl -X POST http://localhost:8080/api/start-conversation \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919715441374",
    "patient_name": "Test Patient"
  }'
```

## ✅ Benefits of MCP Architecture

### 1. **Modularity**
- Tools are independent and reusable
- Easy to add new tools without changing agent logic

### 2. **Testability**
- Mock tools for testing
- Test agent logic without calling real services

### 3. **Observability**
- Centralized logging of all tool executions
- Easy to track workflow progress

### 4. **Extensibility**
- Add new tools by implementing `MCPTool` interface
- Agent automatically discovers new tools

### 5. **Backward Compatibility**
- Old endpoints still work
- Gradual migration possible

## 🔮 Future Enhancements

### Phase 2 (Not Yet Implemented)

- Database Tool
- Forms Tool
- Notification Tool
- Patient Chat Tool

### Phase 3 (Future)

- LangGraph integration for complex workflows
- Autonomous agent decision-making
- Multi-step reasoning
- Tool composition and chaining

## 📝 Migration Guide

### Adding a New Tool

1. **Create tool class**:

```python
# mcp/tools/my_tool.py
from mcp.tools.base import MCPTool

class MyTool(MCPTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "What my tool does"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "param1": {"type": "string", "required": True}
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        # Tool logic here
        return {"success": True}
```

2. **Register in registry**:

```python
# mcp/registry.py
from mcp.tools.my_tool import MyTool

# In create_and_register_tools():
my_tool = MyTool()
mcp_server.register_tool(my_tool)
```

3. **Use in agent**:

```python
# agent/outreach_agent.py
result = self.mcp_server.execute_tool("my_tool", param1="value")
```

## 🎓 Key Takeaways

1. **MCP is an abstraction layer** - It sits between agents and services
2. **Existing code unchanged** - Services work exactly as before
3. **Backward compatible** - Old endpoints still function
4. **Gradual adoption** - Can migrate endpoints one at a time
5. **Foundation for AI** - Ready for autonomous agent workflows

## 📞 Support

For questions or issues with MCP implementation:
1. Check logs for `[MCP Server]` and `[AI Agent]` messages
2. Test with `/api/mcp/status` endpoint
3. Verify tools are registered with `/api/mcp/tools`
4. Run test suite: `python test_mcp_flow.py`

---

**Status**: ✅ Phase 1 Complete
**Version**: 1.0
**Last Updated**: May 21, 2026
