# Patient Discharge Follow-Up System - Setup Guide

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Twilio account (for SMS)
- Google API key (for Gemini AI)
- Google Form URL

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd windsurf-project
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Twilio (for SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Google AI
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-1.5-flash

# Google Form
GOOGLE_FORM_URL=https://forms.gle/your-form-id

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 5. Run Database Migrations

**Option A: Run all migrations at once (recommended)**

```bash
python setup_database.py
```

**Option B: Run migrations individually**

```bash
python migrate_database.py
python migrate_patients_table.py
python migrate_add_follow_up.py
```

### 6. (Optional) Seed Sample Data

```bash
python seed_sample_patients.py
python update_follow_up_status.py
```

### 7. Start the Application

```bash
python app.py
```

The API will be available at: `http://localhost:8080`

Swagger documentation: `http://localhost:8080/swagger`

## API Endpoints

### Patients

- `GET /api/patients/list` - Get paginated list of patients with filters
- `GET /api/patients/pending-followups` - Get patients with pending follow-ups
- `POST /api/patients/send-form-link` - Send form link to patient
- `GET /api/patients/hospitals` - Get list of hospitals

### Forms

- `POST /api/forms/webhook` - Webhook for Google Forms submissions
- `POST /api/forms/send-form-link` - Send form link via SMS

### Care Team

- `GET /api/care-team/patients/<patient_id>` - Get care team for patient
- `POST /api/care-team/patients/<patient_id>` - Add care team member

## Database Schema

### Tables

1. **patients** - Patient information
2. **form_responses** - Google Form submissions
3. **care_team_members** - Care team assignments
4. **conversations** - SMS conversation tracking
5. **messages** - Individual SMS messages

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running
- Check DATABASE_URL in `.env`
- Ensure database exists: `createdb your_database_name`

### Migration Errors

- Migrations are idempotent - safe to run multiple times
- If error persists, check PostgreSQL logs
- Ensure user has CREATE/ALTER permissions

### SMS Not Sending

- Verify Twilio credentials in `.env`
- Check Twilio phone number is verified
- Ensure recipient numbers are in E.164 format (+1234567890)

### AI Summary Not Generating

- Verify GOOGLE_API_KEY in `.env`
- Check API quota/limits
- Review logs for specific error messages

## Development

### Project Structure

```
windsurf-project/
├── api/                    # API endpoints
│   ├── forms_api.py
│   ├── patients_api.py
│   └── care_team_api.py
├── models/                 # Database models
│   └── database.py
├── services/              # Business logic
│   ├── forms_service.py
│   ├── gemini_forms_service.py
│   ├── sms_service.py
│   └── notification_service.py
├── config/                # Configuration
│   └── settings.py
├── migrate_*.py          # Database migrations
├── app.py                # Main application
└── requirements.txt      # Python dependencies
```

## Support

For issues or questions, please create an issue in the repository.
