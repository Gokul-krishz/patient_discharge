"""
Get current webhook URL
"""
import requests
import time

print("=" * 70)
print("CHECKING LOCALTUNNEL URL")
print("=" * 70)

# Try to get from localtunnel inspect
try:
    response = requests.get("http://127.0.0.1:8080/health", timeout=2)
    if response.status_code == 200:
        print("\nFlask is running on: http://127.0.0.1:8080")
    else:
        print("\nFlask may not be running properly")
except:
    print("\nFlask is NOT running")

print("\n" + "=" * 70)
print("WEBHOOK URL FORMAT")
print("=" * 70)
print("\nYour webhook URL should be:")
print("https://YOUR_TUNNEL_SUBDOMAIN.loca.lt/api/forms/webhook")
print("\nTo find your current tunnel URL:")
print("1. Check the terminal where you ran 'lt --port 8080'")
print("2. Look for a line like: 'your url is: https://xxxxx.loca.lt'")
print("3. Copy that URL and add '/api/forms/webhook' to the end")
print("\n" + "=" * 70)
print("UPDATE GOOGLE APPS SCRIPT")
print("=" * 70)
print("\n1. Go to your Google Form")
print("2. Click the 3 dots menu → Script editor")
print("3. Find the line: const WEBHOOK_URL = '...'")
print("4. Update it to: const WEBHOOK_URL = 'https://YOUR_TUNNEL.loca.lt/api/forms/webhook'")
print("5. Save the script (Ctrl+S)")
print("6. Test by submitting the form")
print("\n" + "=" * 70)
