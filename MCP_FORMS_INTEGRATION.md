# MCP Google Forms Integration

## 🎯 Overview

The MCP architecture now supports **Google Forms workflow** for post-discharge patient questionnaires. Instead of sending structured SMS questions, the system sends a Google Form link, and when the patient submits the form, it automatically generates an AI summary and notifies the care team.

## 🔄 New Workflow

### **Previous Flow (Structured SMS)**
```
POST /api/mcp/outreach (outreach_type: "conversation")
  ↓
AI Agent → MCP Server → Conversation SMS Tool
  ↓
Send 5 questions via SMS one by one
  ↓
Patient replies to each question
  ↓
Store responses in database
```

### **New Flow (Google Forms)**
```
POST /api/mcp/outreach (outreach_type: "form")
  ↓
AI Agent → MCP Server → Send Form Tool
  ↓
Send Google Form link via SMS
  ↓
Patient fills out form and submits
  ↓
Google Apps Script webhook → /api/forms/webhook
  ↓
MCP Server → Process Form Response Tool
  ↓
Generate AI summary + Notify care team
```

## 🛠️ New MCP Tools Added

### **1. Send Form Tool** (`send_form_link`)

**Purpose**: Send Google Form link to patient via SMS

**Parameters**:
- `phone_number` (required): Patient phone number
- `patient_name` (required): Patient name
- `form_url` (optional): Custom form URL (uses default from .env if not provided)

**Example**:
```python
mcp_server.execute_tool(
    "send_form_link",
    phone_number="+917477858611",
    patient_name="John Doe"
)
```

### **2. Process Form Response Tool** (`process_form_response`)

**Purpose**: Process submitted form, generate AI summary, notify care team

**Parameters**:
- `payload` (required): Form submission data from Google Apps Script

**Example**:
```python
mcp_server.execute_tool(
    "process_form_response",
    payload={
        "patient_name": "John Doe",
        "patient_phone": "+917477858611",
        "responses": {...}
    }
)
```

## 📡 API Usage

### **Send Google Form Link (MCP Way)**

```bash
curl -X POST http://localhost:8080/api/mcp/outreach \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+917477858611",
    "patient_name": "John Doe",
    "outreach_type": "form"
  }'
```

**Response**:
```json
{
  "agent": "OutreachAgent",
  "workflow": "patient_outreach",
  "patient_name": "John Doe",
  "phone_number": "+917477858611",
  "outreach_type": "form",
  "success": true,
  "form_link_sent": true,
  "form_url": "https://forms.gle/A3btW17ssMiR9mZBA",
  "message_sid": "SM..."
}
```

### **Console Output**

```
======================================================================
[AI Agent] Starting patient outreach workflow
======================================================================
[AI Agent] Executing Google Form workflow for John Doe
[AI Agent] Step 1: Sending Google Form link via SMS
[MCP Server] Executing tool: send_form_link
[MCP SEND_FORM_LINK Tool] Sending Google Form link - to John Doe at +917477858611
[MCP SEND_FORM_LINK Tool] Form link sent successfully - Message SID: SM...
[MCP Server] Tool 'send_form_link' executed successfully
======================================================================
[AI Agent] Outreach workflow completed successfully
======================================================================
```

## 📋 Outreach Types Comparison

| Type | Tool Used | Patient Interaction | AI Summary | Care Team Notification |
|------|-----------|---------------------|------------|------------------------|
| **conversation** | `start_conversation` | 5 SMS questions | After all answers | Manual |
| **notification** | `send_sms` | One-time message | No | No |
| **reminder** | `send_sms` | One-time reminder | No | No |
| **form** | `send_form_link` | Google Form | After submission | Automatic |

## 🎯 Why Use Forms Instead of SMS?

### **Advantages of Google Forms**

✅ **Better UX**: Patient fills out form at their convenience  
✅ **Rich Input**: Support for multiple choice, dropdowns, scales  
✅ **Validation**: Built-in form validation  
✅ **Accessibility**: Works on any device with a browser  
✅ **Cost**: Single SMS vs. multiple SMS messages  
✅ **Data Quality**: Structured responses, less parsing errors  

### **When to Use SMS Conversations**

- Quick check-ins (1-2 questions)
- Urgent follow-ups
- Patients without internet access
- Real-time engagement needed

### **When to Use Google Forms**

- Comprehensive questionnaires (5+ questions)
- Post-discharge assessments
- Quality of life surveys
- Detailed symptom tracking

## 🔧 Configuration

### **Set Google Form URL in .env**

```bash
GOOGLE_FORM_URL=https://forms.gle/A3btW17ssMiR9mZBA
```

### **Google Apps Script Webhook**

The existing webhook at `/api/forms/webhook` automatically processes form submissions. No changes needed!

## 🧪 Testing

### **Test Form Outreach**

