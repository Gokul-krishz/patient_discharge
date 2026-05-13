"""
Patient Chat Service - AI-powered conversational interface for patient questions
"""
from typing import Dict, Any, List, Optional
from config import Config
from services.ai_service import AIService

class PatientChatService:
    """Service for managing AI-powered patient conversations"""
    
    def __init__(self):
        """Initialize chat service with AI"""
        self.ai_service = AIService()
        # In production, use a database to store conversation history
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def _get_chat_prompt(
        self,
        patient_context: Dict[str, Any],
        question: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate prompt for patient chat
        
        Args:
            patient_context: Patient's discharge summary data
            question: Patient's current question
            conversation_history: Previous messages in conversation
            
        Returns:
            Formatted prompt for AI
        """
        prompt = f"""You are a helpful medical assistant helping a patient understand their discharge summary.

Patient Information:
- Name: {patient_context.get('patient_name', 'Unknown')}
- Hospitalization Reason: {patient_context.get('hospitalization_reason', 'N/A')}
- Current Medications: {', '.join(patient_context.get('medication_changes', []))}
- Symptoms: {', '.join(patient_context.get('current_symptoms', []))}
- Diet Restrictions: {', '.join(patient_context.get('diet_restrictions', []))}
- Follow-up Care: {', '.join(patient_context.get('care_team_updates', []))}

Conversation History:
"""
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            prompt += f"{msg['role']}: {msg['content']}\n"
        
        prompt += f"\nPatient Question: {question}\n\n"
        prompt += """Instructions:
1. Answer in a friendly, empathetic tone
2. Keep responses concise (2-3 sentences for SMS)
3. Use simple, non-medical language
4. If it's a medical emergency, advise calling 911
5. For complex medical questions, suggest contacting their doctor
6. Reference their specific discharge information when relevant

Response:"""
        
        return prompt
    
    def get_response(
        self,
        patient_id: str,
        patient_context: Dict[str, Any],
        question: str
    ) -> str:
        """
        Get AI response to patient question
        
        Args:
            patient_id: Unique patient identifier (phone number or ID)
            patient_context: Patient's discharge summary
            question: Patient's question
            
        Returns:
            AI-generated response
        """
        # Get or create conversation history
        if patient_id not in self.conversation_history:
            self.conversation_history[patient_id] = []
        
        history = self.conversation_history[patient_id]
        
        # Add patient question to history
        history.append({
            'role': 'patient',
            'content': question
        })
        
        # Generate prompt
        prompt = self._get_chat_prompt(patient_context, question, history)
        
        # Get AI response
        try:
            if Config.AI_PROVIDER == 'gemini':
                response = self._get_gemini_response(prompt)
            else:
                response = self._get_openai_response(prompt)
            
            # Add assistant response to history
            history.append({
                'role': 'assistant',
                'content': response
            })
            
            # Keep only last 20 messages to manage memory
            if len(history) > 20:
                self.conversation_history[patient_id] = history[-20:]
            
            return response
            
        except Exception as e:
            return f"I apologize, but I'm having trouble processing your question right now. Please contact your healthcare provider directly for assistance. Error: {str(e)}"
    
    def _get_gemini_response(self, prompt: str) -> str:
        """Get response from Gemini"""
        import google.generativeai as genai
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    
    def _get_openai_response(self, prompt: str) -> str:
        """Get response from OpenAI"""
        import openai
        client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200  # Keep responses concise for SMS
        )
        return response.choices[0].message.content.strip()
    
    def clear_conversation(self, patient_id: str):
        """Clear conversation history for a patient"""
        if patient_id in self.conversation_history:
            del self.conversation_history[patient_id]
    
    def get_conversation_summary(self, patient_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a patient"""
        return self.conversation_history.get(patient_id, [])
    
    def detect_emergency(self, question: str) -> bool:
        """
        Detect if patient message indicates an emergency
        
        Args:
            question: Patient's message
            
        Returns:
            True if emergency keywords detected
        """
        emergency_keywords = [
            'chest pain', 'can\'t breathe', 'breathing', 'unconscious',
            'bleeding', 'severe pain', 'emergency', '911',
            'heart attack', 'stroke', 'seizure', 'allergic reaction'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in emergency_keywords)
