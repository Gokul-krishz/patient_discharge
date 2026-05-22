# Automatic SMS Trigger on Patient Discharge - Complete Guide

## 🎯 Overview

Automatically send SMS with Google Form link when a patient is discharged, using database triggers and a background listener.

## 📋 Architecture

```
External System → Discharge API → Patient Table → DB Trigger → Listener → SMS Service
                                                                              ↓
                                                                         Twilio SMS
```

## 🚀 Setup (One-Time)

### Step 1: Create Database Trigger

```bash
python create_patient_trigger.py
```

**What it does:**
- Creates PostgreSQL function `notify_patient_discharge()`
- Creates trigger on `patients` table
- Fires when patient status changes to 'Discharged'
- Sends notification via PostgreSQL NOTIFY

### Step 2: Start Background Listener

```bash
python patient_discharge_listener.py
```

**What it does:**
- Listens for discharge notifications
- Automatically sends SMS via Twilio
- Updates patient follow_up status
- Logs all activity

**Keep it running:**
```bash
# Run in background (macOS/Linux)
nohup python3 patient_discharge_listener.py > listener.log 2>&1 &

# Or use screen
screen -S sms-listener
python3 patient_discharge_listener.py
# Press Ctrl+A then D to detach
```

---

## 📡 API Endpoints

### 1. Trigger Single Discharge

**POST** `/api/discharge/trigger`

**Request:**
```json
{
  "patient_name": "John Doe",
  "phone_number": "+919876543210",
  "hospital": "Apollo Hospitals",
  "admission_date": "2024-05-15",
  "discharge_date": "2024-05-20"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Patient created and discharge triggered",
  "patient_id": "P000009",
  "patient_name": "John Doe",
  "phone_number": "+919876543210",
  "status": "Discharged",
  "follow_up": "Pending",
  "note": "SMS will be sent automatically by the listener"
}
```

**What happens:**
1. Patient created/updated in database
2. Status set to 'Discharged'
3. Database trigger fires
4. Listener receives notification
5. SMS sent automatically
6. Follow-up status updated to 'Link Sent'

---

### 2. Update Patient Status

**POST** `/api/discharge/update-status`

**Request:**
```json
{
  "patient_id": "P000009",
  "status": "Discharged"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Status updated from Admitted to Discharged. SMS will be sent automatically.",
  "patient_id": "P000009",
  "patient_name": "John Doe",
  "old_status": "Admitted",
  "new_status": "Discharged",
  "follow_up": "Pending"
}
```

---

### 3. Batch Discharge Trigger

**POST** `/api/discharge/batch-trigger`

**Request:**
```json
[
  {
    "patient_name": "Patient 1",
    "phone_number": "+919876543210",
    "hospital": "Apollo Hospitals"
  },
  {
    "patient_name": "Patient 2",
    "phone_number": "+919876543211",
    "hospital": "Fortis Hospital"
  }
]
```

**Response:**
```json
{
  "success": true,
  "processed": 2,
  "failed": 0,
  "results": [
    {
      "patient_id": "P000010",
      "name": "Patient 1",
      "phone": "+919876543210",
      "status": "success"
    },
    {
      "patient_id": "P000011",
      "name": "Patient 2",
      "phone": "+919876543211",
      "status": "success"
    }
  ],
  "errors": null
}
```

---

## 🧪 Testing

### Test 1: Manual Trigger via API

```bash
curl -X POST http://localhost:8080/api/discharge/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "patient_name": "Test Patient",
    "phone_number": "+919876543210",
    "hospital": "Test Hospital",
    "discharge_date": "2024-05-21"
  }'
```

### Test 2: Direct Database Insert

```sql
INSERT INTO patients (name, phone_number, hospital, status, discharge_date, follow_up)
VALUES ('Test Patient 2', '+919876543211', 'Test Hospital', 'Discharged', NOW(), 'Pending');
```

### Test 3: Update Existing Patient

```bash
curl -X POST http://localhost:8080/api/discharge/update-status \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P000001",
    "status": "Discharged"
  }'
```

---

## 📊 Monitoring

### Check Listener Status

```bash
# View listener logs
tail -f listener.log

# Or if running in screen
screen -r sms-listener
```

### Expected Output:
```
[2026-05-21 12:30:00] ✓ Listening for patient discharge notifications...
[2026-05-21 12:30:15] 📢 Received notification: INSERT - Patient John Doe
[2026-05-21 12:30:15] Processing discharge for: John Doe (ID: 9)
[2026-05-21 12:30:16] ✓ SMS sent successfully to John Doe (+919876543210)
[2026-05-21 12:30:16]   Message ID: SM1234567890abcdef
[2026-05-21 12:30:16] ✅ Processed successfully!
```

### Check Database Trigger

