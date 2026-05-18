# Google Form Response Summarization and Notification Flow

## Overview
When a patient submits the Google Form, the system automatically:
1. Saves the response to the database
2. Generates an AI summary of the patient's health status
3. Sends the summary to all care team members via email and SMS

## Complete Flow

### 1. Patient Receives Form Link
- Care team sends form link via `/api/forms/send-form-link` endpoint
- SMS sent to patient with Google Form URL
- Record created in `form_responses` table with `form_link_sent_at` timestamp

### 2. Patient Submits Form
- Patient fills out Google Form with health questions
- Google Apps Script triggers `onFormSubmit` function
- Script sends POST request to `/api/forms/webhook` with form data

### 3. Webhook Receives Response
- `FormsService.save_form_response()` processes the webhook payload
- Updates or creates `FormResponse` record in database
- Saves individual responses to database columns

### 4. AI Summary Generation (Automatic)
- `FormSummaryService.generate_form_summary()` is called
- Converts form responses to Q&A format
- Sends to AI service (`AIService.generate_discharge_summary()`)
- AI analyzes responses and generates:
  - **Summary Text**: Overall health status
  - **Key Insights**: Important concerns for care team
  - **Sentiment Analysis**: Patient's emotional state
  - **Patient Responses Summary**: Brief summary of what patient reported

### 5. Care Team Notification (Automatic)
- System queries database for patient's care team members
- `NotificationService.send_summary_to_care_team()` is called
- **Email Notifications**: Sent to ALL care team members
  - HTML formatted email with:
    - AI-generated summary
    - Key insights
    - Sentiment analysis
    - Full form responses
    - Alert if patient requested contact
- **SMS Notifications**: Sent to PRIMARY care team member only
  - Short summary with key insights

## Database Schema

### FormResponse Table
```sql
- id (Primary Key)
- patient_phone
- patient_name
- form_link_sent_at
- submitted_at
- recently_discharged
- medication_changes
- current_symptoms
- care_team_notes
- contact_request
- raw_responses (JSON)
- created_at
```

### CareTeamMember Table
```sql
- id (Primary Key)
- patient_id (Foreign Key to patients.id)
- name
- role (e.g., 'Nephrologist', 'Nurse', 'Dietitian')
- phone_number
- email
- specialty
- is_primary (Boolean)
- notes
- created_at
- updated_at
```

## API Endpoints

### Send Form Link
```http
POST /api/forms/send-form-link
Content-Type: application/json

{
  "phone_number": "+919677863998",
  "patient_name": "Kishore",
  "form_url": "https://forms.gle/nMNMGwuhhEXH5PyW9"
}
```

### Webhook (Receives Form Submissions)
```http
POST /api/forms/webhook
Content-Type: application/json

{
  "patient_phone": "+919677863998",
  "patient_name": "Kishore",
  "submitted_at": "2026-05-18T10:00:00",
  "responses": {
    "recently_discharged": "Yes",
    "medication_changes": "Yes, new blood pressure medication",
    "current_symptoms": "Mild swelling in feet",
    "care_team_notes": "Feeling better overall",
    "contact_request": "Yes"
  }
}
```

**Response includes AI summary:**
```json
{
  "success": true,
  "record_id": 1,
  "patient_phone": "+919677863998",
  "patient_name": "Kishore",
  "submitted_at": "2026-05-18T10:00:00",
  "responses_saved": {...},
  "summary_generated": true,
  "summary": {
    "summary": {
      "summary_text": "Patient reports recent discharge...",
      "key_insights": "Mild swelling noted, medication changes...",
      "sentiment_analysis": "Patient appears positive about recovery",
      "patient_responses_summary": "Recently discharged, new medications..."
    },
    "notifications": {
      "emails_sent": 5,
      "sms_sent": 1,
      "errors": []
    }
  }
}
```

### Care Team Management
```http
# Add care team member
POST /api/care-team/members
{
  "patient_id": 1,
  "name": "Dr. Sarah Johnson",
  "role": "Nephrologist",
  "phone_number": "+1-555-0101",
  "email": "sarah.johnson@hospital.com",
  "specialty": "Nephrology",
  "is_primary": true
}

# Get patient's care team
GET /api/care-team/patient/{patient_id}

# Get primary care member
GET /api/care-team/patient/{patient_id}/primary
```

## Configuration

### Required Environment Variables
```bash
# AI Configuration
GOOGLE_API_KEY=your_gemini_api_key
AI_PROVIDER=gemini

# Email Configuration (for care team notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@hospital.com

# Twilio (for SMS notifications)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
```

## Setup Instructions

### 1. Database Setup
```bash
# Run seed script to add sample care team members
python seed_care_team.py
```

### 2. Configure Email
For Gmail:
1. Enable 2-factor authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`:
   ```
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_16_char_app_password
   ```

### 3. Update Google Apps Script
- Copy updated `google_apps_script.js`
- Update `WEBHOOK_URL` with your tunnel URL
- Deploy script to your Google Form

### 4. Test the Flow
```bash
# 1. Send form link
curl -X POST http://localhost:8080/api/forms/send-form-link \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919677863998",
    "patient_name": "Kishore",
    "form_url": "https://forms.gle/nMNMGwuhhEXH5PyW9"
  }'

# 2. Patient submits form (via Google Form)

# 3. Check that care team received emails and SMS
```

## Services Architecture

```
FormsService
├── save_form_response()
│   ├── Save to database
│   └── _generate_and_notify_care_team()
│       ├── FormSummaryService.generate_form_summary()
│       │   └── AIService.generate_discharge_summary()
│       └── NotificationService.send_summary_to_care_team()
│           ├── Send emails to all members
│           └── Send SMS to primary member
```

## Email Template Preview

The care team receives a formatted HTML email with:
- **Header**: Patient name and form type
- **AI Summary Section**: Overall health status
- **Key Insights Section**: Important concerns
- **Sentiment Analysis Section**: Patient's emotional state
- **Patient Responses Section**: All form answers
- **Alert Section**: If patient requested contact (highlighted)

## Troubleshooting

### No emails sent
- Check SMTP credentials in `.env`
- Verify care team members have email addresses
- Check spam folder

### No SMS sent
- Only primary care team member receives SMS
- Verify `is_primary=True` for at least one member
- Check Twilio credentials

### AI summary not generated
- Verify `GOOGLE_API_KEY` is set
- Check AI service logs for errors
- Ensure `AI_PROVIDER=gemini` in `.env`

### Care team not found
- Ensure patient exists in `patients` table
- Run `seed_care_team.py` to add sample members
- Verify patient phone number matches

## Next Steps

1. **Run seed script**: `python seed_care_team.py`
2. **Configure email**: Add SMTP credentials to `.env`
3. **Test form submission**: Submit Google Form and verify notifications
4. **Monitor logs**: Check for any errors in summarization or notification
