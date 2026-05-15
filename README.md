# SMS Outreach and AI Summary System

A Python-based system for managing SMS outreach conversations with patients, featuring AI-generated questions, response validation, and summary generation for care teams.

## Features

- **AI-Generated Questions**: OpenAI dynamically generates questions based on patient context and conversation history
- **SMS Conversation Management**: Trigger and manage SMS conversations with patients one question at a time
- **AI Response Validation**: Uses OpenAI to validate patient responses and rephrase questions when needed
- **AI Summary Generation**: Automatically generates summaries including patient responses, sentiment analysis, and key insights
- **SMS Logging**: Complete audit trail of all SMS messages sent and received
- **Timeout Handling**: Automatically closes conversations after 48 hours of no response
- **Care Team Integration**: Links patients to care team members for notification
- **PostgreSQL Storage**: Robust database schema for all conversation data

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI**: OpenAI GPT-3.5-turbo
- **Task Scheduling**: APScheduler for timeout checks
- **Python Version**: 3.8+

## Project Structure

```
SMS_Outreach_and _AI_Summary/
├── app/
│   ├── __init__.py
│   ├── config.py              # Application configuration
│   ├── database.py            # Database connection setup
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic schemas for API
│   ├── scheduler.py           # Background task scheduler
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── patients.py        # Patient management endpoints
│   │   ├── conversation.py    # SMS conversation endpoints
│   │   ├── summaries.py       # AI summary endpoints
│   │   └── logs.py            # SMS log endpoints
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py      # OpenAI integration (question generation, validation, summary)
│       └── conversation_service.py  # Conversation logic
├── database/
│   └── schema.sql             # Database schema
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- OpenAI API key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE sms_outreach_db;
```

Run the schema:

```bash
psql -U your_username -d sms_outreach_db -f database/schema.sql
```

### 4. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/sms_outreach_db
OPENAI_API_KEY=your_openai_api_key_here
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True
RESPONSE_TIMEOUT_HOURS=48
```

### 5. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`

## API Endpoints

### Patients
- `POST /api/patients/` - Create a new patient
- `GET /api/patients/{patient_id}` - Get patient details
- `GET /api/patients/` - List all patients
- `POST /api/patients/care-team/` - Create care team member
- `GET /api/patients/care-team/` - List care team members

### Conversations
- `POST /api/conversations/trigger` - Trigger SMS conversation for a patient (AI generates first question)
- `POST /api/conversations/reply` - Process incoming SMS reply (AI validates and generates next question)
- `GET /api/conversations/{conversation_id}` - Get conversation details including Q&A history
- `GET /api/conversations/patient/{patient_id}` - Get patient's conversations

### Summaries
- `GET /api/summaries/conversation/{conversation_id}` - Get conversation summary
- `GET /api/summaries/patient/{patient_id}` - Get patient's summaries
- `GET /api/summaries/` - List all summaries

### SMS Logs
- `GET /api/logs/conversation/{conversation_id}` - Get conversation SMS logs
- `GET /api/logs/patient/{patient_id}` - Get patient's SMS logs
- `GET /api/logs/` - List all SMS logs

## Usage Example

### 1. Create a Patient

```bash
curl -X POST "http://localhost:8000/api/patients/" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT001",
    "phone_number": "+1234567890",
    "name": "John Doe",
    "medical_context": "Diabetes Type 2, hypertension",
    "care_team_member_ids": []
  }'
```

### 2. Trigger SMS Conversation

```bash
curl -X POST "http://localhost:8000/api/conversations/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT001"
  }'
```

This will:
- Create a new conversation
- AI generates the first question based on patient context
- Return the question text (your SMS integration will send it)

### 3. Process SMS Reply

```bash
curl -X POST "http://localhost:8000/api/conversations/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT001",
    "message_text": "I've been feeling better, thank you."
  }'
```

This will:
- Validate the response using AI
- Save Q&A pair to conversation history
- AI decides whether to ask another question or end conversation
- If continuing, AI generates next question based on conversation history
- Generate summary when conversation is complete

### 4. View Summary

```bash
curl -X GET "http://localhost:8000/api/summaries/conversation/1"
```

## SMS Integration

The system provides endpoints for triggering conversations and receiving replies. Your teammate's SMS integration should:

1. **Trigger endpoint** (`POST /api/conversations/trigger`):
   - Call this endpoint when you want to start a conversation
   - AI generates the first question based on patient context
   - Use the `next_question` field to get the question text
   - Send the question via your SMS provider
   - Store the `conversation_id` for future replies

2. **Reply endpoint** (`POST /api/conversations/reply`):
   - Call this endpoint when you receive an SMS from a patient
   - Pass the `patient_id` and `message_text`
   - AI validates the response and decides next action
   - Use the `next_question` field to send the next question (if any)
   - Handle `is_conversation_complete` flag to know when to stop

## Timeout Handling

The system includes a background scheduler that:
- Runs every hour
- Checks for conversations with no response for 48 hours (configurable)
- Automatically marks them as "timeout"
- Generates a summary indicating the timeout

## AI Features

### Question Generation
- **First Question**: AI generates an opening question based on patient's medical context
- **Follow-up Questions**: AI dynamically generates follow-up questions based on conversation history
- **Smart Decision Making**: AI decides when to continue asking questions vs. ending the conversation (max 5-6 questions to avoid overwhelming patients)

### Response Validation
- Checks if responses are meaningful and relevant
- Detects gibberish or completely irrelevant responses
- Can rephrase questions when responses are unclear

### Summary Generation
When a conversation completes, the AI generates:
- **Overall summary**: Comprehensive overview of the conversation
- **Patient responses summary**: Summary of all patient responses
- **Sentiment analysis**: How the patient seems to be feeling
- **Key insights**: Important information for care team members

## Database Schema

The system uses the following main tables:
- `patients`: Patient information and medical context
- `care_team_members`: Care team member details
- `patient_care_team`: Link between patients and care team
- `conversations`: SMS conversation sessions with Q&A history stored as JSON
- `sms_logs`: Complete audit trail of all SMS messages
- `ai_summaries`: AI-generated summaries for care teams

The `conversations` table stores Q&A pairs as JSON in the `qa_history` column, allowing flexible storage of AI-generated questions and patient responses without requiring a predefined question bank.

See `database/schema.sql` for the complete schema.

## Configuration

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `RESPONSE_TIMEOUT_HOURS`: Hours before conversation timeout (default: 48)
- `APP_HOST`: Application host (default: 0.0.0.0)
- `APP_PORT`: Application port (default: 8000)

## Future Enhancements

- Email notifications for care team members when summaries are generated
- Web dashboard for care team to view conversations and summaries
- Integration with electronic health records (EHR)
- Multi-language support
- Advanced response validation with custom rules
- Analytics and reporting dashboard

## Support

For issues or questions, please contact the development team.
