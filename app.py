"""
Flask REST API for File Text Extraction and Discharge Summary
Clean architecture with separated concerns
"""
import os
import sys
import logging
from flask import Flask, request
from flask_restx import Api, Resource, fields
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from config import Config
from models import init_db
from services import FileExtractor, AIService, SMSService, PatientChatService, ConversationAgent
from api import forms_ns, patients_ns, adt_patients_ns, discharge_ns
from api.care_team_api import care_team_ns

# MCP Architecture imports
try:
    from mcp.server import MCPServer
    from mcp.registry import ToolRegistry
    from agent.outreach_agent import OutreachAgent
except ImportError:
    MCPServer = None
    ToolRegistry = None
    OutreachAgent = None
    print("Warning: MCP modules not found. MCP features will be disabled.")

# Configure logging to show all output immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Force unbuffered output for print statements
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Enable CORS for all routes with all methods
CORS(app, 
     resources={r"/*": {
         "origins": "*",
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"]
     }},
     supports_credentials=False)

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
forms_service = None

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

try:
    from services.forms_service import FormsService
    forms_service = FormsService(google_form_url=Config.GOOGLE_FORM_URL)
except Exception as e:
    print(f"Warning: Forms Service initialization failed: {str(e)}")
    print("Forms features will be disabled.")

# Initialize MCP Architecture
mcp_server = None
outreach_agent = None

if MCPServer and ToolRegistry and OutreachAgent:
    print("\n" + "="*70)
    print("Initializing MCP Architecture")
    print("="*70)
    try:
        # Create MCP Server
        mcp_server = MCPServer()
        
        # Register tools with existing service instances
        ToolRegistry.create_and_register_tools(
            mcp_server,
            sms_service=sms_service,
            ai_service=ai_service,
            conversation_agent=conversation_agent,
            forms_service=forms_service
        )
        
        # Create Outreach Agent
        outreach_agent = OutreachAgent(mcp_server)
        
        print("="*70)
        print("MCP Architecture initialized successfully")
        print("="*70 + "\n")
    except Exception as e:
        print(f"Warning: MCP Architecture initialization failed: {str(e)}")
        print("MCP features will be disabled. Falling back to direct service calls.")
else:
    print("MCP modules not available. Skipping MCP initialization.")

# API namespace
ns = api.namespace('api', description='File processing and AI operations')

# Register forms namespace (separate API layer)
api.add_namespace(forms_ns, path='/api/forms')

# Register patients namespace
api.add_namespace(patients_ns, path='/api/patients')

# Register ADT patients namespace
api.add_namespace(adt_patients_ns, path='/api/adt_patients')

# Register discharge trigger namespace
# api.add_namespace(discharge_ns, path='/api/discharge')

# Register care team namespace
api.add_namespace(care_team_ns, path='/api/care-team')

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
            from services import ActionLogger, ACTION_TYPES
            from models.database import Patient, SessionLocal
            
            # Get patient_id from phone number
            db = SessionLocal()
            patient = db.query(Patient).filter_by(phone_number=phone_number).first()
            patient_id = patient.id if patient else None
            db.close()
            
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
            
            # Log the action
            if patient_id and result.get('status') == 'sent':
                ActionLogger.log_action(
                    patient_id=patient_id,
                    action=ACTION_TYPES['SMS_SENT'],
                    metadata={
                        'phone': phone_number,
                        'message_type': message_type,
                        'details': details,
                        'twilio_sid': result.get('message_sid')
                    }
                )
            
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
            from services import ActionLogger, ACTION_TYPES
            from models.database import Patient, SessionLocal
            
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
            
            # Log the action
            if sms_result.get('success'):
                db = SessionLocal()
                patient = db.query(Patient).filter_by(phone_number=phone_number).first()
                if patient:
                    ActionLogger.log_action(
                        patient_id=patient.id,
                        action=ACTION_TYPES['SMS_SENT'],
                        metadata={
                            'phone': phone_number,
                            'message_type': 'ai_chat_response',
                            'question': question[:100],  # First 100 chars
                            'is_emergency': is_emergency,
                            'twilio_sid': sms_result.get('message_sid')
                        }
                    )
                db.close()
            
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
            from services import ActionLogger, ACTION_TYPES
            from models.database import Patient, SessionLocal
            
            result = conversation_agent.start_conversation(
                phone_number, patient_name, discharge_summary
            )
            
            # Log the action
            if result.get('status') == 'started':
                db = SessionLocal()
                patient = db.query(Patient).filter_by(phone_number=phone_number).first()
                if patient:
                    ActionLogger.log_action(
                        patient_id=patient.id,
                        action=ACTION_TYPES['CONVERSATION_STARTED'],
                        metadata={
                            'phone': phone_number,
                            'conversation_id': result.get('conversation_id'),
                            'questions_total': result.get('total_questions', 0)
                        }
                    )
                db.close()
            
            return result, 200
        except Exception as e:
            return {'error': f'Error starting conversation: {str(e)}'}, 500


