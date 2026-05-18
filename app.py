"""
Flask REST API for File Text Extraction and Discharge Summary
Clean architecture with separated concerns
"""
import os
from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from config import Config
from models import init_db
from services import FileExtractor, AIService, SMSService, PatientChatService, ConversationAgent
from api import forms_ns
from api.care_team_api import care_team_ns

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database tables
try:
    init_db()
except Exception as e:
    print(f"Warning: Database initialization failed: {str(e)}")
    print("Check DATABASE_URL in .env file")

# Initialize Swagger API
api = Api(
    app,
    version='2.0',
    title='Medical Discharge Summary API',
    description='Extract text from files and generate structured discharge summaries using AI',
    doc='/swagger'
)

# Initialize services
file_extractor = FileExtractor()
ai_service = None
sms_service = None
chat_service = None

try:
    ai_service = AIService()
except Exception as e:
    print(f"Warning: AI Service initialization failed: {str(e)}")

try:
    sms_service = SMSService()
    chat_service = PatientChatService()
    conversation_agent = ConversationAgent()
except Exception as e:
    print(f"Warning: SMS/Chat Service initialization failed: {str(e)}")
    print("SMS features will be disabled. Check Twilio configuration in .env")

# API namespace
ns = api.namespace('api', description='File processing and AI operations')

# Register forms namespace (separate API layer)
api.add_namespace(forms_ns, path='/api/forms')

# Request parsers
upload_parser = api.parser()
upload_parser.add_argument(
    'file', 
    location='files', 
    type=FileStorage, 
    required=True,
    help='File to process (PDF, DOCX, TXT, or Image)'
)

# Response models
text_extraction_model = api.model('TextExtractionResponse', {
    'filename': fields.String(description='Name of the uploaded file'),
    'text': fields.String(description='Extracted text content'),
    'file_type': fields.String(description='Type of file processed')
})

discharge_summary_model = api.model('DischargeSummaryResponse', {
    'filename': fields.String(description='Name of the uploaded file'),
    'extracted_text': fields.String(description='Raw extracted text from file'),
    'summary': fields.Raw(description='Structured discharge summary in JSON format'),
    'ai_provider': fields.String(description='AI provider used (openai or gemini)')
})

error_model = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})

sms_response_model = api.model('SMSResponse', {
    'success': fields.Boolean(description='Whether SMS was sent successfully'),
    'message_sid': fields.String(description='Twilio message SID'),
    'status': fields.String(description='Message status'),
    'to': fields.String(description='Recipient phone number'),
    'message': fields.String(description='Message content sent')
})

chat_response_model = api.model('ChatResponse', {
    'patient_id': fields.String(description='Patient identifier'),
    'question': fields.String(description='Patient question'),
    'response': fields.String(description='AI-generated response'),
    'is_emergency': fields.Boolean(description='Whether emergency was detected')
})

# Helper functions
def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_and_process_file(file, process_func):
    """
    Common file handling logic
    
    Args:
        file: Uploaded file object
        process_func: Function to process the extracted text
        
    Returns:
        Tuple of (result, status_code)
    """
    if not file or file.filename == '':
        api.abort(400, 'No file selected')
    
    if not allowed_file(file.filename):
        api.abort(400, f'File type not allowed. Supported formats: {", ".join(Config.ALLOWED_EXTENSIONS)}')
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Save file
        file.save(filepath)
        
        # Extract text
        extracted_text = file_extractor.extract_text(filepath, filename)
        
        # Process with provided function
        result = process_func(filename, extracted_text)
        
        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return result, 200
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(filepath):
            os.remove(filepath)
        return {'error': f'Error processing file: {str(e)}'}, 500

