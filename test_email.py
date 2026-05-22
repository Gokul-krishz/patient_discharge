"""
Test Email Configuration
Quick test to verify SMTP settings
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

def test_email():
    print("="*70)
    print("TESTING EMAIL CONFIGURATION")
    print("="*70)
    
    # Check if email is configured
    if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        print("\n❌ Email not configured in .env file!")
        print("\nRequired settings:")
        print("  SMTP_SERVER=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USERNAME=your_email@gmail.com")
        print("  SMTP_PASSWORD=your_app_password")
        print("  FROM_EMAIL=your_email@gmail.com")
        return
    
    print(f"\n📧 SMTP Server: {Config.SMTP_SERVER}")
    print(f"📧 SMTP Port: {Config.SMTP_PORT}")
    print(f"📧 Username: {Config.SMTP_USERNAME}")
    print(f"📧 From Email: {Config.FROM_EMAIL}")
    print(f"📧 Password: {'*' * len(Config.SMTP_PASSWORD)}")
    
    # Test email
    test_recipient = Config.SMTP_USERNAME  # Send to yourself
    
    print(f"\n📤 Sending test email to: {test_recipient}")
    print("⏳ Please wait...")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.FROM_EMAIL
        msg['To'] = test_recipient
        msg['Subject'] = "Test Email - Patient Discharge System"
        
        body = """
        <html>
        <body>
            <h2>✅ Email Configuration Test Successful!</h2>
            <p>Your SMTP settings are working correctly.</p>
            <p>Care team members will receive notifications via email.</p>
        </body>
        </html>
        """
        
        html_part = MIMEText(body, 'html')
        msg.attach(html_part)
        
        # Send with timeout
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
        
        print("\n✅ SUCCESS! Email sent successfully!")
        print(f"📬 Check your inbox: {test_recipient}")
        print("\n✓ Email notifications will work for care team members")
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ AUTHENTICATION FAILED!")
        print("\nPossible issues:")
        print("  1. Wrong username or password")
        print("  2. Using regular password instead of App Password")
        print("  3. 2-Factor Authentication not enabled")
        print("\n📖 For Gmail:")
        print("  1. Enable 2FA: https://myaccount.google.com/security")
        print("  2. Generate App Password: https://myaccount.google.com/apppasswords")
        print("  3. Use the 16-character app password in .env")
        
    except smtplib.SMTPConnectError:
        print("\n❌ CONNECTION FAILED!")
        print("\nPossible issues:")
        print("  1. Wrong SMTP server or port")
        print("  2. Firewall blocking connection")
        print("  3. Network issue")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Check your .env file settings")
        print("  2. Verify SMTP server and port")
        print("  3. Try using port 465 with SSL")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    test_email()