@ns.route('/mcp/outreach')
class MCPOutreach(Resource):
    """MCP-powered patient outreach endpoint (NEW ARCHITECTURE)"""

    @api.doc('mcp_outreach')
    @api.expect(api.model('MCPOutreachRequest', {
        'phone_number': fields.String(required=True, description='Patient phone number'),
        'patient_name': fields.String(required=True, description='Patient full name'),
        'outreach_type': fields.String(required=True, description='Type: conversation, notification, reminder, or form'),
        'discharge_summary': fields.Raw(description='Optional discharge summary context'),
        'custom_message': fields.String(description='Optional custom message for notifications/reminders'),
        'form_url': fields.String(description='Optional Google Form URL (uses default if not provided)')
    }))
    @api.response(200, 'Outreach completed')
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """
        Start patient outreach using MCP architecture.
        Routes through: API → AI Agent → MCP Server → Tools → Services
        
        Outreach Types:
        - conversation: Start structured SMS Q&A conversation
        - notification: Send one-time notification SMS
        - reminder: Send appointment reminder SMS
        - form: Send Google Form link for post-discharge questionnaire
        """
        if not outreach_agent:
            api.abort(500, 'MCP Outreach Agent not available. Check MCP initialization.')

        data = request.json
        phone_number = data.get('phone_number')
        patient_name = data.get('patient_name')
        outreach_type = data.get('outreach_type', 'form')
        discharge_summary = data.get('discharge_summary')
        custom_message = data.get('custom_message')
        form_url = data.get('form_url')

        if not phone_number or not patient_name:
            api.abort(400, 'Missing required fields: phone_number, patient_name')

        try:
            # Route through AI Agent → MCP Server → Tools
            result = outreach_agent.start_patient_outreach(
                phone_number=phone_number,
                patient_name=patient_name,
                outreach_type=outreach_type,
                discharge_summary=discharge_summary,
                custom_message=custom_message,
                form_url=form_url
            )
            return result, 200
        except Exception as e:
            return {'error': f'Error in MCP outreach: {str(e)}'}, 500


@ns.route('/mcp/tools')
class MCPTools(Resource):
    """List available MCP tools"""

    @api.doc('list_mcp_tools')
    @api.response(200, 'Success')
    def get(self):
        """Get list of all registered MCP tools"""
        if not outreach_agent:
            api.abort(500, 'MCP Outreach Agent not available.')
        
        try:
            result = outreach_agent.get_available_tools()
            return result, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/mcp/status')
class MCPStatus(Resource):
    """Get MCP architecture status"""

    @api.doc('mcp_status')
    @api.response(200, 'Success')
    def get(self):
        """Get MCP server and agent status"""
        if not outreach_agent:
            return {
                'mcp_enabled': False,
                'message': 'MCP architecture not initialized'
            }, 200
        
        try:
            result = outreach_agent.get_agent_status()
            result['mcp_enabled'] = True
            return result, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/mcp/execution-history')
class MCPExecutionHistory(Resource):
    """Get MCP tool execution history for demo dashboard"""

    @api.doc('mcp_execution_history')
    @api.response(200, 'Success')
    def get(self):
        """Get recent tool execution history"""
        if not mcp_server:
            return {'executions': [], 'total': 0}, 200
        try:
            limit = request.args.get('limit', 20, type=int)
            history = mcp_server.get_execution_history(limit=limit)
            return {'executions': history, 'total': len(history)}, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/mcp/architecture')
