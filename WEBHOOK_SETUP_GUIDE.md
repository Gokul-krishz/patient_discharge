# Twilio Webhook Setup & Patient Reply API Guide

## 🎯 Complete SMS Conversation Flow

```
1. Start Conversation (API)
   ↓
2. Patient receives Q1 via SMS
   ↓
3. Patient replies → Twilio Webhook → Your Server
   ↓
4. Server stores reply → sends Q2
   ↓
5. Repeat until all questions answered
   ↓
6. Fetch replies via GET API
```

## 📡 New API Endpoints

### 1. **Get All Patient Replies**
```
GET /api/patient-replies/{phone_number}
```

**Example:**
```bash
GET /api/patient-replies/+919715441374
```

**Response:**
```json
{
  "patient_name": "John",
  "phone_number": "+919715441374",
  "total_replies": 3,
  "replies": [
    {
      "conversation_id": 1,
      "question_key": "feeling_after_discharge",
      "reply_text": "Good",
      "timestamp": "2026-05-14T11:30:00",
      "conversation_status": "active"
    },
    {
      "conversation_id": 1,
      "question_key": "shortness_of_breath",
      "reply_text": "NO",
      "timestamp": "2026-05-14T11:32:00",
      "conversation_status": "active"
    },
    {
      "conversation_id": 1,
      "question_key": "dialysis_session",
      "reply_text": "YES",
      "timestamp": "2026-05-14T11:35:00",
      "conversation_status": "active"
    }
  ]
}
```

### 2. **Get Latest Reply**
```
GET /api/latest-reply/{phone_number}
```

**Example:**
```bash
GET /api/latest-reply/+919715441374
```

**Response:**
```json
{
  "patient_name": "John",
  "phone_number": "+919715441374",
  "latest_reply": {
    "conversation_id": 1,
    "question_key": "dialysis_session",
    "reply_text": "YES",
    "timestamp": "2026-05-14T11:35:00",
    "conversation_status": "active"
  }
}
```

### 3. **Twilio Webhook (Receives Patient SMS)**
```
POST /webhook/sms
```

This endpoint is called **automatically by Twilio** when a patient replies.

## 🔧 Twilio Webhook Configuration

### Step 1: Expose Your Local Server (For Testing)

Use **ngrok** to create a public URL:

```bash
# Install ngrok
brew install ngrok

# Start ngrok tunnel
ngrok http 8080
```

You'll get a URL like:
```
https://abc123.ngrok.io
```

### Step 2: Configure Twilio Webhook

1. Go to **Twilio Console**: https://console.twilio.com/
2. Navigate to: **Phone Numbers → Manage → Active Numbers**
3. Click on your phone number
4. Scroll to **Messaging Configuration**
5. Set **"A MESSAGE COMES IN"** webhook:
   ```
   https://abc123.ngrok.io/webhook/sms
   ```
6. Method: **HTTP POST**
7. Click **Save**

### Step 3: Test the Flow

**In Swagger (`http://localhost:8080/swagger`):**

1. **Start a conversation:**
```json
POST /api/start-conversation
{
  "phone_number": "+919715441374",
  "patient_name": "John"
}
```

2. **Patient receives SMS on their phone:**
```
Hi John! 👋 I'm your discharge care assistant. 
How are you feeling after your discharge? 
(e.g., Good, Fair, Poor)
```

3. **Patient replies:** `Good`

4. **Twilio webhook automatically:**
   - Receives the reply
   - Stores it in database
   - Sends next question

5. **Check replies in Swagger:**
```
GET /api/patient-replies/+919715441374
```

## 📊 Complete API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/start-conversation` | POST | Start check-in conversation |
| `/api/patient-replies/{phone}` | GET | Get all patient replies |
| `/api/latest-reply/{phone}` | GET | Get most recent reply |
| `/api/conversation/{id}` | GET | Get full Q&A for conversation |
| `/api/conversations` | GET | List all conversations |
| `/webhook/sms` | POST | Twilio webhook (auto-called) |

## 🧪 Testing Without Twilio (Manual)

You can manually simulate patient replies for testing:

```python
import requests

# Simulate Twilio webhook call
response = requests.post(
    'http://localhost:8080/webhook/sms',
    data={
        'From': '+919715441374',
        'Body': 'Good'
    }
)
```

## 🔍 Database Tables

### **patients**
- id, name, phone_number, discharge_summary, created_at

### **conversations**
- id, patient_id, status, current_question_index, created_at, completed_at

### **messages**
- id, conversation_id, direction (inbound/outbound), content, question_key, timestamp

## 📱 Example Complete Flow

```bash
# 1. Start conversation
curl -X POST http://localhost:8080/api/start-conversation \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919715441374",
    "patient_name": "John"
  }'

# Response: Patient receives Q1 via SMS

# 2. Patient replies "Good" → Twilio webhook triggered automatically

# 3. Get all replies
curl http://localhost:8080/api/patient-replies/+919715441374

# 4. Get latest reply
curl http://localhost:8080/api/latest-reply/+919715441374

# 5. Get full conversation
curl http://localhost:8080/api/conversation/1
```

## 🎯 Production Deployment

For production, replace ngrok with:

1. **Deploy to cloud** (Heroku, AWS, Azure, etc.)
2. **Get permanent URL**: `https://your-app.herokuapp.com`
3. **Update Twilio webhook**: `https://your-app.herokuapp.com/webhook/sms`
4. **Use PostgreSQL** (already configured!)

## 🔐 Security Notes

- ✅ Webhook validates Twilio requests
- ✅ Database stores all messages
- ✅ Phone numbers validated
- ✅ Error handling included

## 💡 Tips

1. **Test locally first** with ngrok
2. **Monitor ngrok console** to see webhook calls
3. **Check database** to verify replies are stored
4. **Use Swagger UI** for easy testing
5. **View logs** in terminal for debugging

---

**System Status:** ✅ Fully Functional
- SMS sending: ✅
- Webhook receiving: ✅
- Database storage: ✅
- Reply retrieval: ✅
