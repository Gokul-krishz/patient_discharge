# ADT Patient to Patient Table Workflow Guide

## Overview
This guide explains the complete workflow for transitioning patients from the ADT (Admission, Discharge, Transfer) system to the main Patient management system with form link distribution.

## Workflow Steps

### 1. Initial State: ADT Patient (Admitted)
- Patient exists in `adt_patients` table
- Status: `'Admitted'`
- `discharge_date`: `NULL`

### 2. Send Form Link (API Call)

**Endpoint:** `POST /api/forms/send-form-link`

**Request Body (using numeric ID):**
```json
{
    "patient_id": 1
}
```

**Note:** The ADT Patients API returns `patient_id` in format `P000001`, but the send-form-link endpoint accepts the numeric `id` value.

**Alternative (without ADT patient):**
```json
{
    "phone_number": "+919876543210",
    "patient_name": "John Doe"
}
```

### 3. Automatic Actions Performed

When `patient_id` is provided, the system automatically:

#### A. Updates ADT Patient Record
- ✅ Status: `'Admitted'` → `'Discharged'`
- ✅ `discharge_date`: Set to current timestamp

#### B. Creates/Updates Patient Record
- ✅ Creates new record in `patients` table (or updates existing)
- ✅ Copies data from ADT patient:
  - `name`
  - `phone_number`
  - `hospital`
  - `admission_date`
  - `discharge_date`
  - `discharge_summary`
- ✅ Sets `status`: `'Discharged'`
- ✅ Sets `follow_up`: `'Link Sent'`

#### C. Sends SMS
- ✅ Sends Google Form link via SMS to patient's phone number

#### D. Creates Form Response Record
- ✅ Creates record in `form_responses` table
- ✅ Sets `form_link_sent_at` to current timestamp

### 4. Patient Submits Form

When the patient submits the Google Form:

**Webhook:** `POST /api/forms/webhook`

**Automatic Actions:**
- ✅ Updates `form_responses` record with submission data
- ✅ Updates Patient `follow_up`: `'Link Sent'` → `'Completed'`
- ✅ Generates AI summary of responses
- ✅ Notifies care team members

## Database Schema

### ADT Patients Table
```sql
CREATE TABLE adt_patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    hospital VARCHAR(255),
    admission_date TIMESTAMP,
    discharge_date TIMESTAMP,
    status VARCHAR(50),  -- 'Admitted', 'Discharged'
    discharge_summary JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Patients Table
```sql
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    hospital VARCHAR(255),
    admission_date TIMESTAMP,
    discharge_date TIMESTAMP,
    status VARCHAR(50),  -- 'Admitted', 'Discharged'
    follow_up VARCHAR(50),  -- 'Pending', 'Link Sent', 'Completed'
    discharge_summary JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Form Responses Table
```sql
CREATE TABLE form_responses (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    patient_phone VARCHAR(20) NOT NULL,
    patient_name VARCHAR(255),
    form_link_sent_at TIMESTAMP,
    submitted_at TIMESTAMP,
    recently_discharged TEXT,
    medication_changes TEXT,
    current_symptoms TEXT,
    care_team_notes TEXT,
    contact_request TEXT,
    raw_responses JSON,
    summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Examples

### Example 0: Get ADT Patients List

```bash
curl http://localhost:5000/api/adt_patients
```

**Response:**
```json
{
  "total": 10,
  "patients": [
    {
      "patient_id": "P000001",
      "id": 1,
      "name": "Rajesh Kumar",
      "phone_number": "+919876543210",
      "hospital": "Apollo Hospital",
      "admission_date": "2026-05-18T09:30:00",
      "discharge_date": null,
      "status": "Admitted",
      "discharge_summary": null,
      "created_at": "2026-05-21T15:30:00"
    }
  ]
}
```

**Note:** Use the numeric `id` field (not `patient_id`) when calling the send-form-link endpoint.

### Example 1: Send Form Link Using ADT Patient ID

```bash
curl -X POST http://localhost:5000/api/forms/send-form-link \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1
  }'
```

**Response:**
```json
{
  "success": true,
  "record_id": 123,
  "patient_name": "Rajesh Kumar",
  "phone_number": "+919876543210",
  "form_url": "https://forms.google.com/...",
  "sms_sent": true,
  "message_sid": "SM...",
  "sent_at": "2026-05-21T15:30:00",
  "adt_patient_id": 1,
  "adt_status_updated": true
}
```

### Example 2: Send Form Link Without ADT Patient

```bash
curl -X POST http://localhost:5000/api/forms/send-form-link \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "patient_name": "John Doe"
  }'