class MCPArchitecture(Resource):
    """Get MCP architecture overview for demo dashboard"""

    @api.doc('mcp_architecture')
    @api.response(200, 'Success')
    def get(self):
        """Get full architecture description for visualization"""
        tools_info = []
        if mcp_server:
            for tool_schema in mcp_server.list_tools():
                tools_info.append({
                    'name': tool_schema['name'],
                    'description': tool_schema['description'],
                    'parameters': tool_schema['parameters']
                })

        return {
            'layers': [
                {
                    'id': 'ui',
                    'name': 'Angular Dashboard',
                    'type': 'frontend',
                    'description': 'Patient management UI with real-time updates',
                    'tech': 'Angular 21'
                },
                {
                    'id': 'api',
                    'name': 'REST API',
                    'type': 'api',
                    'description': 'Flask-RESTX endpoints with Swagger docs',
                    'tech': 'Flask + Flask-RESTX'
                },
                {
                    'id': 'agent',
                    'name': 'AI Outreach Agent',
                    'type': 'agent',
                    'description': 'Orchestrates patient workflows, selects tools, manages context',
                    'tech': 'Python AI Agent'
                },
                {
                    'id': 'mcp',
                    'name': 'MCP Server',
                    'type': 'mcp',
                    'description': 'Tool registry, validation, execution, and history tracking',
                    'tech': 'Model Context Protocol'
                },
                {
                    'id': 'tools',
                    'name': 'MCP Tools',
                    'type': 'tools',
                    'description': 'Pluggable tools: SMS, AI Summary, Forms, Conversations',
                    'tech': 'MCPTool Interface',
                    'items': tools_info
                },
                {
                    'id': 'services',
                    'name': 'Backend Services',
                    'type': 'services',
                    'description': 'Twilio SMS, Google Gemini AI, Google Forms, PostgreSQL',
                    'tech': 'External Integrations'
                }
            ],
            'workflows': [
                {
                    'id': 'form_outreach',
                    'name': 'Form Outreach',
                    'description': 'Send post-discharge questionnaire form link via SMS',
                    'flow': ['ui', 'api', 'agent', 'mcp', 'tools', 'services']
                },
                {
                    'id': 'conversation',
                    'name': 'Patient Conversation',
                    'description': 'Start structured check-in Q&A via SMS',
                    'flow': ['ui', 'api', 'agent', 'mcp', 'tools', 'services']
                },
                {
                    'id': 'notification',
                    'name': 'SMS Notification',
                    'description': 'Send one-time notification to patient',
                    'flow': ['ui', 'api', 'agent', 'mcp', 'tools', 'services']
                },
                {
                    'id': 'ai_summary',
                    'name': 'AI Summary Generation',
                    'description': 'Generate AI-powered discharge summary',
                    'flow': ['ui', 'api', 'agent', 'mcp', 'tools', 'services']
                }
            ]
        }, 200


