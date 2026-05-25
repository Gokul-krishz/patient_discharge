"""
Google Forms Service
Sends Google Form health questionnaire link to patients via SMS
and stores submitted responses in PostgreSQL.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from models.database import FormResponse, Patient, SessionLocal, CareTeamMember, ADTPatient
from services.sms_service import SMSService
from services.gemini_forms_service import GeminiFormsService
from services.notification_service import NotificationService


class FormsService:
    """Handles sending Google Form links and storing form responses"""

    def __init__(self, google_form_url: str = None):
        self.sms_service = SMSService()
        self.ai_service = GeminiFormsService()
        self.notification_service = NotificationService()
        # Default form URL - can be overridden per request
        self.default_form_url = google_form_url or ""

    def _get_db(self):
        return SessionLocal()

    def _resolve_phone(self, phone: str) -> str:
        """
        Normalize a phone number to E.164 format.
        Handles: '9715441374' -> '+919715441374' is NOT done here (country code unknown).
        This simply ensures a leading '+' is present when the raw value already
        includes the country code digits (e.g. '919715441374' -> '+919715441374').
        Use _find_existing_form_response for fuzzy lookup.
        """
        phone = phone.strip()
        if phone and not phone.startswith('+'):
            return '+' + phone
        return phone

    def _find_existing_form_response(self, db, patient_phone: str):
        """
        Find the most recent pending FormResponse for a patient tolerating phone
        format differences (E.164 vs local number without country code).

        Lookup order:
        1. Exact match on patient_phone as-is
        2. Exact match with leading '+' added
        3. Suffix match on last 10 digits (handles local number vs stored E.164)
        """
        from datetime import timedelta

        def _pending_query(db, phone_val):
            return (
                db.query(FormResponse)
                .filter(FormResponse.patient_phone == phone_val)
                .filter(FormResponse.submitted_at == None)
                .order_by(FormResponse.created_at.desc())
                .first()
            )

        def _recent_query(db, phone_val):
            cutoff = datetime.utcnow() - timedelta(hours=24)
            return (
                db.query(FormResponse)
                .filter(FormResponse.patient_phone == phone_val)
                .filter(FormResponse.created_at >= cutoff)
                .order_by(FormResponse.created_at.desc())
                .first()
            )

        # 1. Exact match
        record = _pending_query(db, patient_phone) or _recent_query(db, patient_phone)
        if record:
            return record

        # 2. Try with '+' prefix
        if not patient_phone.startswith('+'):
            with_plus = '+' + patient_phone
            record = _pending_query(db, with_plus) or _recent_query(db, with_plus)
            if record:
                return record

        # 3. Suffix match on last 10 digits (local number submitted, E.164 stored)
        digits_only = ''.join(filter(str.isdigit, patient_phone))
        if len(digits_only) >= 10:
            last10 = digits_only[-10:]
            print(f"[FORMS] Phone lookup: trying suffix match on last 10 digits: {last10}")
            record = (
                db.query(FormResponse)
                .filter(FormResponse.patient_phone.like(f'%{last10}'))
                .filter(FormResponse.submitted_at == None)
                .order_by(FormResponse.created_at.desc())
                .first()
            )
            if not record:
                cutoff = datetime.utcnow() - timedelta(hours=24)
                record = (
                    db.query(FormResponse)
                    .filter(FormResponse.patient_phone.like(f'%{last10}'))
                    .filter(FormResponse.created_at >= cutoff)
                    .order_by(FormResponse.created_at.desc())
                    .first()
                )
            if record:
                print(f"[FORMS] Matched via suffix: payload={patient_phone} -> stored={record.patient_phone}")
                return record

        return None

    def _find_patient_by_phone(self, db, patient_phone: str):
        """
        Find a Patient record tolerating phone format differences.
        Tries exact, +prefix, and last-10-digit suffix match.
        """
        patient = db.query(Patient).filter_by(phone_number=patient_phone).first()
        if patient:
            return patient

        if not patient_phone.startswith('+'):
            patient = db.query(Patient).filter_by(phone_number='+' + patient_phone).first()
            if patient:
                return patient

        digits_only = ''.join(filter(str.isdigit, patient_phone))
        if len(digits_only) >= 10:
            last10 = digits_only[-10:]
            patient = (
                db.query(Patient)
                .filter(Patient.phone_number.like(f'%{last10}'))
                .first()
            )
        return patient

    def _notify_care_team(
        self,
        db,
        patient_name: str,
        patient_phone: str,
        ai_summary: Dict[str, Any],
        responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Notify care team members with the AI-generated summary.

        Args:
            db: Database session
            patient_name: Patient's name
            patient_phone: Patient's phone number (canonical E.164)
            ai_summary: Result from GeminiFormsService.generate_form_summary
            responses: Raw form responses

        Returns:
            Dictionary with notification results (emails_sent, sms_sent, errors)
        """
        notification_results = {
            'emails_sent': 0,
            'sms_sent': 0,
            'errors': []
        }

        if not ai_summary:
            msg = 'Skipping care team notification: no AI summary available'
            notification_results['errors'].append(msg)
            print(f"[NOTIFY] WARNING: {msg}")
            return notification_results

        # Find patient using phone-tolerant lookup
        print(f"[NOTIFY] Looking up patient by phone: {patient_phone}")
        patient = self._find_patient_by_phone(db, patient_phone)

        if patient:
            print(f"[NOTIFY] Patient found: {patient.name} (id={patient.id}, phone={patient.phone_number})")
            care_team_members = db.query(CareTeamMember).filter_by(patient_id=patient.id).all()
            print(f"[NOTIFY] Care team members found: {len(care_team_members)}")

            if care_team_members:
                care_team_list = [{
                    'id': m.id,
                    'name': m.name,
                    'role': m.role,
                    'phone_number': m.phone_number,
                    'email': m.email,
                    'is_primary': m.is_primary
                } for m in care_team_members]

                notification_results = self.notification_service.send_summary_to_care_team(
                    care_team_members=care_team_list,
                    patient_name=patient_name,
                    summary=ai_summary,
                    form_responses=responses
                )
                print(f"[NOTIFY] Results -> emails_sent={notification_results['emails_sent']}, "
                      f"sms_sent={notification_results['sms_sent']}, "
                      f"errors={notification_results['errors']}")
            else:
                msg = f'No care team members found for patient id={patient.id} ({patient_phone})'
                notification_results['errors'].append(msg)
                print(f"[NOTIFY] WARNING: {msg}")
        else:
            msg = f'Patient not found in DB for phone: {patient_phone}'
            notification_results['errors'].append(msg)
            print(f"[NOTIFY] WARNING: {msg}")

        return notification_results
    

    def send_form_link(
        self,
        phone_number: str = None,
        patient_name: str = None,
        form_url: str = None,
        adt_patient_id: int = None
    ) -> Dict[str, Any]:
        """
        Send Google Form health questionnaire link to patient via SMS.
        Records the send event in the database.
        
        If adt_patient_id is provided:
        1. Fetch ADT patient details
        2. Update ADT patient status from 'Admitted' to 'Discharged'
        3. Create/update Patient record with follow_up='Link Sent'
        4. Send SMS with form link
        
        Args:
            phone_number: Patient phone (required if adt_patient_id not provided)
            patient_name: Patient name (required if adt_patient_id not provided)
            form_url: Google Form URL (optional)
            adt_patient_id: ADT Patient ID (optional)
        """
        db = self._get_db()
        try:
            # Handle ADT patient workflow
            if adt_patient_id:
                adt_patient = db.query(ADTPatient).filter_by(id=adt_patient_id).first()
                if not adt_patient:
                    raise ValueError(f"ADT Patient with ID {adt_patient_id} not found")
                
                # Use ADT patient details
                phone_number = adt_patient.phone_number
                patient_name = adt_patient.name
                
                # Update ADT patient status to 'Discharged'
                adt_patient.status = 'Discharged'
                adt_patient.discharge_date = datetime.utcnow()
                
                # Always create a new Patient record (allow multiple records with same phone number)
                patient = Patient(
                    name=patient_name,
                    phone_number=phone_number,
                    hospital=adt_patient.hospital,
                    admission_date=adt_patient.admission_date,
                    discharge_date=adt_patient.discharge_date,
                    status='Discharged',
                    follow_up='Link Sent',
                    discharge_summary=adt_patient.discharge_summary,
                    care_team=adt_patient.care_team
                )
                db.add(patient)
                
                db.commit()
            
            # Validate required fields
            if not phone_number or not patient_name:
                raise ValueError("phone_number and patient_name are required")
            
            url = form_url or self.default_form_url
            if not url:
                raise ValueError("No Google Form URL provided. Pass form_url or set GOOGLE_FORM_URL in .env")

            message = (
                f"Hello {patient_name}! 👋\n\n"
                f"{url}\n\n"
            )

            sms_result = self.sms_service.send_sms(phone_number, message)

            # Note: We no longer update existing patient records since multiple patients 
            # can have the same phone number. Each form link send creates a new patient record.
            
            # Record the form link was sent
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
                'sent_at': record.form_link_sent_at.isoformat(),
                'adt_patient_id': adt_patient_id,
                'adt_status_updated': adt_patient_id is not None
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
            # Find existing pending/recent record with phone-format-tolerant lookup
            existing = self._find_existing_form_response(db, patient_phone)

            if existing:
                print(f"[FORMS] Updating existing FormResponse id={existing.id} (stored phone={existing.patient_phone})")
                # Always use the stored phone number so all downstream lookups stay consistent
                canonical_phone = existing.patient_phone

                # Update existing record
                existing.submitted_at = submitted_at
                existing.patient_name = payload.get('patient_name', existing.patient_name)
                existing.recently_discharged = responses.get('recently_discharged')
                existing.medication_changes = responses.get('medication_changes')
                existing.current_symptoms = responses.get('current_symptoms')
                existing.care_team_notes = responses.get('care_team_notes')
                existing.contact_request = responses.get('contact_request')
                existing.raw_responses = responses

                # Update patient follow_up status to Completed
                patient = self._find_patient_by_phone(db, canonical_phone)
                if patient:
                    patient.follow_up = 'Completed'

                db.commit()
                db.refresh(existing)
                record = existing
                patient_phone = canonical_phone  # use stored format for all downstream calls
            else:
                print(f"[FORMS] No existing record found for {patient_phone}. Creating new FormResponse.")
                # Normalize phone to E.164 for new records (prepend '+' if missing)
                if not patient_phone.startswith('+'):
                    patient_phone = '+' + patient_phone

                # Create new record
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

                # Update patient follow_up status to Completed
                patient = self._find_patient_by_phone(db, patient_phone)
                if patient:
                    patient.follow_up = 'Completed'

                db.commit()
                db.refresh(record)

            # Step 1: Generate AI summary and save to DB immediately
            ai_summary = None
            try:
                print(f"[FORMS] Generating AI summary for {record.patient_name} ({patient_phone})")
                ai_summary = self.ai_service.generate_form_summary(
                    patient_name=record.patient_name,
                    patient_phone=patient_phone,
                    form_responses=responses
                )
                record.summary = ai_summary.get('formatted_response', '')
                db.commit()
                db.refresh(record)
                print(f"[FORMS] Summary saved to DB for record id={record.id}")
            except Exception as e:
                print(f"[FORMS] ERROR: Failed to generate/save summary: {str(e)}")
                import traceback
                traceback.print_exc()

            # Step 2: Notify care team (runs independently — summary already saved above)
            notification_info = None
            try:
                notification_info = self._notify_care_team(
                    db,
                    record.patient_name,
                    patient_phone,
                    ai_summary,
                    responses
                )
            except Exception as e:
                print(f"[NOTIFY] ERROR: Failed to notify care team: {str(e)}")
                import traceback
                traceback.print_exc()

            return {
                'success': True,
                'record_id': record.id,
                'patient_phone': patient_phone,
                'patient_name': record.patient_name,
                'submitted_at': record.submitted_at.isoformat() if record.submitted_at else None,
                'responses_saved': responses,
                'summary_generated': ai_summary is not None,
                'notifications': notification_info,
                'summary': ai_summary
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
