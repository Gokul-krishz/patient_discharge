# Project Structure

This project follows a clean, layered architecture similar to .NET best practices.

## 📁 Directory Structure

```
windsurf-project/
├── app.py                      # Main Flask application (entry point)
├── app_old.py                  # Backup of old monolithic code
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .env.example               # Example environment file
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation
├── PROJECT_STRUCTURE.md       # This file
│
├── config/                    # Configuration Layer
│   ├── __init__.py
│   └── settings.py           # Application settings and config
│
├── models/                    # Data Models Layer
│   ├── __init__.py
│   └── discharge_summary.py  # Discharge summary data model
│
├── services/                  # Business Logic Layer
│   ├── __init__.py
│   ├── file_extractor.py     # File text extraction service
│   └── ai_service.py         # AI summarization service
│
└── uploads/                   # Temporary file storage (auto-created)
```

## 🏗️ Architecture Layers

### 1. **Configuration Layer** (`config/`)
- **Purpose**: Centralized configuration management
- **Files**:
  - `settings.py`: All app settings, API keys, model names
- **Similar to**: `appsettings.json` in .NET

### 2. **Models Layer** (`models/`)
- **Purpose**: Data structures and domain models
- **Files**:
  - `discharge_summary.py`: Discharge summary data class
- **Similar to**: DTOs/Models in .NET

### 3. **Services Layer** (`services/`)
- **Purpose**: Business logic and external integrations
- **Files**:
  - `file_extractor.py`: Handles PDF, DOCX, TXT, Image extraction
  - `ai_service.py`: Manages Gemini/OpenAI integration
- **Similar to**: Service classes in .NET

### 4. **API Layer** (`app.py`)
- **Purpose**: REST API endpoints and request handling
- **Responsibilities**:
  - Route definitions
  - Request validation
  - Response formatting
  - Swagger documentation
- **Similar to**: Controllers in .NET

## 🔄 Data Flow

```
1. Client Request
   ↓
2. Flask Route (app.py)
   ↓
3. File Validation & Upload
   ↓
4. FileExtractor Service
   ↓
5. AIService (Gemini)
   ↓
6. JSON Response
```

## 📦 Component Responsibilities

### **FileExtractor Service**
```python
from services import FileExtractor

extractor = FileExtractor()
text = extractor.extract_text(filepath, filename)
```
- Extracts text from PDF using PyPDF2
- Extracts text from DOCX using python-docx
- Extracts text from images using Tesseract OCR
- Reads plain text files

### **AIService**
```python
from services import AIService

ai = AIService()  # Auto-detects provider from config
summary = ai.summarize_discharge_report(text)
```
- Initializes Gemini or OpenAI based on config
- Generates structured prompts
- Parses AI responses into JSON
- Handles errors gracefully

### **Config**
```python
from config import Config

print(Config.AI_PROVIDER)      # 'gemini'
print(Config.GEMINI_MODEL)     # 'models/gemini-2.5-flash'
Config.validate()              # Checks API keys
```

## 🎯 Benefits of This Structure

### For .NET Developers:
- **Separation of Concerns**: Each layer has a single responsibility
- **Dependency Injection**: Services are injected into routes
- **Testability**: Each component can be unit tested independently
- **Maintainability**: Easy to locate and modify specific functionality
- **Scalability**: Easy to add new services or models

### Comparison to .NET:
| Python Layer | .NET Equivalent |
|-------------|----------------|
| `config/` | `appsettings.json` + Configuration classes |
| `models/` | DTOs / Domain Models |
| `services/` | Service classes (Business Logic) |
| `app.py` | Controllers |

## 🔧 How to Extend

### Add a New File Type:
1. Add method to `services/file_extractor.py`
2. Update `extractors` dictionary
3. Add extension to `Config.ALLOWED_EXTENSIONS`

### Add a New AI Provider:
1. Add initialization method in `services/ai_service.py`
2. Add summarization method
3. Update config in `config/settings.py`
4. Update `.env` file

### Add a New Endpoint:
1. Create new Resource class in `app.py`
2. Define route with `@ns.route('/endpoint')`
3. Add Swagger documentation
4. Use existing services

## 📝 Code Quality

- **Type Hints**: Used throughout for better IDE support
- **Docstrings**: Every class and method documented
- **Error Handling**: Comprehensive try-catch blocks
- **Clean Code**: Single Responsibility Principle
- **DRY**: Reusable helper functions

## 🚀 Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
python app.py
```

The refactored code is cleaner, more maintainable, and follows industry best practices!
