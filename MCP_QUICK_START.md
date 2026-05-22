# MCP Architecture - Quick Start Guide

## 🚀 Getting Started

### 1. Start the Application

```bash
python app.py
```

You should see:

```
======================================================================
Initializing MCP Architecture
======================================================================
[MCP Server] Initialized
[Tool Registry] Registering MCP tools...
[MCP Server] Registered tool: send_sms
[MCP Server] Registered tool: start_conversation
[MCP Server] Registered tool: generate_summary
[MCP Server] Registered tool: summarize_form_response
[Tool Registry] Successfully registered 4 tools
  - send_sms: Send SMS message to a patient via Twilio. Use this tool...
  - start_conversation: Start a structured patient check-in conversation...
  - generate_summary: Generate AI-powered summary from patient discharge...
  - summarize_form_response: Generate professional care team summary from...
[AI Agent] Outreach Agent initialized
======================================================================
MCP Architecture initialized successfully
======================================================================
```

### 2. Test MCP Status

```bash
curl http://localhost:8080/api/mcp/status
```

Expected response:
```json
{
  "agent": "OutreachAgent",
  "status": "active",
  "mcp_server": {
    "status": "running",
    "registered_tools": 4,
    "tool_names": ["send_sms", "start_conversation", "generate_summary", "summarize_form_response"],
    "total_executions": 0
  },
  "context_size": 0,
  "mcp_enabled": true
}
```

### 3. List Available Tools

```bash
curl http://localhost:8080/api/mcp/tools
```

### 4. Use MCP Outreach (New Way)

```bash
curl -X POST http://localhost:8080/api/mcp/outreach \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919715441374",
    "patient_name": "John Doe",
    "outreach_type": "conversation"
  }'
```

### 5. Use Old Endpoint (Still Works!)

```bash
curl -X POST http://localhost:8080/api/start-conversation \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919715441374",
    "patient_name": "John Doe"
  }'
```

## 📊 Flow Visualization

### New MCP Flow

```
Your Request
    ↓
POST /api/mcp/outreach
    ↓
[AI Agent] Starting outreach workflow
    ↓
[MCP Server] Executing tool: start_conversation
    ↓
[MCP START_CONVERSATION Tool] Starting conversation
    ↓
ConversationAgent.start_conversation()
    ↓
SMSService.send_sms()
    ↓
Twilio API
```

### Console Output Example

```
======================================================================
[AI Agent] Starting patient outreach workflow
======================================================================
[AI Agent] Executing conversation workflow for John Doe
[AI Agent] Step 1: Starting structured conversation
[MCP Server] Executing tool: start_conversation
[MCP START_CONVERSATION Tool] Starting conversation - with John Doe at +919715441374
[MCP START_CONVERSATION Tool] Conversation started - ID: 123
[MCP Server] Tool 'start_conversation' executed successfully
======================================================================
[AI Agent] Outreach workflow completed successfully
======================================================================
```

## 🧪 Run Test Suite

```bash
python test_mcp_flow.py
```

This will test:
1. ✓ MCP Status
2. ✓ List Tools
3. ✓ MCP Outreach (Conversation)
4. ✓ MCP Outreach (Notification)
5. ✓ Health Check
6. ✓ Backward Compatibility

## 📋 Outreach Types

### 1. Conversation

Starts structured Q&A conversation:

```json
{
  "outreach_type": "conversation",
  "phone_number": "+919715441374",
  "patient_name": "John Doe"
}
```

### 2. Notification

Sends one-time notification:

```json
{
  "outreach_type": "notification",
  "phone_number": "+919715441374",
  "patient_name": "John Doe",
  "custom_message": "Your discharge summary is ready"
}
```

### 3. Reminder

Sends appointment reminder:

```json
{
  "outreach_type": "reminder",
  "phone_number": "+919715441374",
  "patient_name": "John Doe",
  "custom_message": "Appointment tomorrow at 2 PM"
}
```

## 🔍 Debugging

### Check MCP is Initialized

```bash
curl http://localhost:8080/api/health
```

Look for:
```json
{
  "mcp_architecture": {
    "enabled": true,
    "mcp_server_available": true,
    "outreach_agent_available": true,
    "registered_tools": 4
  }
}
```

### View Execution History

The MCP server tracks all tool executions. Check console logs for:
- `[MCP Server] Executing tool: <name>`
- `[MCP <TOOL> Tool] <action>`
- `[AI Agent] <workflow step>`

## 🎯 Key Differences

| Aspect | Old Way | New MCP Way |
|--------|---------|-------------|
| **Endpoint** | `/api/start-conversation` | `/api/mcp/outreach` |
| **Flow** | Direct service call | Agent → MCP → Tool → Service |
| **Logging** | Service-level only | Agent + MCP + Tool + Service |
| **Extensibility** | Modify route code | Add new tool |
| **Testing** | Mock services | Mock tools |

## ✅ Verification Checklist

- [ ] App starts without errors
- [ ] MCP initialization message appears
- [ ] 4 tools registered
- [ ] `/api/mcp/status` returns `mcp_enabled: true`
- [ ] `/api/mcp/tools` lists 4 tools
- [ ] `/api/mcp/outreach` works
- [ ] Old `/api/start-conversation` still works
- [ ] Console shows MCP flow logs

## 🚨 Troubleshooting

### MCP Not Initialized

**Symptom**: `/api/mcp/status` returns `mcp_enabled: false`

**Solution**: Check console for initialization errors. Ensure services are available.

### Tool Not Found

**Symptom**: `Tool 'xyz' not found`

**Solution**: Check tool is registered in `mcp/registry.py`

### Old Endpoints Not Working

**Symptom**: `/api/start-conversation` fails

**Solution**: MCP doesn't affect old endpoints. Check service initialization.

## 📚 Next Steps

1. **Explore Swagger UI**: http://localhost:8080/swagger
2. **Read Full Docs**: `MCP_ARCHITECTURE.md`
3. **Add Custom Tool**: See migration guide in docs
4. **Test with Postman**: Import API collection

---

**Quick Reference**: This is Phase 1 implementation with 4 core tools. Phase 2 will add database, forms, and notification tools.
