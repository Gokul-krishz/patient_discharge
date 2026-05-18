"""
OpenRouter AI Service for generating form response summaries
"""
import os
import json
import requests
from typing import Dict, Any


class OpenRouterService:
    """Service for generating AI summaries using OpenRouter API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet:beta"  # Correct OpenRouter model name
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    
    def generate_form_summary(
        self,
        patient_name: str,
        patient_phone: str,
        form_responses: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate a comprehensive summary of the patient's form responses
        
        Args:
            patient_name: Patient's name
            patient_phone: Patient's phone number
            form_responses: Dictionary of form responses
            
        Returns:
            Dictionary with details, action_required, and formatted_response
        """
        try:
            # Build the prompt
            prompt = self._build_summary_prompt(patient_name, patient_phone, form_responses)
            
            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional medical documentation assistant. Always return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 300
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                result_text = result['choices'][0]['message']['content']
                result_text = self._clean_json_response(result_text)
                parsed_result = json.loads(result_text)
                
                details = parsed_result.get(
                    "details",
                    "The patient has submitted a post-discharge response for care team review."
                )
                
                action_required = parsed_result.get(
                    "action_required",
                    "The care team should review the patient's response and follow up if required."
                )
                
                formatted_response = f"""Details -

{details}

Action Required:
{action_required}"""
                
                return {
                    "details": details,
                    "action_required": action_required,
                    "formatted_response": formatted_response
                }
            else:
                error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                print(error_msg)
                return self._generate_fallback_summary(patient_name, patient_phone, form_responses)
                
        except Exception as e:
            print(f"Error generating summary with OpenRouter: {str(e)}")
            return self._generate_fallback_summary(patient_name, patient_phone, form_responses)
    
    def _build_summary_prompt(
        self,
        patient_name: str,
        patient_phone: str,
        form_responses: Dict[str, Any]
    ) -> str:
        """Build the prompt for AI summary generation"""
        
        prompt = f"""You are a medical documentation assistant creating a professional care-team summary from a patient's post-discharge questionnaire.

Patient: {patient_name}

Raw Patient Responses:
- Recently Discharged: {form_responses.get('recently_discharged', 'Not provided')}
- Medication Changes: {form_responses.get('medication_changes', 'Not provided')}
- Current Symptoms: {form_responses.get('current_symptoms', 'Not provided')}
- Care Team Notes: {form_responses.get('care_team_notes', 'Not provided')}
- Contact Request: {form_responses.get('contact_request', 'Not provided')}

CRITICAL INSTRUCTIONS:
1. Transform raw responses into a flowing professional narrative paragraph
2. NEVER copy answers verbatim (e.g., "Yes just 15 mins ago" → "was discharged 15 minutes ago")
3. NEVER include "Yes" or "No" as standalone words - integrate the information naturally
4. NEVER list items - write as connected sentences in paragraph form
5. DO NOT use emojis, bullet points, or section headers
6. DO NOT mention phone numbers
7. Synthesize all information into ONE cohesive clinical paragraph for "details"
8. Create ONE clear actionable instruction for "action_required"
9. If patient requests contact, explicitly state this in action_required

EXAMPLE TRANSFORMATION:
Raw: "Recently Discharged: Yes 3 days ago, Medication Changes: Yes blood pressure meds, Symptoms: mild dizziness, Contact: Yes"
Good: "The patient was discharged 3 days ago and has started a new medication for blood pressure management. They report mild dizziness, which is currently manageable, but this may require follow-up to assess whether it is related to the medication change. The patient has requested contact from the care team to discuss possible medication side effects."
Bad: "The patient reports being recently discharged: Yes 3 days ago. Medication changes include: Yes blood pressure meds."

Return ONLY valid JSON in this exact format:
{{
    "details": "The patient was discharged [timeframe] and [medication information]. They report [symptoms with clinical context]. [Any additional relevant information]. [Contact request if applicable].",
    "action_required": "The care team should [specific action based on symptoms, medications, and patient needs]."
}}"""

        return prompt
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response from AI model"""
        response = response.strip()
        response = response.replace('```json', '').replace('```', '').strip()
        return response
    
    def _generate_fallback_summary(
        self,
        patient_name: str,
        patient_phone: str,
        form_responses: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate a basic summary if AI service fails"""
        
        discharged = form_responses.get('recently_discharged', 'Unknown')
        medications = form_responses.get('medication_changes', 'Not provided')
        symptoms = form_responses.get('current_symptoms', 'None reported')
        notes = form_responses.get('care_team_notes', 'None')
        contact = form_responses.get('contact_request', 'No')
        
        details_parts = [
            f"The patient reports being recently discharged: {discharged}. "
        ]
        
        if medications and medications.lower() not in ['no', 'none', 'not provided']:
            details_parts.append(f"Medication changes include: {medications}. ")
        
        details_parts.append(f"Current symptoms: {symptoms}. ")
        
        if notes and notes.lower() not in ['none', 'not provided', 'no']:
            details_parts.append(f"Additional notes: {notes}. ")
        
        if contact.lower() in ['yes', 'y']:
            details_parts.append("Patient has requested to be contacted by the care team.")
        
        details = "".join(details_parts)
        action_required = "The care team should review the patient's response and follow up if required."
        
        formatted_response = f"""Details -

{details}

Action Required:
{action_required}"""
        
        return {
            "details": details,
            "action_required": action_required,
            "formatted_response": formatted_response
        }
