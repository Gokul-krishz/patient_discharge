"""
Google Forms API Layer
Separate namespace for all Google Forms related endpoints.
Registered into the main Flask app via app.py.
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from services.forms_service import FormsService
from config import Config

forms_ns = Namespace('forms', description='Google Forms health questionnaire operations')

# Initialize service
try:
    forms_service = FormsService(google_form_url=Config.GOOGLE_FORM_URL)
except Exception as e:
    forms_service = None
    print(f"Warning: FormsService initialization failed: {str(e)}")

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

send_form_model = forms_ns.model('SendFormRequest', {
    'patient_id': fields.Integer(description='ADT Patient ID (if sending from ADT system)'),
    'phone_number': fields.String(description='Patient phone number (E.164 format: +919...) - required if patient_id not provided'),
    'patient_name': fields.String(description='Patient full name - required if patient_id not provided'),
    'form_url': fields.String(description='Override Google Form URL (optional if set in .env)')
})

form_webhook_model = forms_ns.model('FormWebhookPayload', {
    'patient_phone': fields.String(required=True, description='Patient phone number'),
    'patient_name': fields.String(description='Patient name'),
    'submitted_at': fields.String(description='ISO timestamp of submission'),
    'responses': fields.Raw(required=True, description='Form field answers as key-value pairs')
})

error_model = forms_ns.model('Error', {
    'error': fields.String(description='Error message')
})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@forms_ns.route('/send-form-link')
class SendFormLink(Resource):
    """Send Google Forms health questionnaire link to patient via SMS"""

    @forms_ns.doc('send_form_link')
    @forms_ns.expect(send_form_model)
    @forms_ns.response(200, 'Form link sent successfully')
    @forms_ns.response(400, 'Bad Request', error_model)
    @forms_ns.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Send Google Form link to patient via SMS and record in database"""
        if not forms_service:
            forms_ns.abort(500, 'Forms service not available. Check configuration.')

        data = request.json or {}
        patient_id = data.get('patient_id')
        phone_number = data.get('phone_number', '').strip() if data.get('phone_number') else None
        patient_name = data.get('patient_name', '').strip() if data.get('patient_name') else None
        form_url = data.get('form_url', '').strip() or None

        # Validate: either patient_id OR (phone_number AND patient_name) must be provided
        if not patient_id and (not phone_number or not patient_name):
            forms_ns.abort(400, 'Either patient_id OR (phone_number AND patient_name) must be provided')

        try:
            result = forms_service.send_form_link(
                phone_number=phone_number,
                patient_name=patient_name,
                form_url=form_url,
                adt_patient_id=patient_id
            )
            return result, 200
        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': f'Error sending form link: {str(e)}'}, 500


@forms_ns.route('/webhook')
class GoogleFormsWebhook(Resource):
    """
    Webhook endpoint called by Google Apps Script when patient submits the form.
    Stores the response in PostgreSQL.
    """

    @forms_ns.doc('receive_form_response')
    @forms_ns.expect(form_webhook_model)
    @forms_ns.response(200, 'Response saved successfully')
    @forms_ns.response(400, 'Bad Request', error_model)
    @forms_ns.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Receive Google Forms submission from Apps Script and store in database"""
        if not forms_service:
            forms_ns.abort(500, 'Forms service not available.')

        payload = request.json or {}
        
        # Debug logging
        print("=" * 70)
        print("WEBHOOK RECEIVED")
        print("=" * 70)
        print(f"Payload: {payload}")
        print("=" * 70)

        if not payload.get('patient_phone'):
            return {'error': 'Missing required field: patient_phone'}, 400

        if not payload.get('responses'):
            return {'error': 'Missing required field: responses'}, 400

        try:
            result = forms_service.save_form_response(payload)
            return result, 200
        except ValueError as e:
            print(f"ValueError: {e}")
            return {'error': str(e)}, 400
        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Error saving form response: {str(e)}'}, 500

    def get(self):
        """Health check for the webhook endpoint"""
        return {
            'status': 'active',
            'message': 'Google Forms webhook is ready to receive POST submissions',
            'endpoint': '/api/forms/webhook',
            'method': 'POST'
        }, 200


@forms_ns.route('/responses')
class AllFormResponses(Resource):
    """Get all form responses across all patients"""

    @forms_ns.doc('get_all_form_responses')
    @forms_ns.response(200, 'Success')
    def get(self):
        """Get all Google Forms health questionnaire responses"""
        if not forms_service:
            forms_ns.abort(500, 'Forms service not available.')
        try:
            results = forms_service.get_all_responses()
            return {
                'total': len(results),
                'responses': results
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500


@forms_ns.route('/responses/<phone_number>')
class PatientFormResponses(Resource):
    """Get form responses for a specific patient"""

    @forms_ns.doc('get_patient_form_responses')
    @forms_ns.response(200, 'Success')
    @forms_ns.response(404, 'Not Found', error_model)
    def get(self, phone_number):
        """Get all Google Forms responses for a patient by phone number"""
        if not forms_service:
            forms_ns.abort(500, 'Forms service not available.')
        try:
            results = forms_service.get_responses_by_phone(phone_number)
            if not results:
                return {'error': f'No form records found for {phone_number}'}, 404
            return {
                'phone_number': phone_number,
                'total': len(results),
                'responses': results
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500