```sql
-- Verify trigger exists
SELECT tgname, tgenabled 
FROM pg_trigger 
WHERE tgname = 'patient_discharge_trigger';

-- View trigger function
\df notify_patient_discharge
```

---

## 🔄 Workflow Diagram

```
┌─────────────────┐
│ External System │
│  (Hospital EHR) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ POST /discharge │
│    /trigger     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Patient Table   │
│ INSERT/UPDATE   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Database Trigger│
│ (PostgreSQL)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ NOTIFY Channel  │
│ 'patient_       │
│  discharged'    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Background      │
│ Listener        │
│ (Python)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FormsService    │
│ send_form_link()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Twilio SMS API  │
│ Send SMS        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Patient Receives│
│ SMS with Form   │
└─────────────────┘
```

---

## 🛠️ Integration Examples

### Example 1: Hospital EHR Integration

```python
import requests

def discharge_patient_from_ehr(patient_data):
    """Called when patient is discharged in hospital system"""
    
    response = requests.post(
        'http://your-api.com/api/discharge/trigger',
        json={
            'patient_name': patient_data['name'],
            'phone_number': patient_data['phone'],
            'hospital': patient_data['hospital'],
            'admission_date': patient_data['admission_date'],
            'discharge_date': patient_data['discharge_date']
        }
    )
    
    return response.json()
```

### Example 2: Scheduled Batch Processing

```python
import requests
from datetime import datetime

def process_daily_discharges():
    """Process all patients discharged today"""
    
    # Get discharged patients from your system
    discharged_patients = get_todays_discharges()
    
    # Batch trigger
    response = requests.post(
        'http://your-api.com/api/discharge/batch-trigger',
        json=discharged_patients
    )
    
    result = response.json()
    print(f"Processed: {result['processed']}, Failed: {result['failed']}")
```

### Example 3: Webhook from External System

```python
from flask import Flask, request

@app.route('/webhook/discharge', methods=['POST'])
def handle_discharge_webhook():
    """Receive discharge webhook from external system"""
    
    data = request.json
    
    # Forward to discharge trigger
    response = requests.post(
        'http://localhost:8080/api/discharge/trigger',
        json={
            'patient_name': data['patient']['name'],
            'phone_number': data['patient']['contact']['phone'],
            'hospital': data['facility']['name'],
            'discharge_date': data['discharge']['date']
        }
    )
    
    return response.json()
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Twilio (required for SMS)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Google Form (required)
GOOGLE_FORM_URL=https://forms.gle/your-form-id

# Database (required)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

---

## 🚨 Troubleshooting

### SMS Not Sending?

1. **Check listener is running:**
   ```bash
   ps aux | grep patient_discharge_listener
   ```

2. **Check listener logs:**
   ```bash
   tail -f listener.log
   ```

3. **Test Twilio credentials:**
   ```bash
   python -c "from services.sms_service import SMSService; sms = SMSService(); print(sms.send_sms('+919876543210', 'Test'))"
   ```

### Trigger Not Firing?

1. **Verify trigger exists:**
   ```sql
   SELECT * FROM pg_trigger WHERE tgname = 'patient_discharge_trigger';
   ```

2. **Check trigger is enabled:**
   ```sql
   ALTER TABLE patients ENABLE TRIGGER patient_discharge_trigger;
   ```

3. **Test manually:**
   ```sql
   UPDATE patients SET status = 'Discharged' WHERE id = 1;
   ```

### Listener Not Receiving Notifications?

1. **Check PostgreSQL connection:**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

2. **Test NOTIFY manually:**
   ```sql
   NOTIFY patient_discharged, '{"patient_id": 1, "name": "Test"}';
   ```

3. **Restart listener:**
   ```bash
   pkill -f patient_discharge_listener
   python3 patient_discharge_listener.py
   ```

---

## 📈 Production Deployment

### Run as System Service (Linux)

Create `/etc/systemd/system/patient-sms-listener.service`:

```ini
[Unit]
Description=Patient Discharge SMS Listener
After=network.target postgresql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/windsurf-project
ExecStart=/path/to/venv/bin/python patient_discharge_listener.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable patient-sms-listener
sudo systemctl start patient-sms-listener
sudo systemctl status patient-sms-listener
```

---

## ✅ Summary

**Setup:**
1. Run `python create_patient_trigger.py` (one-time)
2. Start `python patient_discharge_listener.py` (keep running)

**Usage:**
- POST to `/api/discharge/trigger` with patient data
- Or update patient status to 'Discharged'
- SMS sent automatically!

**Benefits:**
- ✅ Fully automated
- ✅ Real-time processing
- ✅ No manual intervention
- ✅ Reliable (database-driven)
- ✅ Scalable (handles batch operations)

🎉 **Your SMS will now be triggered automatically whenever a patient is discharged!**
