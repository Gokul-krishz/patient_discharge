# File Upload & Text Extraction API

A REST API built with Flask and Swagger that allows you to upload files and extract text content from various file formats.

## Features

- 📄 **PDF Text Extraction** - Extract text from PDF documents
- 📝 **DOCX Support** - Extract text from Microsoft Word documents
- 🖼️ **Image OCR** - Extract text from images using Tesseract OCR
- 📋 **Plain Text** - Read and display text files
- 🤖 **AI-Powered Discharge Summary** - Extract structured data from patient discharge reports using Google Gemini
- 📱 **SMS Notifications** - Send discharge summaries and reminders via Twilio
- 💬 **AI Patient Chat** - Answer patient questions about their discharge using AI
- 🔔 **Automated Communication** - Combined SMS + AI chat for patient support
- 📚 **Swagger UI** - Interactive API documentation and testing interface
- 🔌 **REST API** - Easy integration with any application

## Supported File Formats

- **PDF** (.pdf)
- **Word Documents** (.docx)
- **Text Files** (.txt)
- **Images** (.png, .jpg, .jpeg, .gif, .bmp)

## Prerequisites

Before running this application, ensure you have:

1. **Python 3.12+** installed (Python 3.14 has compatibility issues with some libraries)
2. **Tesseract OCR** installed (for image text extraction)
3. **Twilio Account** (for SMS features) - Optional, SMS features disabled if not configured

### Installing Tesseract OCR

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

1. **Clone or navigate to the project directory:**
```bash
cd /Users/gokulkumar/Projects/CascadeProjects/windsurf-project
```

2. **Create a virtual environment (recommended):**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip3 install -r requirements.txt
```

4. **Configure AI API Keys (for discharge summary feature):**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Choose 'openai' or 'gemini'
AI_PROVIDER=openai

# OpenAI API Key (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-key-here

# OR Google Gemini API Key (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=your-google-key-here
```

## Usage

1. **Start the Flask application:**
```bash
python3 app.py
```

2. **Access Swagger UI:**
Open your browser and navigate to:
```
http://localhost:8080/swagger
```

3. **Test the API:**
   
   **For simple text extraction:**
   - In Swagger UI, expand the `/api/extract-text` endpoint
   - Click "Try it out"
   - Upload a file using the file picker
   - Click "Execute" to see the response
   
   **For AI-powered discharge summary:**
   - Expand the `/api/discharge-summary` endpoint
   - Click "Try it out"
   - Upload a discharge report (PDF, DOCX, or TXT)
   - Click "Execute" to get structured JSON summary

## Project Structure

```
windsurf-project/
├── app.py                 # Main Flask REST API application
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── uploads/             # Temporary upload folder (auto-created)
```

## API Endpoints

### GET `/swagger`
Interactive Swagger UI documentation interface.

### POST `/api/extract-text`
Uploads a file and extracts text content.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (binary)

**Success Response (200):**
```json
{
  "filename": "example.pdf",
  "text": "Extracted text content...",
  "file_type": "pdf"
}
```

**Error Response (400/500):**
```json
{
  "error": "Error message"
}
```

### POST `/api/discharge-summary`
Upload a patient discharge report and get AI-powered structured summary.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (discharge report in PDF, DOCX, or TXT format)

**Success Response (200):**
```json
{
  "filename": "discharge_report.pdf",
  "extracted_text": "Full text content...",
  "summary": {
    "patient_name": "John Doe",
    "hospitalization_reason": "Fluid overload",
    "medication_changes": [
      "Started Furosemide 40mg daily",
      "Discontinued Lisinopril"
    ],
    "current_symptoms": [
      "Mild shortness of breath",
      "Fatigue"
    ],
    "outcomes_after_discharge": [
      "Stable condition",
      "Improved breathing"
    ],
    "care_team_updates": [
      "Nephrologist follow-up required in 3 days",
      "Nutritionist consultation recommended"
    ],
    "diet_restrictions": [
      "Low sodium diet",
      "Fluid restriction"
    ],
    "risk_indicators": [
      "High readmission risk"
    ]
  },
  "ai_provider": "openai"
}
```

### POST `/api/send-sms`
Send SMS notification to patient via Twilio.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "patient_name": "John Doe",
  "message_type": "discharge_summary"
}
```

### POST `/api/patient-chat`
Get AI response to patient question (no SMS).

**Request:**
```json
{
  "patient_id": "+1234567890",
  "question": "Can I take ibuprofen?",
  "discharge_summary": { ... }
}
```

### POST `/api/patient-chat-sms`
Get AI response and send via SMS to patient.

**Request:**
```json
{
  "phone_number": "+1234567890",
  "question": "What should I eat?",
  "discharge_summary": { ... }
}
```

### GET `/api/health`
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running",
  "ai_service_available": true,
  "sms_service_available": true,
  "chat_service_available": true
}
```

## Using the API with cURL

```bash
# Extract text from a file
curl -X POST "http://localhost:8080/api/extract-text" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/file.pdf"

# Get AI-powered discharge summary
curl -X POST "http://localhost:8080/api/discharge-summary" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/discharge_report.pdf"

# Check API health
curl -X GET "http://localhost:8080/api/health"
```

## Using the API with Python

```python
import requests

# Simple text extraction
url = "http://localhost:8080/api/extract-text"
files = {'file': open('document.pdf', 'rb')}
response = requests.post(url, files=files)
print(response.json())

# AI-powered discharge summary
url = "http://localhost:8080/api/discharge-summary"
files = {'file': open('discharge_report.pdf', 'rb')}
response = requests.post(url, files=files)
summary = response.json()
print(f"Patient: {summary['summary']['patient_name']}")
print(f"Reason: {summary['summary']['hospitalization_reason']}")
print(f"Medications: {summary['summary']['medication_changes']}")
```

## Configuration

You can modify these settings in `app.py`:

- `MAX_CONTENT_LENGTH`: Maximum file size (default: 16MB)
- `UPLOAD_FOLDER`: Temporary upload directory
- `ALLOWED_EXTENSIONS`: Supported file extensions

## Security Features

- File type validation
- Secure filename handling
- Automatic cleanup of uploaded files
- File size limits

## Troubleshooting

**Issue: OCR not working**
- Ensure Tesseract is installed and in your system PATH
- On macOS, you may need to set: `pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'`

**Issue: PDF extraction fails**
- Some PDFs may be scanned images - use image upload with OCR instead
- Encrypted PDFs are not supported

**Issue: Port already in use**
- Change the port in `app.py`: `app.run(debug=True, port=5001)`

## License

This project is open source and available for personal and commercial use.

## Contributing

Feel free to submit issues and enhancement requests!
