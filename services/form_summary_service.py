"""
Form Summary Service
Generates AI summaries of Google Form responses
"""
from typing import Dict, Any
from services.ai_service import AIService


class FormSummaryService:
    """Service for generating AI summaries of form responses"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def generate_form_summary(
        self,
        patient_name: str,
        form_responses: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate AI summary of Google Form responses
        
        Args:
            patient_name: Name of the patient
            form_responses: Dictionary of form responses
            
        Returns:
            Dictionary with details, action_required, and formatted_response
        """
        try:
            # Build conversation-like format for AI
            qa_pairs = self._convert_responses_to_qa_pairs(form_responses)
            
            conversation_data = {
                "patient_context": f"Patient: {patient_name}",
                "qa_pairs": qa_pairs
            }
            
            # Use AI service to generate summary
            summary = self.ai_service.generate_discharge_summary(conversation_data)
            
            return summary
            
        except Exception as e:
            details = f"Error generating summary: {str(e)}"
            action_required = "The care team should manually review the patient's response."
            
            formatted_response = f"""Details -

{details}

Action Required:
{action_required}"""
            
            return {
                "details": details,
                "action_required": action_required,
                "formatted_response": formatted_response
            }
    
    def _convert_responses_to_qa_pairs(self, form_responses: Dict[str, Any]) -> list:
        """Convert form responses to Q&A format for AI processing"""
        qa_pairs = []
        
        # Map form fields to questions
        field_questions = {
            'recently_discharged': 'Were you recently discharged from the hospital?',
            'medication_changes': 'Did the hospital prescribe any new medications or change existing medications?',
            'current_symptoms': 'Are you currently experiencing any symptoms such as swelling, shortness of breath, pain, dizziness, or weakness?',
            'care_team_notes': 'Is there anything your nephrologist or care team should know about your recent hospitalization or recovery?',
            'contact_request': 'Would you like someone from your care team to contact you?'
        }
        
        for field, question in field_questions.items():
            answer = form_responses.get(field)
            if answer:
                qa_pairs.append({
                    "question": question,
                    "response": str(answer)
                })
        
        return qa_pairs
