# SMS & Patient Chat Integration Guide

## 🎯 Overview

This system integrates **Twilio SMS** and **AI-powered chat** to enable automated patient communication after discharge.

## 📱 Features

### 1. **SMS Notifications**
- Send discharge summary notifications
- Send follow-up appointment reminders
- Track message delivery status

### 2. **AI-Powered Patient Chat**
- Answer patient questions about their discharge
- Context-aware responses based on discharge summary
- Emergency detection and appropriate responses
- Conversation history tracking

### 3. **Combined SMS + Chat**
- Answer patient questions via AI
- Automatically send response via SMS
- Perfect for automated patient support

## 🔧 Setup

### 1. Get Twilio Credentials

1. Sign up at https://www.twilio.com/
2. Get a phone number (Trial: free number, Production: buy number)
3. Find your credentials in Twilio Console:
   - Account SID
   - Auth Token
   - Phone Number

### 2. Configure `.env` File

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# AI Provider (for chat)
AI_PROVIDER=gemini
GOOGLE_API_KEY=your_google_api_key
```

### 3. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📡 API Endpoints

### 1. Send SMS Notification

**`POST /api/send-sms`**

Send discharge summary or follow-up reminder to patient.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "patient_name": "John Doe",
  "message_type": "discharge_summary",
  "details": "Optional appointment details"
}
```

**Message Types:**
- `discharge_summary`: Notify patient their summary is ready
- `follow_up`: Send appointment reminder

**Response:**
```json
{
  "success": true,
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "status": "queued",
  "to": "+1234567890",
  "message": "Hello John Doe, Your discharge summary is ready..."
}
```

### 2. Patient Chat (AI Response Only)

**`POST /api/patient-chat`**

Get AI response to patient question (no SMS sent).

**Request:**
```json
{
  "patient_id": "+1234567890",
  "question": "Can I take ibuprofen with my medications?",
  "discharge_summary": {
    "patient_name": "John Doe",
    "hospitalization_reason": "Fluid overload",
    "medication_changes": ["Started Furosemide 40mg daily"],
    "current_symptoms": ["Mild shortness of breath"],
    "outcomes_after_discharge": ["Stable condition"],
    "care_team_updates": ["Nephrologist follow-up in 3 days"],
    "diet_restrictions": ["Low sodium diet"],
    "risk_indicators": ["High readmission risk"]
  }
}
```

**Response:**
```json
{
  "patient_id": "+1234567890",
  "question": "Can I take ibuprofen with my medications?",
  "response": "I recommend checking with your doctor before taking ibuprofen, as it can interact with Furosemide and may affect your kidney function. Please call your nephrologist before your follow-up appointment.",
  "is_emergency": false
}
```

### 3. Patient Chat + SMS

**`POST /api/patient-chat-sms`**

