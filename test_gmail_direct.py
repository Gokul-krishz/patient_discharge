"""
Direct Gmail SMTP Test
Tests Gmail connection with your credentials
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(override=True)

# Read credentials from .env
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USERNAME)
TO_EMAIL = SMTP_USERNAME  # Send to yourself

print("="*70)
print("DIRECT GMAIL SMTP TEST")
print("="*70)
print(f"\nServer: {SMTP_SERVER}")
print(f"Username: {SMTP_USERNAME}")
print(f"Password: {'*' * len(SMTP_PASSWORD)}")
print(f"\nSending test email to: {TO_EMAIL}")

# Test 1: Try SSL (port 465)
print("\n" + "="*70)
print("TEST 1: SSL (Port 465)")
print("="*70)
try:
    msg = MIMEMultipart('alternative')
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = "Test Email - SSL Port 465"
    
    body = MIMEText("<h2>✅ SSL Test Successful!</h2><p>Port 465 is working.</p>", 'html')
    msg.attach(body)
    
    print("Connecting to smtp.gmail.com:465 (SSL)...")
    with smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=30) as server:
        print("✓ Connected")
        print("Logging in...")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        print("✓ Authenticated")
        print("Sending message...")
        server.send_message(msg)
        print("✓ Message sent")
    
    print("\n✅ SUCCESS! Email sent via SSL (port 465)")
    print(f"📬 Check your inbox: {TO_EMAIL}")
    
except Exception as e:
    print(f"\n❌ SSL FAILED: {str(e)}")
    
    # Test 2: Try TLS (port 587)
    print("\n" + "="*70)
    print("TEST 2: TLS (Port 587)")
    print("="*70)
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = FROM_EMAIL
        msg['To'] = TO_EMAIL
        msg['Subject'] = "Test Email - TLS Port 587"
        
        body = MIMEText("<h2>✅ TLS Test Successful!</h2><p>Port 587 is working.</p>", 'html')
        msg.attach(body)
        
        print("Connecting to smtp.gmail.com:587 (TLS)...")
        with smtplib.SMTP(SMTP_SERVER, 587, timeout=30) as server:
            print("✓ Connected")
            print("Starting TLS...")
            server.starttls()
            print("✓ TLS started")
            print("Logging in...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("✓ Authenticated")
            print("Sending message...")
            server.send_message(msg)
            print("✓ Message sent")
        
        print("\n✅ SUCCESS! Email sent via TLS (port 587)")
        print(f"📬 Check your inbox: {TO_EMAIL}")
        
    except Exception as e2:
        print(f"\n❌ TLS ALSO FAILED: {str(e2)}")
        print("\n" + "="*70)
        print("BOTH METHODS FAILED")
        print("="*70)
        print("\nPossible issues:")
        print("1. App password is incorrect")
        print("2. 2-Factor Authentication not enabled")
        print("3. 'Less secure app access' needs to be enabled")
        print("4. Account has security restrictions")
        print("\nSteps to fix:")
        print("1. Go to: https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification")
        print("3. Go to: https://myaccount.google.com/apppasswords")
        print("4. Generate new app password for 'Mail'")
        print("5. Use that password (16 chars, no spaces)")

print("\n" + "="*70)
