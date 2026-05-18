"""
Google Forms Service
Sends Google Form health questionnaire link to patients via SMS
and stores submitted responses in PostgreSQL.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from models.database import FormResponse, Patient, SessionLocal
from services.sms_service import SMSService


class FormsService:
    """Handles sending Google Form links and storing form responses"""

    def __init__(self, google_form_url: str = None):
        self.sms_service = SMSService()
        # Default form URL - can be overridden per request
        self.default_form_url = google_form_url or ""

    def _get_db(self):
        return SessionLocal()

    def send_form_link(
        self,
        phone_number: str,
        patient_name: str,
        form_url: str = None
    ) -> Dict[str, Any]:
        """
        Send Google Form health questionnaire link to patient via SMS.
        Records the send event in the database.
        """
        url = form_url or self.default_form_url
        if not url:
            raise ValueError("No Google Form URL provided. Pass form_url or set GOOGLE_FORM_URL in .env")

        message = (
            f"Hello {patient_name}! 👋\n\n"
            f"{url}\n\n"
        )

        sms_result = self.sms_service.send_sms(phone_number, message)

        # Record the form link was sent
        db = self._get_db()
        try:
            record = FormResponse(
                patient_phone=phone_number,
                patient_name=patient_name,
                form_link_sent_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return {
                'success': True,
                'record_id': record.id,
                'patient_name': patient_name,
                'phone_number': phone_number,
                'form_url': url,
                'sms_sent': sms_result.get('success', False),
                'message_sid': sms_result.get('message_sid'),
                'sent_at': record.form_link_sent_at.isoformat()
            }
        finally:
            db.close()

    def save_form_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save Google Forms response submitted via Google Apps Script webhook.
        Maps form field answers to database columns.

        Expected payload from Google Apps Script:
        {
            "patient_phone": "+919715441374",
            "patient_name": "John",
            "submitted_at": "2026-05-15T10:00:00",
            "responses": {
                "feeling_today": "Good",
                "shortness_of_breath": "No",
                "dialysis_attended": "Yes",
                "medications_taken": "Yes",
                "followup_scheduled": "Yes",
                "additional_notes": "Feeling better"
            }
        }
        """
        patient_phone = payload.get('patient_phone', '').strip()
        if not patient_phone:
            raise ValueError("patient_phone is required in the payload")

        responses = payload.get('responses', {})
        submitted_at_str = payload.get('submitted_at')

        submitted_at = None
        if submitted_at_str:
            try:
                submitted_at = datetime.fromisoformat(submitted_at_str)
            except ValueError:
                submitted_at = datetime.utcnow()
        else:
            submitted_at = datetime.utcnow()

        db = self._get_db()
        try:
            # Find the most recent unsaved form_response record for this patient
            existing = (
                db.query(FormResponse)
                .filter_by(patient_phone=patient_phone)
                .filter(FormResponse.submitted_at == None)
                .order_by(FormResponse.created_at.desc())
                .first()
            )

            if existing:
                # Update existing pending record
                existing.submitted_at = submitted_at
                existing.patient_name = payload.get('patient_name', existing.patient_name)
                existing.feeling_today = responses.get('feeling_today')
                existing.shortness_of_breath = responses.get('shortness_of_breath')
                existing.dialysis_attended = responses.get('dialysis_attended')
                existing.medications_taken = responses.get('medications_taken')
                existing.followup_scheduled = responses.get('followup_scheduled')
                existing.additional_notes = responses.get('additional_notes')
                existing.raw_responses = responses
                db.commit()
                db.refresh(existing)
                record = existing
            else:
                # Create new record (patient submitted without SMS link being sent via API)
                record = FormResponse(
                    patient_phone=patient_phone,
                    patient_name=payload.get('patient_name'),
                    submitted_at=submitted_at,
                    feeling_today=responses.get('feeling_today'),
                    shortness_of_breath=responses.get('shortness_of_breath'),
                    dialysis_attended=responses.get('dialysis_attended'),
                    medications_taken=responses.get('medications_taken'),
                    followup_scheduled=responses.get('followup_scheduled'),
                    additional_notes=responses.get('additional_notes'),
                    raw_responses=responses
                )
                db.add(record)
                db.commit()
                db.refresh(record)

            return {
                'success': True,
                'record_id': record.id,
                'patient_phone': patient_phone,
                'patient_name': record.patient_name,
                'submitted_at': record.submitted_at.isoformat(),
                'responses_saved': responses
            }
        finally:
            db.close()

    def get_responses_by_phone(self, phone_number: str) -> List[Dict[str, Any]]:
        """Get all form responses for a patient by phone number"""
        db = self._get_db()
        try:
            records = (
                db.query(FormResponse)
                .filter_by(patient_phone=phone_number)
                .order_by(FormResponse.created_at.desc())
                .all()
            )

            results = []
            for r in records:
                results.append({
                    'id': r.id,
                    'patient_name': r.patient_name,
                    'phone_number': r.patient_phone,
                    'form_link_sent_at': r.form_link_sent_at.isoformat() if r.form_link_sent_at else None,
                    'submitted_at': r.submitted_at.isoformat() if r.submitted_at else None,
                    'status': 'submitted' if r.submitted_at else 'pending',
                    'responses': {
                        'feeling_today': r.feeling_today,
                        'shortness_of_breath': r.shortness_of_breath,
                        'dialysis_attended': r.dialysis_attended,
                        'medications_taken': r.medications_taken,
                        'followup_scheduled': r.followup_scheduled,
                        'additional_notes': r.additional_notes
                    } if r.submitted_at else None
                })
            return results
        finally:
            db.close()

    def get_all_responses(self) -> List[Dict[str, Any]]:
        """Get all form responses across all patients"""
        db = self._get_db()
        try:
            records = (
                db.query(FormResponse)
                .order_by(FormResponse.created_at.desc())
                .all()
            )

            results = []
            for r in records:
                results.append({
                    'id': r.id,
                    'patient_name': r.patient_name,
                    'phone_number': r.patient_phone,
                    'form_link_sent_at': r.form_link_sent_at.isoformat() if r.form_link_sent_at else None,
                    'submitted_at': r.submitted_at.isoformat() if r.submitted_at else None,
                    'status': 'submitted' if r.submitted_at else 'pending',
                    'responses': {
                        'feeling_today': r.feeling_today,
                        'shortness_of_breath': r.shortness_of_breath,
                        'dialysis_attended': r.dialysis_attended,
                        'medications_taken': r.medications_taken,
                        'followup_scheduled': r.followup_scheduled,
                        'additional_notes': r.additional_notes
                    } if r.submitted_at else None
                })
            return results
        finally:
            db.close()