Get AI response AND send it via SMS to patient.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "question": "What foods should I avoid?",
  "discharge_summary": {
    "patient_name": "John Doe",
    "diet_restrictions": ["Low sodium diet", "Fluid restriction"]
  }
}
```

**Response:**
```json
{
  "question": "What foods should I avoid?",
  "response": "Based on your low sodium diet, avoid processed foods, canned soups, deli meats, and salty snacks. Also limit fluids as prescribed. Focus on fresh fruits, vegetables, and lean proteins.",
  "is_emergency": false,
  "sms_sent": true,
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

## 🔄 Complete Workflow Example

### Scenario: Patient Discharge Process

```python
import requests

BASE_URL = "http://localhost:8080/api"

# Step 1: Upload and process discharge report
with open('discharge_report.pdf', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/discharge-summary",
        files={'file': f}
    )
    summary = response.json()

# Step 2: Send SMS notification to patient
sms_response = requests.post(
    f"{BASE_URL}/send-sms",
    json={
        "phone_number": "+1234567890",
        "patient_name": summary['summary']['patient_name'],
        "message_type": "discharge_summary"
    }
)

# Step 3: Patient texts back with a question
# This would come from Twilio webhook in production
patient_question = "Can I exercise?"

# Step 4: Get AI response and send via SMS
chat_response = requests.post(
    f"{BASE_URL}/patient-chat-sms",
    json={
        "phone_number": "+1234567890",
        "question": patient_question,
        "discharge_summary": summary['summary']
    }
)

print(f"Response sent to patient: {chat_response.json()['response']}")
```

## 🚨 Emergency Detection

The system automatically detects emergency keywords:
- chest pain
- can't breathe
- severe pain
- bleeding
- unconscious
- heart attack
- stroke
- seizure

**Emergency Response:**
```
⚠️ EMERGENCY: Please call 911 immediately or go to the nearest ER. 
This is a medical emergency.
```

## 💬 Conversation Features

### Context Awareness
The AI maintains conversation history and references:
- Patient's specific medications
- Their diet restrictions
- Follow-up appointments
- Current symptoms

### Example Conversation:

**Patient:** "What medications am I taking?"

**AI:** "You're currently taking Furosemide 40mg daily. This was started during your hospitalization for fluid overload. Take it in the morning as prescribed."

**Patient:** "Can I drink coffee?"

**AI:** "Yes, but remember your fluid restriction. Coffee counts toward your daily fluid limit. Try to keep total fluids (including coffee) to the amount your doctor recommended."

## 🔐 Security & Privacy

### HIPAA Considerations
1. **Encryption**: All SMS sent via Twilio are encrypted in transit
2. **No PHI Storage**: Conversation history stored in memory only (use database in production)
3. **Access Control**: Implement authentication in production
4. **Audit Logging**: Log all patient communications

### Production Recommendations
```python
# Use database for conversation history
from sqlalchemy import create_engine

# Encrypt sensitive data
from cryptography.fernet import Fernet

# Add authentication
from flask_jwt_extended import jwt_required

@ns.route('/patient-chat')
class PatientChat(Resource):
    @jwt_required()  # Require authentication
    def post(self):
        # Your code here
```

## 📊 Twilio Webhook Integration

For receiving patient SMS responses:

```python
@app.route('/webhook/sms', methods=['POST'])
def receive_sms():
    """Webhook for incoming SMS from patients"""
    from twilio.twiml.messaging_response import MessagingResponse
    
    # Get incoming message
    from_number = request.form.get('From')
    body = request.form.get('Body')
    
    # Get patient's discharge summary from database
    discharge_summary = get_patient_summary(from_number)
    
    # Get AI response
    response_text = chat_service.get_response(
        from_number,
        discharge_summary,
        body
    )
    
    # Send response via Twilio
    resp = MessagingResponse()
    resp.message(response_text)
    
    return str(resp)
```

## 📈 Monitoring & Analytics

Track important metrics:
- SMS delivery rates
- Response times
- Emergency detections
- Common patient questions
- Conversation lengths

## 🧪 Testing

### Test SMS (without sending)
```python
# Mock Twilio in tests
from unittest.mock import Mock, patch

@patch('services.sms_service.Client')
def test_send_sms(mock_client):
    sms_service = SMSService()
    result = sms_service.send_sms('+1234567890', 'Test message')
    assert result['success'] == True
```

### Test Chat
```python
def test_patient_chat():
    chat_service = PatientChatService()
    response = chat_service.get_response(
        'test_patient',
        {'patient_name': 'Test'},
        'What should I do?'
    )
    assert len(response) > 0
```

## 💰 Cost Considerations

### Twilio Pricing (US, as of 2024)
- **SMS**: $0.0079 per message
- **Phone Number**: $1.15/month

### Example Costs
- 100 patients × 5 messages each = 500 messages
- Cost: 500 × $0.0079 = **$3.95**
- Plus phone number: **$1.15**
- **Total: ~$5/month for 100 patients**

### AI API Costs
- **Gemini**: Free tier available, then pay-per-use
- **OpenAI**: ~$0.002 per conversation

## 🎓 Best Practices

1. **Keep responses concise** - SMS has 160 char limit (though Twilio handles longer)
2. **Use simple language** - Avoid medical jargon
3. **Always include disclaimer** - "This is not medical advice"
4. **Emergency protocol** - Always direct emergencies to 911
5. **Follow-up reminders** - Send appointment reminders 24-48 hours before
6. **Opt-out option** - Allow patients to stop messages (reply STOP)
7. **Business hours** - Consider time zones when sending

## 🔄 Future Enhancements

- [ ] Multi-language support
- [ ] Voice call integration
- [ ] Appointment scheduling via SMS
- [ ] Medication reminder system
- [ ] Photo upload for wound care
- [ ] Video call integration
- [ ] Integration with EHR systems
