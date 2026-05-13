import os
import json
from flask import Flask, request
from flask_restx import Api, Resource, fields
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import PyPDF2
import docx
from PIL import Image
import pytesseract
from dotenv import load_dotenv

load_dotenv()

# Try to import AI libraries with error handling
openai = None
genai = None
AI_IMPORT_ERROR = None

try:
    import openai
except Exception as e:
    AI_IMPORT_ERROR = f"OpenAI import error: {str(e)}"

try:
    import google.generativeai as genai
except Exception as e:
    if AI_IMPORT_ERROR:
        AI_IMPORT_ERROR += f" | Gemini import error: {str(e)}"
    else:
        AI_IMPORT_ERROR = f"Gemini import error: {str(e)}"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

api = Api(
    app,
    version='1.0',
    title='File Text Extraction API',
    description='Upload files and extract text content from PDF, DOCX, TXT, and Images',
    doc='/swagger'
)

AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if AI_PROVIDER == 'openai' and OPENAI_API_KEY and openai:
    openai.api_key = OPENAI_API_KEY
elif AI_PROVIDER == 'gemini' and GOOGLE_API_KEY and genai:
    genai.configure(api_key=GOOGLE_API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        text = f"Error extracting PDF: {str(e)}"
    return text

def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        text = f"Error extracting DOCX: {str(e)}"
    return text

def extract_text_from_image(filepath):
    try:
        image = Image.open(filepath)
        text = pytesseract.image_to_string(image)
    except Exception as e:
        text = f"Error extracting text from image: {str(e)}"
    return text

def extract_text_from_txt(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        text = f"Error reading text file: {str(e)}"
    return text

def extract_text(filepath, filename):
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension == 'pdf':
        return extract_text_from_pdf(filepath)
    elif extension == 'docx':
        return extract_text_from_docx(filepath)
    elif extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
        return extract_text_from_image(filepath)
    elif extension == 'txt':
        return extract_text_from_txt(filepath)
    else:
        return "Unsupported file format"

def summarize_with_openai(text):
    """Summarize discharge report using OpenAI"""
    if not openai:
        raise Exception("OpenAI library not available. This may be due to Python version compatibility issues.")
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""You are a medical AI assistant. Analyze the following patient discharge summary and extract structured information in JSON format.

Extract the following fields:
- patient_name: Patient's full name
- hospitalization_reason: Primary reason for hospitalization
- medication_changes: List of medication changes (started, discontinued, adjusted)
- current_symptoms: List of current symptoms at discharge
- outcomes_after_discharge: Expected outcomes and current condition
- care_team_updates: Follow-up appointments and care team instructions
- diet_restrictions: Dietary restrictions and recommendations
- risk_indicators: Any risk factors or readmission risks

Discharge Summary Text:
{text}

Return ONLY valid JSON without any markdown formatting or code blocks."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a medical data extraction assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result = response.choices[0].message.content.strip()
        result = result.replace('```json', '').replace('```', '').strip()
        return json.loads(result)
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

def summarize_with_gemini(text):
    """Summarize discharge report using Google Gemini"""
    if not genai:
        raise Exception("Google Gemini library not available. This may be due to Python version compatibility issues. Try using OpenAI instead by setting AI_PROVIDER=openai in .env")
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        prompt = f"""You are a medical AI assistant. Analyze the following patient discharge summary and extract structured information in JSON format.

Extract the following fields:
- patient_name: Patient's full name
- hospitalization_reason: Primary reason for hospitalization
- medication_changes: List of medication changes (started, discontinued, adjusted)
- current_symptoms: List of current symptoms at discharge
- outcomes_after_discharge: Expected outcomes and current condition
- care_team_updates: Follow-up appointments and care team instructions
- diet_restrictions: Dietary restrictions and recommendations
- risk_indicators: Any risk factors or readmission risks

Discharge Summary Text:
{text}

Return ONLY valid JSON without any markdown formatting or code blocks."""

        response = model.generate_content(prompt)
        result = response.text.strip()
        result = result.replace('```json', '').replace('```', '').strip()
        return json.loads(result)
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

def summarize_discharge_report(text):
    """Main function to summarize discharge report using configured AI provider"""
    if AI_IMPORT_ERROR and not openai and not genai:
        raise Exception(f"AI libraries not available: {AI_IMPORT_ERROR}. You may need to use Python 3.11 or 3.12 for better compatibility.")
    
    if AI_PROVIDER == 'openai':
        if not OPENAI_API_KEY:
            raise Exception("OpenAI API key not configured. Please set OPENAI_API_KEY in .env file")
        if not openai:
            raise Exception("OpenAI library not available. Try using Gemini by setting AI_PROVIDER=gemini in .env")
        return summarize_with_openai(text)
    elif AI_PROVIDER == 'gemini':
        if not GOOGLE_API_KEY:
            raise Exception("Google API key not configured. Please set GOOGLE_API_KEY in .env file")
        if not genai:
            raise Exception("Google Gemini library not available due to Python 3.14 compatibility. Use OpenAI instead by setting AI_PROVIDER=openai in .env")
        return summarize_with_gemini(text)
    else:
        raise Exception(f"Invalid AI provider: {AI_PROVIDER}. Use 'openai' or 'gemini'")

ns = api.namespace('api', description='File text extraction operations')

upload_parser = api.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, 
                          help='File to extract text from (PDF, DOCX, TXT, or Image)')

response_model = api.model('TextExtractionResponse', {
    'filename': fields.String(description='Name of the uploaded file'),
    'text': fields.String(description='Extracted text content'),
    'file_type': fields.String(description='Type of file processed')
})

error_model = api.model('ErrorResponse', {
    'error': fields.String(description='Error message')
})

discharge_summary_model = api.model('DischargeSummaryResponse', {
    'filename': fields.String(description='Name of the uploaded file'),
    'extracted_text': fields.String(description='Raw extracted text from file'),
    'summary': fields.Raw(description='Structured discharge summary in JSON format'),
    'ai_provider': fields.String(description='AI provider used (openai or gemini)')
})

@ns.route('/extract-text')
class TextExtraction(Resource):
    @api.doc('extract_text_from_file')
    @api.expect(upload_parser)
    @api.response(200, 'Success', response_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Upload a file and extract its text content"""
        if 'file' not in request.files:
            api.abort(400, 'No file part in the request')
        
        file = request.files['file']
        
        if file.filename == '':
            api.abort(400, 'No file selected')
        
        if not allowed_file(file.filename):
            api.abort(400, f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}')
        
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            extracted_text = extract_text(filepath, filename)
            extension = filename.rsplit('.', 1)[1].lower()
            
            os.remove(filepath)
            
            return {
                'filename': filename,
                'text': extracted_text,
                'file_type': extension
            }, 200
        except Exception as e:
            return {'error': f'Error processing file: {str(e)}'}, 500

@ns.route('/discharge-summary')
class DischargeSummary(Resource):
    @api.doc('extract_discharge_summary')
    @api.expect(upload_parser)
    @api.response(200, 'Success', discharge_summary_model)
    @api.response(400, 'Bad Request', error_model)
    @api.response(500, 'Internal Server Error', error_model)
    def post(self):
        """Upload a discharge report and get AI-powered structured summary"""
        if 'file' not in request.files:
            api.abort(400, 'No file part in the request')
        
        file = request.files['file']
        
        if file.filename == '':
            api.abort(400, 'No file selected')
        
        if not allowed_file(file.filename):
            api.abort(400, f'File type not allowed. Supported formats: {", ".join(ALLOWED_EXTENSIONS)}')
        
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            extracted_text = extract_text(filepath, filename)
            
            summary = summarize_discharge_report(extracted_text)
            
            os.remove(filepath)
            
            return {
                'filename': filename,
                'extracted_text': extracted_text,
                'summary': summary,
                'ai_provider': AI_PROVIDER
            }, 200
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return {'error': f'Error processing file: {str(e)}'}, 500

@ns.route('/health')
class Health(Resource):
    @api.doc('health_check')
    def get(self):
        """Check API health status"""
        return {'status': 'healthy', 'message': 'API is running'}, 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
