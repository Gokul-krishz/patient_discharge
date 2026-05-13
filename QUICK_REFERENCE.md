# Quick Reference Card

## 🚀 Start Application

```bash
source venv/bin/activate
python app.py
```

Access: `http://localhost:8080/swagger`

## 📡 API Endpoints

### 1. Extract Text
```bash
POST /api/extract-text
# Upload: PDF, DOCX, TXT, Image
# Returns: Plain text
```

### 2. Discharge Summary (AI)
```bash
POST /api/discharge-summary
# Upload: Discharge document
# Returns: Structured JSON summary
```

### 3. Send SMS
```bash
POST /api/send-sms
{
  "phone_number": "+1234567890",
  "patient_name": "John Doe",
  "message_type": "discharge_summary"
}
```

### 4. Patient Chat
```bash
POST /api/patient-chat
{
  "patient_id": "patient123",
  "question": "Can I exercise?",
  "discharge_summary": {...}
}
```

### 5. Chat + SMS
```bash
POST /api/patient-chat-sms
{
  "phone_number": "+1234567890",
  "question": "What can I eat?",
  "discharge_summary": {...}
}
```

## 🔧 Configuration (.env)

```env
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_key
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890
```

## 📁 Project Structure

```
config/         → Settings
models/         → Data structures
services/       → Business logic
  ├── file_extractor.py
  ├── ai_service.py
  ├── sms_service.py
  └── patient_chat_service.py
app.py          → API routes
```

## 🛠️ Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python app.py

# Test endpoint
curl -X POST http://localhost:8080/api/health

# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

## 🔍 Troubleshooting

**Port in use:**
```bash
lsof -ti:8080 | xargs kill -9
```

**Import errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Twilio not working:**
- Check .env has correct credentials
- Verify phone number format: +1234567890
- Check Twilio console for errors

**AI not working:**
- Verify API key in .env
- Check AI_PROVIDER setting
- Test with /api/health endpoint

## 📊 Response Formats

**Discharge Summary:**
```json
{
  "patient_name": "...",
  "hospitalization_reason": "...",
  "medication_changes": [...],
  "current_symptoms": [...],
  "outcomes_after_discharge": [...],
  "care_team_updates": [...],
  "diet_restrictions": [...],
  "risk_indicators": [...]
}
```

**SMS Response:**
```json
{
  "success": true,
  "message_sid": "SMxxx",
  "status": "queued",
  "to": "+1234567890"
}
```

## 🎯 Testing Workflow

1. Upload discharge PDF → `/api/discharge-summary`
2. Get structured summary
3. Send SMS → `/api/send-sms`
4. Ask question → `/api/patient-chat`
5. Send answer via SMS → `/api/patient-chat-sms`

## 📚 Documentation

- `README.md` - Main documentation
- `SMS_CHAT_GUIDE.md` - SMS/Chat details
- `PROJECT_STRUCTURE.md` - Code organization
- `ARCHITECTURE.md` - System design
- `COMPLETE_SYSTEM_OVERVIEW.md` - Full overview

## 🔐 Security Checklist

- [ ] .env file not in git
- [ ] API keys configured
- [ ] File size limits set
- [ ] File types validated
- [ ] Temp files cleaned up

## 💡 Tips

- Use Swagger UI for testing
- Check /api/health for service status
- Emergency keywords trigger special response
- Conversation history maintained per patient
- SMS costs ~$0.0079 per message
