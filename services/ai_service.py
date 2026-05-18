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
        """Generate prompt for discharge report extraction"""
        return f"""You are a medical AI assistant. Analyze the following patient discharge summary and extract structured information in JSON format.

Extract the following fields:
- patient_name: Patient's full name
- hospitalization_reason: Primary reason for hospitalization
- medication_changes: List of medication changes
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
                    {
                        "role": "system",
                        "content": "You are a medical data extraction assistant. Always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )

            result = self._clean_json_response(response.choices[0].message.content)
            return json.loads(result)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def generate_discharge_summary(self, conversation_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate professional post-discharge form response.

        Returns:
            Dictionary with details, action_required, and formatted_response
        """
        try:
            qa_pairs = conversation_data.get("qa_pairs", [])
            patient_context = conversation_data.get("patient_context", "")

            conversation_text = "\n".join([
                f"Q: {pair.get('question', '')}\nA: {pair.get('response', '')}"
                for pair in qa_pairs
            ])

            prompt = f"""You are a medical documentation assistant creating a professional care-team summary from a patient's post-discharge questionnaire.

Patient Context:
{patient_context}

Patient's Responses:
{conversation_text}

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
Raw: "Q: Recently discharged? A: Yes 3 days ago, Q: Medication changes? A: Yes blood pressure meds, Q: Symptoms? A: mild dizziness, Q: Contact? A: Yes"
Good: "The patient was discharged 3 days ago and has started a new medication for blood pressure management. They report mild dizziness, which is currently manageable, but this may require follow-up to assess whether it is related to the medication change. The patient has requested contact from the care team to discuss possible medication side effects."
Bad: "The patient reports being recently discharged: Yes 3 days ago. Medication changes include: Yes blood pressure meds."

Return ONLY valid JSON in this exact format:
{{
    "details": "The patient was discharged [timeframe] and [medication information]. They report [symptoms with clinical context]. [Any additional relevant information]. [Contact request if applicable].",
    "action_required": "The care team should [specific action based on symptoms, medications, and patient needs]."
}}"""

            if self.provider == 'gemini':
                model = self.gemini_client.GenerativeModel(Config.GEMINI_MODEL)
                response = model.generate_content(prompt)
                result_text = response.text
            else:
                response = self.openai_client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional medical documentation assistant. Always return valid JSON only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content

            result_text = self._clean_json_response(result_text)
            result = json.loads(result_text)

            details = result.get(
                "details",
                "The patient has submitted a post-discharge response for care team review."
            )

            action_required = result.get(
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

    def summarize_discharge_report(self, text: str) -> Dict[str, Any]:
        """
        Main method to summarize discharge report
        """
        if self.provider == 'gemini':
            return self.summarize_with_gemini(text)
        elif self.provider == 'openai':
            return self.summarize_with_openai(text)
        else:
            raise Exception(f"Unsupported AI provider: {self.provider}")