@ns.route('/mcp/demo-trace')
class MCPDemoTrace(Resource):
    """Simulate MCP workflow trace for demo (dry-run, no actual SMS sent)"""

    @api.doc('mcp_demo_trace')
    @api.expect(api.model('DemoTraceRequest', {
        'workflow': fields.String(required=True, description='Workflow to trace: form_outreach, conversation, notification, ai_summary'),
        'patient_name': fields.String(description='Demo patient name', default='Demo Patient'),
        'phone_number': fields.String(description='Demo phone number', default='+1234567890')
    }))
    @api.response(200, 'Success')
    def post(self):
        """Simulate a workflow trace showing each layer step-by-step (no real actions)"""
        import time

        data = request.json or {}
        workflow = data.get('workflow', 'form_outreach')
        patient_name = data.get('patient_name', 'Demo Patient')
        phone_number = data.get('phone_number', '+1234567890')

        trace_steps = []

        # Step 1: UI Layer
        trace_steps.append({
            'step': 1,
            'layer': 'Angular Dashboard',
            'layer_id': 'ui',
            'action': 'User clicks outreach button',
            'detail': f'Initiating {workflow} for {patient_name}',
            'status': 'completed',
            'data_sent': {'patient_name': patient_name, 'phone_number': phone_number, 'outreach_type': workflow}
        })

        # Step 2: API Layer
        trace_steps.append({
            'step': 2,
            'layer': 'REST API',
            'layer_id': 'api',
            'action': 'POST /api/mcp/outreach',
            'detail': 'Request validated, routed to AI Agent',
            'status': 'completed',
            'data_sent': {'endpoint': '/api/mcp/outreach', 'method': 'POST'}
        })

        # Step 3: Agent Layer
        tool_selected = {
            'form_outreach': 'send_form_link',
            'conversation': 'start_conversation',
            'notification': 'send_sms',
            'ai_summary': 'generate_summary'
        }.get(workflow, 'send_form_link')

        trace_steps.append({
            'step': 3,
            'layer': 'AI Outreach Agent',
            'layer_id': 'agent',
            'action': f'Agent selects tool: {tool_selected}',
            'detail': f'Workflow: {workflow} — Agent analyzes context, picks optimal tool',
            'status': 'completed',
            'data_sent': {'tool_selected': tool_selected, 'workflow': workflow}
        })

        # Step 4: MCP Server
        trace_steps.append({
            'step': 4,
            'layer': 'MCP Server',
            'layer_id': 'mcp',
            'action': f'execute_tool("{tool_selected}")',
            'detail': 'Parameter validation passed, tool found in registry, executing...',
            'status': 'completed',
            'data_sent': {'tool_name': tool_selected, 'params_validated': True, 'registry_lookup': 'success'}
        })

        # Step 5: MCP Tool
        trace_steps.append({
            'step': 5,
            'layer': f'MCP Tool: {tool_selected}',
            'layer_id': 'tools',
            'action': f'{tool_selected}.execute()',
            'detail': f'Tool executes business logic for {patient_name}',
            'status': 'completed',
            'data_sent': {'phone_number': phone_number, 'patient_name': patient_name}
        })

        # Step 6: Service Layer
        service_name = {
            'form_outreach': 'FormsService + Twilio SMS',
            'conversation': 'ConversationAgent + Twilio SMS',
            'notification': 'SMSService + Twilio',
            'ai_summary': 'AIService + Google Gemini'
        }.get(workflow, 'Service Layer')

        trace_steps.append({
            'step': 6,
            'layer': f'Service: {service_name}',
            'layer_id': 'services',
            'action': f'External API call (DRY RUN)',
            'detail': f'In production: sends to {phone_number} via {service_name}',
            'status': 'simulated',
            'data_sent': {'service': service_name, 'dry_run': True}
        })

        return {
            'workflow': workflow,
            'patient_name': patient_name,
            'total_steps': len(trace_steps),
            'trace': trace_steps,
            'summary': f'Workflow "{workflow}" traced through 6 architecture layers successfully (dry-run mode)'
        }, 200


@ns.route('/action-logs')
class ActionLogs(Resource):
    """Get patient action logs"""

    @api.doc('get_action_logs')
    @api.response(200, 'Success')
    def get(self):
        """Get recent action logs across all patients"""
        from services import ActionLogger
        
        try:
            limit = request.args.get('limit', 100, type=int)
            patient_id = request.args.get('patient_id', type=int)
            action = request.args.get('action', type=str)
            
            if patient_id:
                logs = ActionLogger.get_patient_logs(patient_id, limit)
            elif action:
                logs = ActionLogger.get_logs_by_action(action, limit)
            else:
                logs = ActionLogger.get_recent_logs(limit)
            
            return {
                'logs': logs,
                'total': len(logs)
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500


@ns.route('/action-logs/<int:patient_id>')
class PatientActionLogs(Resource):
    """Get action logs for a specific patient"""

    @api.doc('get_patient_action_logs')
    @api.response(200, 'Success')
    @api.response(404, 'Patient not found')
    def get(self, patient_id):
        """Get all action logs for a specific patient"""
        from services import ActionLogger
        
        try:
            limit = request.args.get('limit', 50, type=int)
            logs = ActionLogger.get_patient_logs(patient_id, limit)
            
            return {
                'patient_id': patient_id,
                'logs': logs,
                'total': len(logs)
            }, 200
        except Exception as e:
            return {'error': str(e)}, 500


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
        health_status = {
            'status': 'healthy',
            'message': 'API is running',
            'ai_provider': Config.AI_PROVIDER,
            'ai_service_available': ai_service is not None,
            'sms_service_available': sms_service is not None,
            'chat_service_available': chat_service is not None,
            'conversation_agent_available': conversation_agent is not None,
            'mcp_architecture': {
                'enabled': mcp_server is not None and outreach_agent is not None,
                'mcp_server_available': mcp_server is not None,
                'outreach_agent_available': outreach_agent is not None,
                'registered_tools': len(mcp_server.list_tools()) if mcp_server else 0
            }
        }
        return health_status, 200

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
