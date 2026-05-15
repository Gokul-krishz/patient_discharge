from openai import OpenAI
from app.config import settings
from typing import Dict, Optional


class AIService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL
        )
    
    def generate_first_question(self, patient_context: str) -> str:
        """
        Generate the first question for a patient based on their medical context.
        Triggered from patient discharge event.
        """
        try:
            prompt = f"""
            You are a healthcare assistant conducting an SMS outreach to a patient on behalf of their care team.
            This message is triggered after the patient's discharge from the hospital.

            Patient Context: {patient_context}

            Generate a warm, friendly opening message to check on the patient's post-discharge recovery.
            The message should:
            - Address the patient by name
            - Start by identifying this as a message from their care team
            - Mention this is a post-discharge follow-up check
            - Ask if they were recently discharged from the hospital
            - Be simple and clear (SMS format)
            - Be relevant to their medical context if provided
            - Be no more than 160 characters if possible
            - DO NOT include closing phrases like "Take care!" or "Best regards" - just ask the question

            Return only the message text, nothing else.
            """

            response_obj = self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful healthcare assistant that conducts post-discharge SMS outreach for care teams. Never include closing phrases like 'Take care!' or 'Best regards' in your questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )

            return response_obj.choices[0].message.content.strip()

        except Exception as e:
            # If AI generation fails, return a default question with context
            return "Hi from your care team. Following up on your discharge - how are you recovering at home?"
    
    def generate_next_question(self, patient_context: str, qa_history: list) -> tuple[str, bool]:
        """
        Generate the next question based on the conversation history.

        Returns:
            tuple: (question_text, should_continue)
                   - question_text: The next question to ask
                   - should_continue: Whether to continue asking questions (True) or end conversation (False)
        """
        try:
            # Build conversation history
            history_text = "\n".join([
                f"Q: {qa['question']}\nA: {qa['response']}"
                for qa in qa_history
            ])

            # Count questions asked
            questions_asked = len(qa_history)

            # Set question limits
            MINIMUM_QUESTIONS = 4
            MAXIMUM_QUESTIONS = 8

            # Check if we've reached the maximum
            if questions_asked >= MAXIMUM_QUESTIONS:
                return None, False

            prompt = f"""
            You are a healthcare assistant conducting an SMS outreach to a patient on behalf of their care team.
            This is a post-discharge follow-up to gather important health information.

            Patient Context: {patient_context}
            Questions asked so far: {questions_asked}
            Maximum questions allowed: {MAXIMUM_QUESTIONS}

            Conversation so far:
            {history_text}

            CRITICAL: You must ask questions to gather the following information (in order if not already covered):
            1. Confirmation of hospitalization/discharge
            2. Whether any new medications were prescribed
            3. Whether they are experiencing current symptoms
            4. Any outcomes their nephrologist/care team should be aware of

            IMPORTANT RULES:
            - DO NOT repeat questions about topics already discussed
            - Check the conversation history to avoid asking about the same topic twice
            - End the conversation after {MAXIMUM_QUESTIONS} questions maximum
            - If all 4 critical topics are covered, end the conversation
            - DO NOT ask about the same topic multiple times

            Based on the conversation history, decide:
            1. Should we ask another question? (End if all topics covered or max questions reached)
            2. If yes, what should be the next follow-up question? (Must be about a NEW topic)

            Guidelines:
            - Review the conversation history carefully to identify what topics have been covered
            - Only ask about topics that haven't been discussed yet
            - If all 4 critical topics are covered, end the conversation
            - Keep questions simple and clear (SMS format)
            - Address the patient by name
            - Be empathetic and supportive
            - Max 160 characters if possible
            - DO NOT include closing phrases like "Take care!" or "Best regards" - just ask the question

            Return your answer in the following JSON format:
            {{
                "should_continue": true/false,
                "question": "next question text (or 'CONVERSATION_COMPLETE' if ending)"
            }}
            """

            response_obj = self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful healthcare assistant that conducts post-discharge SMS outreach for care teams. Never repeat the same question. Always check conversation history to avoid repetition."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response_obj.choices[0].message.content)

            # Override AI decision if minimum questions not reached
            if questions_asked < MINIMUM_QUESTIONS:
                if result["should_continue"] and result["question"] != "CONVERSATION_COMPLETE":
                    return result["question"], True
                else:
                    # Force continuation with a default question if AI tries to end early
                    default_questions = [
                        "Were you recently hospitalized or discharged?",
                        "Were any new medications prescribed?",
                        "Are you experiencing any current symptoms?",
                        "Is there anything your care team should know?"
                    ]
                    question_index = min(questions_asked, len(default_questions) - 1)
                    return default_questions[question_index], True
            else:
                if result["should_continue"] and result["question"] != "CONVERSATION_COMPLETE":
                    return result["question"], True
                else:
                    return None, False

        except Exception as e:
            # If AI generation fails, end the conversation
            return None, False
    
    def validate_response(self, question: str, response: str) -> Dict[str, any]:
        """
        Validate if the response is relevant and meaningful to the question.

        Returns:
            Dict with keys:
            - is_valid (bool): Whether the response is valid
            - reason (str): Reason for validation result
            - should_rephrase (bool): Whether to rephrase the question
        """
        try:
            prompt = f"""
            You are validating patient responses to health-related questions.

            Question: "{question}"
            Patient Response: "{response}"

            Evaluate the response and determine:
            1. Is the response meaningful and relevant to the question? (not empty, not just "ok" without context, not gibberish)
            2. If invalid, should the question be rephrased and asked again?

            Return your answer in the following JSON format:
            {{
                "is_valid": true/false,
                "reason": "brief explanation",
                "should_rephrase": true/false
            }}
            """

            response_obj = self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that validates patient responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response_obj.choices[0].message.content)
            return result

        except Exception as e:
            # If AI validation fails, default to accepting the response
            return {
                "is_valid": True,
                "reason": f"AI validation failed: {str(e)}. Defaulting to valid.",
                "should_rephrase": False
            }
    
    def generate_summary(self, conversation_data: Dict) -> Dict[str, str]:
        """
        Generate AI summary of the conversation including:
        - Overall summary
        - Patient responses summary
        - Sentiment analysis
        - Key insights
        """
        try:
            # Build conversation context
            qa_pairs = conversation_data.get("qa_pairs", [])
            patient_context = conversation_data.get("patient_context", "")

            conversation_text = "\n".join([
                f"Q: {pair['question']}\nA: {pair['response']}"
                for pair in qa_pairs
            ])

            prompt = f"""
            You are analyzing a conversation between a healthcare system and a patient via SMS.

            Patient Context: {patient_context}

            Conversation:
            {conversation_text}

            Please analyze this conversation and provide:
            1. A comprehensive summary of the conversation
            2. A summary of the patient's responses
            3. Sentiment analysis (how the patient seems to be feeling/responding)
            4. Key insights or concerns that care team members should be aware of

            Return your answer in the following JSON format:
            {{
                "summary_text": "overall summary",
                "patient_responses_summary": "summary of patient responses",
                "sentiment_analysis": "sentiment analysis",
                "key_insights": "key insights for care team"
            }}
            """

            response_obj = self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes patient healthcare conversations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response_obj.choices[0].message.content)
            return result

        except Exception as e:
            # If AI generation fails, return a basic summary
            return {
                "summary_text": f"AI summary generation failed: {str(e)}",
                "patient_responses_summary": "Unable to generate summary",
                "sentiment_analysis": "Unknown",
                "key_insights": "No insights available due to error"
            }
    
    def rephrase_question(self, original_question: str) -> str:
        """
        Rephrase a question when the patient's response was invalid.
        """
        try:
            prompt = f"""
            The patient gave an invalid or unclear response to this health-related question:
            "{original_question}"

            Please rephrase the question in a clearer, more specific way to help the patient understand what information is needed.
            Keep it simple and direct for SMS format.

            Return only the rephrased question, nothing else.
            """

            response_obj = self.client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that rephrases health questions for clarity."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )

            return response_obj.choices[0].message.content.strip()

        except Exception as e:
            # If rephrasing fails, return the original question
            return original_question


# Singleton instance
ai_service = AIService()
