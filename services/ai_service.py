"""
AI Service for discharge summary extraction
Supports Google Gemini and OpenAI
"""
import json
from typing import Dict, Any
from config import Config

class AIService:
    """Service for AI-powered text summarization"""
    
    def __init__(self):
        self.provider = Config.AI_PROVIDER
        self.gemini_client = None
        self.openai_client = None
        
        if self.provider == 'gemini':
            self._initialize_gemini()
        elif self.provider == 'openai':
            self._initialize_openai()
        else:
            raise ValueError(f"Invalid AI provider: {self.provider}")
    
    def _initialize_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.gemini_client = genai
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini: {str(e)}")
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI: {str(e)}")
    
    def _get_prompt(self, text: str) -> str:
        """Generate prompt for AI model"""
        return f"""You are a medical AI assistant. Analyze the following patient discharge summary and extract structured information in JSON format.

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
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from AI model"""
        response = response.strip()
        response = response.replace('```json', '').replace('```', '').strip()
        return response
    
    def summarize_with_gemini(self, text: str) -> Dict[str, Any]:
        """Summarize using Google Gemini"""
        if not self.gemini_client:
            raise Exception("Gemini client not initialized")
        
        try:
            model = self.gemini_client.GenerativeModel(Config.GEMINI_MODEL)
            prompt = self._get_prompt(text)
            response = model.generate_content(prompt)
            
            result = self._clean_json_response(response.text)
            return json.loads(result)
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def summarize_with_openai(self, text: str) -> Dict[str, Any]:
        """Summarize using OpenAI"""
        if not self.openai_client:
            raise Exception("OpenAI client not initialized")
        
        try:
            prompt = self._get_prompt(text)
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a medical data extraction assistant. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            result = self._clean_json_response(response.choices[0].message.content)
            return json.loads(result)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def summarize_discharge_report(self, text: str) -> Dict[str, Any]:
        """
        Main method to summarize discharge report
        
        Args:
            text: Extracted text from discharge report
            
        Returns:
            Dictionary with structured discharge summary
        """
        if self.provider == 'gemini':
            return self.summarize_with_gemini(text)
        elif self.provider == 'openai':
            return self.summarize_with_openai(text)
        else:
            raise Exception(f"Unsupported AI provider: {self.provider}")
