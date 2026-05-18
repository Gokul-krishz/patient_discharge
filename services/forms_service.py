"""
Google Forms Service
Sends Google Form health questionnaire link to patients via SMS
and stores submitted responses in PostgreSQL.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from models.database import FormResponse, Patient, SessionLocal, CareTeamMember
from services.sms_service import SMSService
from services.openrouter_service import OpenRouterService
from services.notification_service import NotificationService


class FormsService:
    """Handles sending Google Form links and storing form responses"""

    def __init__(self, google_form_url: str = None):
        self.sms_service = SMSService()
        self.ai_service = OpenRouterService()
        self.notification_service = NotificationService()
        # Default form URL - can be overridden per request
        self.default_form_url = google_form_url or ""

    def _get_db(self):
        return SessionLocal()
    
    def _generate_and_notify_care_team(
        self,
        db,
        patient_name: str,
        patient_phone: str,
        responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI summary and notify care team members
        
        Args:
            db: Database session
            patient_name: Patient's name
            patient_phone: Patient's phone number
            responses: Form responses
            
        Returns:
            Dictionary with summary text and notification results
        """
        # Generate AI summary using OpenRouter
        summary_result = self.ai_service.generate_form_summary(
            patient_name=patient_name,
            patient_phone=patient_phone,
            form_responses=responses
        )
        
        # Find patient and their care team
        patient = db.query(Patient).filter_by(phone_number=patient_phone).first()
        
        notification_results = {
            'emails_sent': 0,
            'sms_sent': 0,
            'errors': []
        }
        
        if patient:
            # Get care team members
            care_team_members = db.query(CareTeamMember).filter_by(patient_id=patient.id).all()
            
            if care_team_members:
                # Convert to dictionaries
                care_team_list = [{
                    'id': m.id,
                    'name': m.name,
                    'role': m.role,
                    'phone_number': m.phone_number,
                    'email': m.email,
                    'is_primary': m.is_primary
                } for m in care_team_members]
                
                # Send notifications to all care team members
                notification_results = self.notification_service.send_summary_to_care_team(
                    care_team_members=care_team_list,
                    patient_name=patient_name,
                    summary=summary_result,
                    form_responses=responses
                )
            else:
                notification_results['errors'].append('No care team members found for this patient')
        else:
            notification_results['errors'].append('Patient not found in database')
        
        return {
            'summary': summary_result,
            'notifications': notification_results
        }
    

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
                "recently_discharged": "Yes",
                "medication_changes": "Yes",
                "current_symptoms": "No symptoms",
                "care_team_notes": "Recovering well",
                "contact_request": "No"
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
            # Strategy 1: Find the most recent unsaved form_response record for this patient
            existing = (
                db.query(FormResponse)
                .filter_by(patient_phone=patient_phone)
                .filter(FormResponse.submitted_at == None)
                .order_by(FormResponse.created_at.desc())
                .first()
            )
            
            # Strategy 2: If no pending record, check for recent record within last 24 hours
            # This prevents duplicate submissions if patient submits form multiple times
            if not existing:
                from datetime import timedelta
                twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
                existing = (
                    db.query(FormResponse)
                    .filter_by(patient_phone=patient_phone)
                    .filter(FormResponse.created_at >= twenty_four_hours_ago)
                    .order_by(FormResponse.created_at.desc())
                    .first()
                )

            if existing:
                # Update existing pending record
                existing.submitted_at = submitted_at
                existing.patient_name = payload.get('patient_name', existing.patient_name)
                existing.recently_discharged = responses.get('recently_discharged')
                existing.medication_changes = responses.get('medication_changes')
                existing.current_symptoms = responses.get('current_symptoms')
                existing.care_team_notes = responses.get('care_team_notes')
                existing.contact_request = responses.get('contact_request')
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
                    recently_discharged=responses.get('recently_discharged'),
                    medication_changes=responses.get('medication_changes'),
                    current_symptoms=responses.get('current_symptoms'),
                    care_team_notes=responses.get('care_team_notes'),
                    contact_request=responses.get('contact_request'),
                    raw_responses=responses
                )
                db.add(record)
                db.commit()
                db.refresh(record)

            # Generate AI summary and notify care team
            summary_result = None
            try:
                summary_result = self._generate_and_notify_care_team(
                    db, 
                    record.patient_name, 
                    patient_phone,
                    responses
                )
                
                # Save summary to database
                if summary_result and 'summary' in summary_result:
                    # Store the formatted_response in the database
                    record.summary = summary_result['summary'].get('formatted_response', '')
                    db.commit()
                    db.refresh(record)
                    
            except Exception as e:
                print(f"Warning: Failed to generate summary or notify care team: {str(e)}")
                import traceback
                traceback.print_exc()

            return {
                'success': True,
                'record_id': record.id,
                'patient_phone': patient_phone,
                'patient_name': record.patient_name,
                'submitted_at': record.submitted_at.isoformat() if record.submitted_at else None,
                'responses_saved': responses,
                'summary_generated': summary_result is not None,
                'summary': summary_result
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
                        'recently_discharged': r.recently_discharged,
                        'medication_changes': r.medication_changes,
                        'current_symptoms': r.current_symptoms,
                        'care_team_notes': r.care_team_notes,
                        'contact_request': r.contact_request
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
                        'recently_discharged': r.recently_discharged,
                        'medication_changes': r.medication_changes,
                        'current_symptoms': r.current_symptoms,
                        'care_team_notes': r.care_team_notes,
                        'contact_request': r.contact_request
                    } if r.submitted_at else None
                })
            return results
        finally:
            db.close()