```

### Example 3: Check Patient Status

```bash
# Get all ADT patients
curl http://localhost:5000/api/adt_patients

# Get all patients
curl http://localhost:5000/api/patients

# Get form responses for a patient
curl http://localhost:5000/api/forms/responses/+919876543210
```

## Testing the Workflow

### 1. Run Test Script
```bash
source venv/bin/activate
python test_adt_workflow.py
```

This will:
- Show all ADT patients with 'Admitted' status
- Provide a sample patient ID for testing
- Display the curl command to test the API

### 2. Send Form Link
Use the provided curl command or Postman to send the form link.

### 3. Verify Results
```bash
python test_adt_workflow.py check <patient_id>
```

This will show:
- ADT patient status and discharge date
- Patient record in patients table
- Form response record

### 4. Simulate Form Submission
```bash
curl -X POST http://localhost:5000/api/forms/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "patient_phone": "+919876543210",
    "patient_name": "Rajesh Kumar",
    "submitted_at": "2026-05-21T16:00:00",
    "responses": {
      "recently_discharged": "Yes",
      "medication_changes": "No changes",
      "current_symptoms": "Feeling better",
      "care_team_notes": "Recovery going well",
      "contact_request": "No"
    }
  }'
```

## Follow-up Status Flow

```
ADT Patient (Admitted)
         ↓
    [Send Form Link]
         ↓
Patient Created/Updated
follow_up: 'Link Sent'
         ↓
    [Patient Submits Form]
         ↓
follow_up: 'Completed'
```

## Status Transitions

### ADT Patient Status
- `'Admitted'` → `'Discharged'` (when form link is sent)

### Patient Follow-up Status
- `NULL` or `'Pending'` → `'Link Sent'` (when form link is sent)
- `'Link Sent'` → `'Completed'` (when form is submitted)

## Error Handling

### Common Errors

1. **ADT Patient Not Found**
   ```json
   {
     "error": "ADT Patient with ID 999 not found"
   }
   ```

2. **Missing Required Fields**
   ```json
   {
     "error": "Either patient_id OR (phone_number AND patient_name) must be provided"
   }
   ```

3. **No Google Form URL**
   ```json
   {
     "error": "No Google Form URL provided. Pass form_url or set GOOGLE_FORM_URL in .env"
   }
   ```

## Configuration

Ensure your `.env` file contains:
```env
GOOGLE_FORM_URL=https://forms.google.com/your-form-url
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

## Files Modified

1. **`api/forms_api.py`**
   - Updated `send_form_model` to accept `patient_id`
   - Modified endpoint to handle ADT patient workflow

2. **`services/forms_service.py`**
   - Updated `send_form_link()` method
   - Added ADT patient status update logic
   - Added Patient record creation/update logic

3. **`models/database.py`**
   - No changes needed (tables already support the workflow)

## Integration Points

### Frontend Integration
```javascript
// Send form link from ADT patient list
async function sendFormLink(adtPatientId) {
  const response = await fetch('/api/forms/send-form-link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: adtPatientId })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Form link sent successfully');
    // Refresh patient lists
  }
}
```

### Monitoring
```sql
-- Check patients awaiting form submission
SELECT p.name, p.phone_number, p.follow_up, fr.form_link_sent_at
FROM patients p
JOIN form_responses fr ON p.phone_number = fr.patient_phone
WHERE p.follow_up = 'Link Sent'
  AND fr.submitted_at IS NULL;

-- Check completed forms
SELECT p.name, p.phone_number, fr.submitted_at
FROM patients p
JOIN form_responses fr ON p.phone_number = fr.patient_phone
WHERE p.follow_up = 'Completed'
  AND fr.submitted_at IS NOT NULL
ORDER BY fr.submitted_at DESC;
```

## Next Steps

1. ✅ ADT patient workflow implemented
2. ✅ Patient record creation/update implemented
3. ✅ Follow-up status tracking implemented
4. 🔄 Frontend UI for ADT patient management (pending)
5. 🔄 Dashboard for monitoring form submissions (pending)
6. 🔄 Automated reminders for pending forms (pending)
