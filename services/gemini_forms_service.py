"""
Google Gemini AI Service for generating form response summaries
"""
import os
import json
import google.generativeai as genai
from typing import Dict, Any
from config import Config


class GeminiFormsService:
    """Service for generating AI summaries using Google Gemini"""
    
    def __init__(self):
        self.api_key = Config.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
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
            prompt = self._build_summary_prompt(patient_name, form_responses)
            
            # Call Gemini API
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Clean and parse JSON
            result_text = self._clean_json_response(result_text)
            parsed_result = json.loads(result_text)
            
            details = parsed_result.get("details", "")
            action_required = parsed_result.get("action_required", "")
            
            if not details:
                details = "The patient has submitted a post-discharge health questionnaire. Please review the raw responses for clinical assessment."
            if not action_required:
                action_required = "The care team should schedule a post-discharge follow-up to assess the patient's recovery status and address any reported symptoms or medication concerns."
            
            formatted_response = f"""Details -

{details}

Action Required:
{action_required}"""
            
            return {
                "details": details,
                "action_required": action_required,
                "formatted_response": formatted_response
            }
                
        except Exception as e:
            print(f"Error generating summary with Gemini: {str(e)}")
            return self._generate_fallback_summary(patient_name, form_responses)
    
    def _build_summary_prompt(
        self,
        patient_name: str,
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
8. "action_required" MUST be specific to THIS patient's symptoms, medications, and contact request
9. NEVER use generic phrases like "review the patient's response and follow up if required"
10. If patient requests contact, the action_required MUST say "contact the patient" explicitly
11. If there are symptoms, the action_required MUST address those specific symptoms
12. If there are medication changes, the action_required MUST mention assessing those medications

EXAMPLE:
Raw: "Recently Discharged: Yes 3 days ago, Medication Changes: Yes blood pressure meds, Symptoms: mild dizziness, Contact: Yes"
details: "The patient was discharged 3 days ago and has started a new medication for blood pressure management. They report mild dizziness, which is currently manageable, but this may require follow-up to assess whether it is related to the medication change. The patient has requested contact from the care team to discuss possible medication side effects."
action_required: "The care team should contact the patient to review the reported dizziness and assess whether it is linked to the new blood pressure medication, adjusting the dosage or treatment plan as necessary."

Return ONLY valid JSON in this exact format:
{{
    "details": "ONE cohesive clinical paragraph about this patient based on their actual responses.",
    "action_required": "ONE specific instruction directly tied to this patient's symptoms, medications, and contact request."
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
        form_responses: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate a basic summary if AI service fails"""
        
        discharged = form_responses.get('recently_discharged', 'Unknown')
        medications = form_responses.get('medication_changes', 'Not provided')
        symptoms = form_responses.get('current_symptoms', 'None reported')
        notes = form_responses.get('care_team_notes', 'None')
        contact = form_responses.get('contact_request', 'No')
        
        details_parts = []
        
        if discharged and discharged.lower() not in ['unknown', 'not provided']:
            details_parts.append(f"The patient has confirmed a recent hospital discharge ({discharged}). ")
        else:
            details_parts.append("The patient has submitted a post-discharge health questionnaire. ")
        
        if medications and medications.lower() not in ['no', 'none', 'not provided']:
            details_parts.append(f"Medication changes have been reported: {medications}. ")
        
        if symptoms and symptoms.lower() not in ['none', 'no symptoms', 'not provided', 'no']:
            details_parts.append(f"The patient reports the following symptoms: {symptoms}. ")
        else:
            details_parts.append("No significant symptoms were reported at this time. ")
        
        if notes and notes.lower() not in ['none', 'not provided', 'no']:
            details_parts.append(f"Additional notes from the patient: {notes}. ")
        
        if contact.lower() in ['yes', 'y']:
            details_parts.append("The patient has requested to be contacted by the care team.")
        
        details = "".join(details_parts)
        
        # Build specific action_required based on actual data
        action_parts = []
        if contact.lower() in ['yes', 'y']:
            action_parts.append("contact the patient as requested")
        if symptoms and symptoms.lower() not in ['none', 'no symptoms', 'not provided', 'no']:
            action_parts.append(f"assess the reported symptoms ({symptoms})")
        if medications and medications.lower() not in ['no', 'none', 'not provided']:
            action_parts.append(f"review the medication changes ({medications}) for any adverse effects")
        
        if action_parts:
            action_required = f"The care team should {', and '.join(action_parts)}."
        else:
            action_required = "The care team should schedule a routine post-discharge follow-up with the patient to confirm recovery progress."
        
        formatted_response = f"""Details -

{details}

Action Required:
{action_required}"""
        
        return {
            "details": details,
            "action_required": action_required,
            "formatted_response": formatted_response
        }