# API Routes
@ns.route('/extract-text')
class TextExtraction(Resource):
    """Simple text extraction endpoint"""
    
    @api.doc('extract_text_from_file')
    @api.expect(upload_parser)
    @api.response(200, 'Success', text_extraction_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Upload a file and extract its text content"""
        if 'file' not in request.files:
            api.abort(400, 'No file part in the request')
        
        file = request.files['file']
        
        def process(filename, text):
            extension = filename.rsplit('.', 1)[1].lower()
            return {
                'filename': filename,
                'text': text,
                'file_type': extension
            }
        
        return save_and_process_file(file, process)

@ns.route('/discharge-summary')
class DischargeSummary(Resource):
    """AI-powered discharge summary extraction endpoint"""
    
    @api.doc('extract_discharge_summary')
    @api.expect(upload_parser)
    @api.response(200, 'Success', discharge_summary_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Upload a discharge report and get AI-powered structured summary"""
        if not ai_service:
            api.abort(500, 'AI service not available. Please check configuration.')
        
        if 'file' not in request.files:
            api.abort(400, 'No file part in the request')
        
        file = request.files['file']
        
        def process(filename, text):
            # Get AI summary
            summary = ai_service.summarize_discharge_report(text)
            
            return {
                'filename': filename,
                'extracted_text': text,
                'summary': summary,
                'ai_provider': Config.AI_PROVIDER
            }
        
        return save_and_process_file(file, process)

@ns.route('/send-sms')
class SendSMS(Resource):
    """Send SMS notification to patient"""
    
    @api.doc('send_sms_notification')
    @api.expect(api.model('SMSRequest', {
        'phone_number': fields.String(required=True, description='Patient phone number (E.164 format: +1234567890)'),
        'patient_name': fields.String(required=True, description='Patient name'),
        'message_type': fields.String(required=True, description='Type: discharge_summary or follow_up'),
        'details': fields.String(description='Additional details (appointment info, etc.)')
    }))
    @api.response(200, 'Success', sms_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Send SMS notification to patient"""
        if not sms_service:
            api.abort(500, 'SMS service not available. Please check Twilio configuration.')
        
        data = request.json
        phone_number = data.get('phone_number')
        patient_name = data.get('patient_name')
        message_type = data.get('message_type')
        details = data.get('details', '')
        
        if not phone_number or not patient_name or not message_type:
            api.abort(400, 'Missing required fields: phone_number, patient_name, message_type')
        
        try:
            if message_type == 'discharge_summary':
                result = sms_service.send_discharge_summary_notification(
                    phone_number, 
                    patient_name
                )
            elif message_type == 'follow_up':
                if not details:
                    api.abort(400, 'Details required for follow_up message type')
                result = sms_service.send_follow_up_reminder(
                    phone_number,
                    patient_name,
                    details
                )
            else:
                api.abort(400, 'Invalid message_type. Use: discharge_summary or follow_up')
            
            return result, 200
            
        except Exception as e:
            return {'error': f'Error sending SMS: {str(e)}'}, 500

@ns.route('/patient-chat')
class PatientChat(Resource):
    """AI-powered patient chat for questions"""
    
    @api.doc('patient_chat')
    @api.expect(api.model('ChatRequest', {
        'patient_id': fields.String(required=True, description='Patient identifier (phone number or ID)'),
        'question': fields.String(required=True, description='Patient question'),
        'discharge_summary': fields.Raw(required=True, description='Patient discharge summary context')
    }))
    @api.response(200, 'Success', chat_response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Get AI response to patient question based on their discharge summary"""
        if not chat_service:
            api.abort(500, 'Chat service not available. Please check configuration.')
        
        data = request.json
        patient_id = data.get('patient_id')
        question = data.get('question')
        discharge_summary = data.get('discharge_summary')
        
        if not patient_id or not question or not discharge_summary:
            api.abort(400, 'Missing required fields: patient_id, question, discharge_summary')
        
        try:
            # Check for emergency
            is_emergency = chat_service.detect_emergency(question)
            
            if is_emergency:
                response = "⚠️ EMERGENCY DETECTED: If you're experiencing a medical emergency, please call 911 immediately or go to the nearest emergency room. Do not wait for a response."
            else:
                # Get AI response
                response = chat_service.get_response(
                    patient_id,
                    discharge_summary,
                    question
                )
            
            return {
                'patient_id': patient_id,
                'question': question,
                'response': response,
                'is_emergency': is_emergency
            }, 200
            
        except Exception as e:
            return {'error': f'Error processing chat: {str(e)}'}, 500

@ns.route('/patient-chat-sms')
class PatientChatSMS(Resource):
    """Combined endpoint: Answer patient question and send via SMS"""
    
    @api.doc('patient_chat_sms')
    @api.expect(api.model('ChatSMSRequest', {
        'phone_number': fields.String(required=True, description='Patient phone number'),
        'question': fields.String(required=True, description='Patient question'),
        'discharge_summary': fields.Raw(required=True, description='Patient discharge summary context')
    }))
    @api.response(200, 'Success')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Get AI response and send it via SMS to patient"""
        if not chat_service or not sms_service:
            api.abort(500, 'Chat or SMS service not available.')
        
        data = request.json
        phone_number = data.get('phone_number')
        question = data.get('question')
        discharge_summary = data.get('discharge_summary')
        
        if not phone_number or not question or not discharge_summary:
            api.abort(400, 'Missing required fields')
        
        try:
            # Get AI response
            is_emergency = chat_service.detect_emergency(question)
            
            if is_emergency:
                response = "⚠️ EMERGENCY: Please call 911 immediately or go to the nearest ER. This is a medical emergency."
            else:
                response = chat_service.get_response(
                    phone_number,
                    discharge_summary,
                    question
                )
            
            # Send via SMS
            sms_result = sms_service.send_sms(phone_number, response)
            
            return {
                'question': question,
                'response': response,
                'is_emergency': is_emergency,
                'sms_sent': sms_result['success'],
                'message_sid': sms_result.get('message_sid')
            }, 200
            
        except Exception as e:
            return {'error': f'Error: {str(e)}'}, 500

@ns.route('/start-conversation')
class StartConversation(Resource):
    """Start a structured patient check-in conversation via SMS"""

    @api.doc('start_conversation')
    @api.expect(api.model('StartConversationRequest', {
        'phone_number': fields.String(required=True, description='Patient phone number (+919...'),
        'patient_name': fields.String(required=True, description='Patient full name'),
        'discharge_summary': fields.Raw(description='Optional discharge summary context')
    }))
    @api.response(200, 'Conversation started')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Start a structured check-in conversation - sends first question via SMS"""
        if not conversation_agent:
            api.abort(500, 'Conversation agent not available. Check Twilio configuration.')

        data = request.json
        phone_number = data.get('phone_number')
        patient_name = data.get('patient_name')
        discharge_summary = data.get('discharge_summary')

        if not phone_number or not patient_name:
            api.abort(400, 'Missing required fields: phone_number, patient_name')

        try:
            result = conversation_agent.start_conversation(
                phone_number, patient_name, discharge_summary
            )
            return result, 200
        except Exception as e:
            return {'error': f'Error starting conversation: {str(e)}'}, 500


@ns.route('/conversation/<int:conversation_id>')
class GetConversation(Resource):
    """Get conversation details and responses"""

    @api.doc('get_conversation')
    @api.response(200, 'Success')
    @api.response(404, 'Not Found', error_model)
    def get(self, conversation_id):
        """Get full Q&A summary for a conversation"""
        if not conversation_agent:
            api.abort(500, 'Conversation agent not available.')
        try:
            result = conversation_agent.get_conversation_summary(conversation_id)
            if 'error' in result:
                return result, 404
            return result, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/conversations')
class ListConversations(Resource):
    """List all patient conversations"""

    @api.doc('list_conversations')
    def get(self):
        """List all conversations with status and progress"""
        if not conversation_agent:
            api.abort(500, 'Conversation agent not available.')
        try:
            phone_number = request.args.get('phone_number')
            result = conversation_agent.get_all_conversations(phone_number)
            return {'conversations': result, 'total': len(result)}, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/patient-replies/<phone_number>')
class GetPatientReplies(Resource):
    """Get all SMS replies from a patient"""
    
    @api.doc('get_patient_replies')
    @api.response(200, 'Success')
    @api.response(404, 'Not Found', error_model)
    def get(self, phone_number):
        """Get all inbound SMS replies from a specific patient phone number"""
        if not conversation_agent:
            api.abort(500, 'Conversation agent not available.')
        
        try:
            from models.database import Patient, Conversation, Message, SessionLocal
            
            db = SessionLocal()
            try:
                # Find patient by phone number
                patient = db.query(Patient).filter_by(phone_number=phone_number).first()
                if not patient:
                    return {'error': f'No patient found with phone number {phone_number}'}, 404
                
                # Get all conversations for this patient
                conversations = db.query(Conversation).filter_by(patient_id=patient.id).all()
                
                if not conversations:
                    return {
                        'patient_name': patient.name,
                        'phone_number': phone_number,
                        'total_replies': 0,
                        'replies': []
                    }, 200
                
                # Get all inbound messages across all conversations
                all_replies = []
                for conv in conversations:
                    messages = db.query(Message).filter_by(
                        conversation_id=conv.id,
                        direction='inbound'
                    ).order_by(Message.timestamp).all()
                    
                    for msg in messages:
                        all_replies.append({
                            'conversation_id': conv.id,
                            'question_key': msg.question_key,
                            'reply_text': msg.content,
                            'timestamp': msg.timestamp.isoformat(),
                            'conversation_status': conv.status
                        })
                
                return {
                    'patient_name': patient.name,
                    'phone_number': phone_number,
                    'total_replies': len(all_replies),
                    'replies': all_replies
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error fetching replies: {str(e)}'}, 500


@ns.route('/latest-reply/<phone_number>')
class GetLatestReply(Resource):
    """Get the most recent SMS reply from a patient"""
    
    @api.doc('get_latest_reply')
    @api.response(200, 'Success')
    @api.response(404, 'Not Found', error_model)
    def get(self, phone_number):
        """Get the most recent inbound SMS reply from a patient"""
        if not conversation_agent:
            api.abort(500, 'Conversation agent not available.')
        
        try:
            from models.database import Patient, Conversation, Message, SessionLocal
            
            db = SessionLocal()
            try:
                # Find patient
                patient = db.query(Patient).filter_by(phone_number=phone_number).first()
                if not patient:
                    return {'error': f'No patient found with phone number {phone_number}'}, 404
                
                # Get most recent inbound message
                latest_message = (
                    db.query(Message)
                    .join(Conversation)
                    .filter(Conversation.patient_id == patient.id)
                    .filter(Message.direction == 'inbound')
                    .order_by(Message.timestamp.desc())
                    .first()
                )
                
                if not latest_message:
                    return {
                        'patient_name': patient.name,
                        'phone_number': phone_number,
                        'message': 'No replies received yet'
                    }, 200
                
                conversation = db.query(Conversation).filter_by(id=latest_message.conversation_id).first()
                
                return {
                    'patient_name': patient.name,
                    'phone_number': phone_number,
                    'latest_reply': {
                        'conversation_id': conversation.id,
                        'question_key': latest_message.question_key,
                        'reply_text': latest_message.content,
                        'timestamp': latest_message.timestamp.isoformat(),
                        'conversation_status': conversation.status
                    }
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error fetching latest reply: {str(e)}'}, 500


@app.route('/webhook/sms', methods=['GET', 'POST'])
def sms_webhook():
    """Twilio webhook - receives patient SMS replies and sends next question"""
    
    # Handle GET requests (for testing/verification)
    if request.method == 'GET':
        return {
            'status': 'webhook_active',
            'message': 'Twilio SMS webhook is ready to receive POST requests',
            'endpoint': '/webhook/sms',
            'method': 'POST',
            'tunnel_url': 'https://ninety-trains-grin.loca.lt/webhook/sms'
        }, 200
    
    # Handle POST requests from Twilio
    from twilio.twiml.messaging_response import MessagingResponse

    from_number = request.form.get('From')
    body = request.form.get('Body', '').strip()

    resp = MessagingResponse()

    if not from_number or not body:
        resp.message("Sorry, we could not process your message.")
        return str(resp)

    try:
        result = conversation_agent.handle_patient_reply(from_number, body)
        # Twilio webhook handles sending via the agent - no TwiML message needed
    except Exception as e:
        resp.message("Sorry, there was an error processing your response. Please try again.")

    return str(resp)


@ns.route('/health')
class Health(Resource):
    """Health check endpoint"""
    
    @api.doc('health_check')
    def get(self):
        """Check API health status"""
        return {
            'status': 'healthy',
            'message': 'API is running',
            'ai_provider': Config.AI_PROVIDER,
            'ai_service_available': ai_service is not None,
            'sms_service_available': sms_service is not None,
            'chat_service_available': chat_service is not None,
            'conversation_agent_available': conversation_agent is not None
        }, 200

# Entry point
if __name__ == '__main__':
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration Error: {str(e)}")
        print("Please check your .env file")
    
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )
