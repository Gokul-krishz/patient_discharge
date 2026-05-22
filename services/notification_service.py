"""
Notification Service
Sends notifications to care team members via email and SMS
"""
from typing import Dict, Any, List
from services.sms_service import SMSService
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import os


class NotificationService:
    """Service for sending notifications to care team members"""
    
    def __init__(self):
        self.sms_service = SMSService()
        # Email configuration (you'll need to add these to .env)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@hospital.com')
    
    def send_summary_to_care_team(
        self,
        care_team_members: List[Dict[str, Any]],
        patient_name: str,
        summary: Dict[str, str],
        form_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send AI-generated summary to all care team members
        
        Args:
            care_team_members: List of care team member dictionaries
            patient_name: Name of the patient
            summary: AI-generated summary with keys: details, action_required, formatted_response
            form_responses: Raw form responses
            
        Returns:
            Dictionary with notification results
        """
        results = {
            'emails_sent': 0,
            'sms_sent': 0,
            'errors': []
        }
        
        # Format the message
        email_body = self._format_email_body(patient_name, summary, form_responses)
        sms_body = self._format_sms_body(patient_name, summary)
        
        for member in care_team_members:
            member_name = member.get('name', 'Unknown')
            print(f"[NOTIFY] Processing member: {member_name} | email={member.get('email')} | phone={member.get('phone_number')}")
            import sys
            sys.stdout.flush()
            
            # Send email
            if member.get('email'):
                if not self.smtp_username or not self.smtp_password:
                    msg = f"Email to {member_name} skipped: SMTP_USERNAME/SMTP_PASSWORD not configured in .env"
                    results['errors'].append(msg)
                    print(f"[NOTIFY] WARNING: {msg}")
                else:
                    try:
                        self._send_email(
                            to_email=member['email'],
                            subject=f"Patient Update: {patient_name} - Post-Discharge Form Response",
                            body=email_body,
                            member_name=member_name
                        )
                        results['emails_sent'] += 1
                        print(f"[NOTIFY] Email sent to {member_name} ({member['email']})")
                    except Exception as e:
                        msg = f"Email to {member_name}: {str(e)}"
                        results['errors'].append(msg)
                        print(f"[NOTIFY] ERROR: {msg}")
            
            # Send SMS to ALL care team members
            if member.get('phone_number'):
                # Normalize phone number to E.164 format
                phone = member['phone_number'].strip()
                if not phone.startswith('+'):
                    phone = '+' + phone
                    print(f"[NOTIFY] Normalized care team phone: {member['phone_number']} -> {phone}")
                try:
                    self.sms_service.send_sms(
                        to_number=phone,
                        message=sms_body
                    )
                    results['sms_sent'] += 1
                    print(f"[NOTIFY] SMS sent to {member_name} ({phone})")
                except Exception as e:
                    msg = f"SMS to {member_name}: {str(e)}"
                    results['errors'].append(msg)
                    print(f"[NOTIFY] ERROR: {msg}")
        
        return results
    
    def _format_email_body(
        self,
        patient_name: str,
        summary: Dict[str, str],
        form_responses: Dict[str, Any]
    ) -> str:
        """Format the email body with HTML"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .section {{ margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #4CAF50; }}
                .section-title {{ font-weight: bold; color: #4CAF50; margin-bottom: 10px; }}
                .responses {{ background-color: #fff; padding: 10px; border: 1px solid #ddd; }}
                .response-item {{ margin-bottom: 10px; }}
                .label {{ font-weight: bold; color: #555; }}
                .alert {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Patient Post-Discharge Form Response</h2>
                <p>Patient: {patient_name}</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <div class="section-title">Details</div>
                    <p>{summary.get('details', 'No details available')}</p>
                </div>
                
                <div class="section">
                    <div class="section-title">Action Required</div>
                    <p>{summary.get('action_required', 'No action required')}</p>
                </div>
                
                {self._get_alert_section(form_responses)}
            </div>
        </body>
        </html>
        """
        return html
    
    def _get_alert_section(self, form_responses: Dict[str, Any]) -> str:
        """Generate alert section if patient needs contact"""
        if form_responses.get('contact_request', '').lower() in ['yes', 'y', 'true']:
            return """
            <div class="alert">
                <strong>⚠️ Action Required:</strong> Patient has requested to be contacted by the care team.
            </div>
            """
        return ""
    
    def _format_sms_body(self, patient_name: str, summary: Dict[str, str]) -> str:
        """Format SMS body (keep it short)"""
        details = summary.get('details', 'No details available')
        # Truncate if too long - take first sentence or 140 chars
        sentences = details.split('.')
        if len(sentences) > 0:
            sms_text = sentences[0] + '.'
            if len(sms_text) > 140:
                sms_text = sms_text[:137] + "..."
        else:
            sms_text = details[:140]
        
        return f"Patient Update: {patient_name}\n{sms_text}"
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        member_name: str
    ):
        """Send email using SMTP"""
        
        print(f"[EMAIL] Preparing email: From={self.from_email}, To={to_email}, Subject={subject}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = self.from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach HTML body
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Send email
        print(f"[EMAIL] Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            print(f"[EMAIL] Logging in as: {self.smtp_username}")
            server.login(self.smtp_username, self.smtp_password)
            print(f"[EMAIL] Sending message...")
            result = server.send_message(msg)
            print(f"[EMAIL] Email sent successfully! SMTP response: {result}")