```bash
python3 test_mcp_flow.py
```

This will run test #5: "MCP Outreach (Google Form)"

### **Manual Test**

```bash
curl -X POST http://localhost:8080/api/mcp/outreach \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+917477858611",
    "patient_name": "Test Patient",
    "outreach_type": "form"
  }'
```

**Expected SMS**:
```
Hi Test Patient! 👋

Please complete your post-discharge health questionnaire:
https://forms.gle/A3btW17ssMiR9mZBA

This helps us ensure you're recovering well. Thank you!
```

## 📊 Complete Workflow Example

### **Step 1: Send Form Link**

```bash
POST /api/mcp/outreach
{
  "phone_number": "+917477858611",
  "patient_name": "John Doe",
  "outreach_type": "form"
}
```

### **Step 2: Patient Receives SMS**

```
Hi John Doe! 👋

Please complete your post-discharge health questionnaire:
https://forms.gle/A3btW17ssMiR9mZBA

This helps us ensure you're recovering well. Thank you!
```

### **Step 3: Patient Fills Form**

Patient clicks link → Opens Google Form → Fills out questions → Submits

### **Step 4: Google Apps Script Webhook**

```javascript
// Google Apps Script automatically sends to:
POST /api/forms/webhook
{
  "patient_name": "John Doe",
  "patient_phone": "+917477858611",
  "responses": {
    "How are you feeling?": "Good",
    "Pain level (1-10)": "3",
    "Taking medications?": "Yes",
    ...
  }
}
```

### **Step 5: MCP Processes Response**

```
[MCP Server] Executing tool: process_form_response
[MCP PROCESS_FORM_RESPONSE Tool] Processing form response - for patient: John Doe
[AI Service] Generating summary...
[Notification Service] Notifying care team...
[MCP PROCESS_FORM_RESPONSE Tool] Form response processed - Summary generated and care team notified
```

### **Step 6: Care Team Receives Summary**

**Email to Care Team**:
```
Subject: Patient Follow-up Summary - John Doe

Patient: John Doe
Phone: +917477858611
Date: May 21, 2026

Summary:
Patient reports feeling good with minimal pain (3/10). 
Taking medications as prescribed. No concerning symptoms.

Recommendation: Routine follow-up in 1 week.
```

## 🔄 Backward Compatibility

All existing endpoints still work:

- ✅ `/api/forms/send-link` - Old direct form sending
- ✅ `/api/forms/webhook` - Form submission webhook
- ✅ `/api/start-conversation` - Old SMS conversation
- ✅ `/api/mcp/outreach` with `outreach_type: "conversation"` - New SMS conversation

## 📈 Tool Registry Status

After this update, you now have **6 registered MCP tools**:

1. `send_sms` - Send SMS messages
2. `start_conversation` - Start SMS Q&A conversation
3. `generate_summary` - Generate AI summary from text
4. `summarize_form_response` - Summarize form responses
5. **`send_form_link`** - Send Google Form link (NEW)
6. **`process_form_response`** - Process form submission (NEW)

## 🎓 Key Benefits

### **For Developers**

- ✅ Modular tool architecture
- ✅ Easy to test and mock
- ✅ Clear separation of concerns
- ✅ Reusable components

### **For Healthcare Providers**

- ✅ Automated patient follow-up
- ✅ AI-powered insights
- ✅ Reduced manual work
- ✅ Better patient engagement

### **For Patients**

- ✅ Convenient form filling
- ✅ Single SMS instead of multiple
- ✅ Works on any device
- ✅ Better user experience

## 🚀 Next Steps

1. **Test the new form workflow**: `python3 test_mcp_flow.py`
2. **Update your .env**: Add `GOOGLE_FORM_URL`
3. **Try it out**: Send a form link to a test patient
4. **Monitor logs**: Watch the MCP flow in action

## 📝 Files Modified

- `mcp/tools/forms_tool.py` - NEW: Form tools implementation
- `mcp/tools/__init__.py` - Added forms tool exports
- `mcp/registry.py` - Registered new form tools
- `agent/outreach_agent.py` - Added form workflow
- `app.py` - Added form_url parameter, initialized FormsService
- `test_mcp_flow.py` - Added form workflow test

## ✅ Summary

You now have a complete **Google Forms MCP workflow** that:

1. ✅ Sends form link via MCP architecture
2. ✅ Processes form submissions automatically
3. ✅ Generates AI summaries
4. ✅ Notifies care team
5. ✅ Maintains backward compatibility
6. ✅ Provides detailed logging

**Default outreach type is now `form`** - The system will send Google Form links by default instead of structured SMS questions!

---

**Status**: ✅ Google Forms MCP Integration Complete  
**Tools Added**: 2 (send_form_link, process_form_response)  
**Total MCP Tools**: 6  
**Backward Compatible**: Yes
