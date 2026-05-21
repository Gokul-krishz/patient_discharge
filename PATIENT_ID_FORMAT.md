# Patient ID Format Documentation

## Overview
The ADT Patients API now returns a formatted `patient_id` field in the format `P000001` for better readability and display purposes.

## API Response Format

### GET /api/adt_patients

**Response includes both formats:**
```json
{
  "total": 10,
  "patients": [
    {
      "patient_id": "P000001",  // ← Formatted for display
      "id": 1,                   // ← Numeric ID for internal use
      "name": "Rajesh Kumar",
      "phone_number": "+919876543210",
      "hospital": "Apollo Hospital",
      "status": "Admitted"
    },
    {
      "patient_id": "P000002",
      "id": 2,
      "name": "Priya Sharma",
      "phone_number": "+919876543211",
      "hospital": "Fortis Hospital",
      "status": "Admitted"
    }
  ]
}
```

## Field Usage

### `patient_id` (String)
- **Format:** `P000001`, `P000002`, etc.
- **Purpose:** Display in UI, reports, and user-facing interfaces
- **Padding:** 6 digits with leading zeros
- **Examples:**
  - ID 1 → `P000001`
  - ID 42 → `P000042`
  - ID 999 → `P000999`
  - ID 1234 → `P001234`

### `id` (Integer)
- **Format:** Numeric (1, 2, 3, etc.)
- **Purpose:** Internal API calls, database operations
- **Use this for:**
  - Sending form links: `POST /api/forms/send-form-link`
  - Database queries
  - Backend operations

## Frontend Integration

### Display Patient ID
```javascript
// Display formatted patient_id in UI
const patientCard = (patient) => {
  return `
    <div class="patient-card">
      <h3>${patient.patient_id}</h3>  <!-- Shows: P000001 -->
      <p>${patient.name}</p>
      <p>${patient.hospital}</p>
    </div>
  `;
};
```

### Send Form Link
```javascript
// Use numeric id for API calls
async function sendFormLink(patient) {
  const response = await fetch('/api/forms/send-form-link', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: patient.id  // ← Use numeric id, not patient_id
    })
  });
  
  return response.json();
}
```

### Complete Example
```javascript
// Fetch ADT patients
const response = await fetch('/api/adt_patients');
const data = await response.json();

// Display in table
data.patients.forEach(patient => {
  console.log(`Patient: ${patient.patient_id} - ${patient.name}`);
  // Output: Patient: P000001 - Rajesh Kumar
  
  // When user clicks "Send Form Link" button
  sendFormLink(patient);  // Uses patient.id internally
});
```

## API Endpoints

### 1. Get ADT Patients
```bash
GET /api/adt_patients
```
Returns both `patient_id` (formatted) and `id` (numeric)

### 2. Send Form Link
```bash
POST /api/forms/send-form-link
{
  "patient_id": 1  # Use numeric id
}
```

## Database Schema

The database table remains unchanged:
```sql
CREATE TABLE adt_patients (
    id SERIAL PRIMARY KEY,  -- Numeric ID (auto-increment)
    name VARCHAR(255),
    phone_number VARCHAR(20),
    ...
);
```

The formatting happens at the API layer, not in the database.

## Testing

### Test the Format
```bash
python test_patient_id_format.py
```

**Output:**
```
Numeric ID   Patient ID      Name                 Status
----------------------------------------------------------------------
1            P000001         Rajesh Kumar         Admitted
2            P000002         Priya Sharma         Admitted
3            P000003         Amit Patel           Admitted
...
```

### Test API Response
```bash
curl http://localhost:5000/api/adt_patients | jq '.patients[0]'
```

**Output:**
```json
{
  "patient_id": "P000001",
  "id": 1,
  "name": "Rajesh Kumar",
  "phone_number": "+919876543210",
  "hospital": "Apollo Hospital",
  "status": "Admitted"
}
```

## Migration Notes

### No Database Migration Required
- The `patient_id` field is generated dynamically
- No changes to database schema
- Existing data works without modification

### Frontend Changes Required
If you have existing frontend code:

**Before:**
```javascript
// Old code using id
<div>Patient ID: {patient.id}</div>
```

**After:**
```javascript
// New code using patient_id for display
<div>Patient ID: {patient.patient_id}</div>

// But still use id for API calls
sendFormLink(patient.id);
```

## Summary

| Field | Type | Format | Use Case |
|-------|------|--------|----------|
| `patient_id` | String | P000001 | Display in UI |
| `id` | Integer | 1 | API calls, database |

**Remember:** Display `patient_id`, but use `id` for operations! 🎯
