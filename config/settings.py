"""
Application configuration settings
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    """Application configuration class"""
    
    # Flask settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 8080
    DEBUG = True
    
    # AI Provider settings
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Gemini settings
    GEMINI_MODEL = 'models/gemini-2.5-flash'
    
    # OpenAI settings
    OPENAI_MODEL = 'gpt-4o-mini'
    
    # Google Forms
    GOOGLE_FORM_URL = os.getenv('GOOGLE_FORM_URL', '')

    # PostgreSQL Database
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/patient_discharge_db'
    )
    
    # Twilio settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # Email settings (for care team notifications)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL', os.getenv('SMTP_USERNAME'))
    
    @staticmethod
    def validate():
        """Validate configuration"""
        if Config.AI_PROVIDER == 'gemini' and not Config.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY not set in .env file")
        elif Config.AI_PROVIDER == 'openai' and not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in .env file")
    
    @staticmethod
    def validate_twilio():
        """Validate Twilio configuration"""
        if not Config.TWILIO_ACCOUNT_SID:
            raise ValueError("TWILIO_ACCOUNT_SID not set in .env file")
        if not Config.TWILIO_AUTH_TOKEN:
            raise ValueError("TWILIO_AUTH_TOKEN not set in .env file")
        if not Config.TWILIO_PHONE_NUMBER:
            raise ValueError("TWILIO_PHONE_NUMBER not set in .env file")
