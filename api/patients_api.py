"""
Patients API Layer
Endpoints for managing and viewing patient data with follow-up information
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from models.database import Patient, FormResponse, SessionLocal
from sqlalchemy import desc

patients_ns = Namespace('patients', description='Patient management operations')

# Response models
form_responses_model = patients_ns.model('FormResponses', {
    'recently_discharged': fields.String(description='Recently discharged response'),
    'medication_changes': fields.String(description='Medication changes response'),
    'current_symptoms': fields.String(description='Current symptoms response'),
    'care_team_notes': fields.String(description='Care team notes response'),
    'contact_request': fields.String(description='Contact request response'),
})

form_response_summary_model = patients_ns.model('FormResponseSummary', {
    'id': fields.Integer(description='Form response ID'),
    'submitted_at': fields.String(description='Submission timestamp'),
    'status': fields.String(description='Form status (Pending/Completed)'),
    'summary': fields.String(description='AI-generated summary (only for Completed)'),
    'responses': fields.Nested(form_responses_model, allow_null=True, description='Patient responses (only for Completed)'),
})

patient_model = patients_ns.model('Patient', {
    'patient_id': fields.String(description='Patient ID'),
    'name': fields.String(description='Patient name'),
    'phone_number': fields.String(description='Patient phone number'),
    'hospital': fields.String(description='Hospital name'),
    'admission_date': fields.String(description='Admission date'),
    'discharge_date': fields.String(description='Discharge date'),
    'status': fields.String(description='Patient status (Admitted/Discharged)'),
    'follow_up': fields.String(description='Follow-up status (Pending/Link Sent/Completed)'),
    'latest_form_response': fields.Nested(form_response_summary_model, allow_null=True, description='Latest form response'),
})

patients_list_model = patients_ns.model('PatientsList', {
    'total': fields.Integer(description='Total number of patients'),
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total_pages': fields.Integer(description='Total number of pages'),
    'patients': fields.List(fields.Nested(patient_model))
})


@patients_ns.route('/list')
class PatientsList(Resource):
    @patients_ns.doc('get_patients_list')
    @patients_ns.param('page', 'Page number (default: 1)', type=int)
    @patients_ns.param('per_page', 'Items per page (default: 10, max: 100)', type=int)
    @patients_ns.param('status', 'Filter by status (Admitted/Discharged)', type=str)
    @patients_ns.param('hospital', 'Filter by hospital name', type=str)
    @patients_ns.param('follow_up', 'Filter by follow-up status (Pending/Link Sent/Completed)', type=str)
    @patients_ns.param('search', 'Search by patient name or patient ID', type=str)
    @patients_ns.response(200, 'Success', patients_list_model)
    @patients_ns.response(400, 'Bad Request')
    @patients_ns.response(500, 'Internal Server Error')
    def get(self):
        """Get paginated list of patients with follow-up status and form responses"""
        try:
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status_filter = request.args.get('status', None, type=str)
            hospital_filter = request.args.get('hospital', None, type=str)
            follow_up_filter = request.args.get('follow_up', None, type=str)
            search_query = request.args.get('search', None, type=str)
            
            # Validate parameters
            if page < 1:
                return {'error': 'Page number must be >= 1'}, 400
            if per_page < 1 or per_page > 100:
                return {'error': 'per_page must be between 1 and 100'}, 400
            
            db = SessionLocal()
            try:
                # Build query
                query = db.query(Patient).order_by(desc(Patient.created_at))
                
                # Apply search filter (patient name or ID)
                if search_query:
                    search_query = search_query.strip()
                    # Check if search is for patient ID (starts with P followed by digits)
                    if search_query.upper().startswith('P') and search_query[1:].isdigit():
                        numeric_id = int(search_query[1:])
                        query = query.filter(Patient.id == numeric_id)
                    else:
                        # Search by name (case-insensitive partial match)
                        query = query.filter(Patient.name.ilike(f'%{search_query}%'))
                
                # Apply status filter
                if status_filter:
                    query = query.filter(Patient.status == status_filter)
                
                # Apply hospital filter
                if hospital_filter:
                    query = query.filter(Patient.hospital == hospital_filter)
                
                # Get total count
                total = query.count()
                
                # Calculate pagination
                total_pages = (total + per_page - 1) // per_page
                offset = (page - 1) * per_page
                
                # Get paginated results
                patients = query.offset(offset).limit(per_page).all()
                
                # Build response with follow-up status and form responses
                patients_data = []
                for patient in patients:
                    # Apply follow-up filter
                    if follow_up_filter and patient.follow_up != follow_up_filter:
                        continue
                    
                    # Get latest form response
                    latest_form = (
                        db.query(FormResponse)
                        .filter(FormResponse.patient_phone == patient.phone_number)
                        .order_by(desc(FormResponse.created_at))
                        .first()
                    )
                    
                    latest_form_data = None
                    if latest_form:
                        form_status = 'Completed' if latest_form.submitted_at else 'Pending'
                        
                        latest_form_data = {
                            'id': latest_form.id,
                            'submitted_at': latest_form.submitted_at.isoformat() if latest_form.submitted_at else None,
                            'status': form_status
                        }
                        
                        # Include full response data and summary only if status is Completed
                        if form_status == 'Completed':
                            latest_form_data['summary'] = latest_form.summary
                            latest_form_data['responses'] = {
                                'recently_discharged': latest_form.recently_discharged,
                                'medication_changes': latest_form.medication_changes,
                                'current_symptoms': latest_form.current_symptoms,
                                'care_team_notes': latest_form.care_team_notes,
                                'contact_request': latest_form.contact_request
                            }
                    
                    patient_data = {
                        'patient_id': f'P{str(patient.id).zfill(6)}',
                        'name': patient.name,
                        'phone_number': patient.phone_number,
                        'hospital': patient.hospital or '-',
                        'admission_date': patient.admission_date.strftime('%d %b %Y') if patient.admission_date else '-',
                        'discharge_date': patient.discharge_date.strftime('%d %b %Y') if patient.discharge_date else '-',
                        'status': patient.status or 'Unknown',
                        'follow_up': patient.follow_up or 'Pending',
                        'latest_form_response': latest_form_data
                    }
                    patients_data.append(patient_data)
                
                return {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'patients': patients_data
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error fetching patients: {str(e)}'}, 500


send_link_model = patients_ns.model('SendLink', {
    'patient_id': fields.String(required=True, description='Patient ID (e.g., P000001)'),
})


@patients_ns.route('/pending-followups')
class PendingFollowUps(Resource):
    @patients_ns.doc('get_pending_followups')
    @patients_ns.response(200, 'Success')
    @patients_ns.response(500, 'Internal Server Error')
    def get(self):
        """Get list of discharged patients with pending follow-ups"""
        try:
            db = SessionLocal()
            try:
                # Query for discharged patients with pending follow-up
                patients = (
                    db.query(Patient)
                    .filter(Patient.status == 'Discharged')
                    .filter(Patient.follow_up == 'Pending')
                    .order_by(desc(Patient.discharge_date))
                    .all()
                )
                
                patients_data = []
                for patient in patients:
                    # Get initials for avatar
                    name_parts = patient.name.split()
                    initials = ''.join([part[0].upper() for part in name_parts[:2]]) if name_parts else 'NA'
                    
                    patient_data = {
                        'patient_id': f'P{str(patient.id).zfill(6)}',
                        'name': patient.name,
                        'initials': initials,
                        'phone_number': patient.phone_number,
                        'hospital': patient.hospital or 'Unknown',
                        'discharge_date': patient.discharge_date.strftime('%d %b %Y') if patient.discharge_date else 'Unknown',
                        'discharge_date_iso': patient.discharge_date.isoformat() if patient.discharge_date else None,
                        'status': patient.status,
                        'follow_up': patient.follow_up
                    }
                    patients_data.append(patient_data)
                
                return {
                    'count': len(patients_data),
                    'patients': patients_data
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error fetching pending follow-ups: {str(e)}'}, 500


@patients_ns.route('/send-form-link')
class SendFormLink(Resource):
    @patients_ns.doc('send_form_link')
    @patients_ns.expect(send_link_model)
    @patients_ns.response(200, 'Form link sent successfully')
    @patients_ns.response(404, 'Patient not found')
    @patients_ns.response(500, 'Internal Server Error')
    def post(self):
        """Send form link to a patient"""
        try:
            from services.forms_service import FormsService
            from config import Config
            
            data = request.json
            patient_id_str = data.get('patient_id', '')
            
            # Extract numeric ID
            try:
                numeric_id = int(patient_id_str.replace('P', ''))
            except ValueError:
                return {'error': 'Invalid patient ID format'}, 400
            
            db = SessionLocal()
            try:
                patient = db.query(Patient).filter(Patient.id == numeric_id).first()
                
                if not patient:
                    return {'error': 'Patient not found'}, 404
                
                # Initialize forms service and send link
                forms_service = FormsService(google_form_url=Config.GOOGLE_FORM_URL)
                result = forms_service.send_form_link(
                    phone_number=patient.phone_number,
                    patient_name=patient.name
                )
                
                return {
                    'success': True,
                    'message': f'Form link sent to {patient.name}',
                    'patient_id': patient_id_str,
                    'patient_name': patient.name,
                    'phone_number': patient.phone_number
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error sending form link: {str(e)}'}, 500


@patients_ns.route('/hospitals')
class HospitalsList(Resource):
    @patients_ns.doc('get_hospitals_list')
    @patients_ns.response(200, 'Success')
    @patients_ns.response(500, 'Internal Server Error')
    def get(self):
        """Get list of unique hospitals for filtering"""
        try:
            db = SessionLocal()
            try:
                # Get distinct hospitals
                hospitals = (
                    db.query(Patient.hospital)
                    .filter(Patient.hospital.isnot(None))
                    .distinct()
                    .order_by(Patient.hospital)
                    .all()
                )
                
                hospital_list = [h[0] for h in hospitals if h[0]]
                
                return {
                    'hospitals': hospital_list,
                    'count': len(hospital_list)
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error fetching hospitals: {str(e)}'}, 500
