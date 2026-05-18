"""
Start localtunnel with a fixed subdomain for more stability
"""
import subprocess
import sys

# Use a fixed subdomain so URL doesn't change
SUBDOMAIN = "gokul-patient-discharge"

print("=" * 70)
print("STARTING LOCALTUNNEL WITH FIXED SUBDOMAIN")
print("=" * 70)
print(f"\nSubdomain: {SUBDOMAIN}")
print(f"Your URL will be: https://{SUBDOMAIN}.loca.lt")
print(f"Webhook URL: https://{SUBDOMAIN}.loca.lt/api/forms/webhook")
print("\nThis URL will stay the same even if you restart!")
print("=" * 70)
print("\nStarting tunnel...")

try:
    # Start localtunnel with fixed subdomain
    # Use shell=True for Windows to find npx
    subprocess.run(
        f"npx localtunnel --port 8080 --subdomain {SUBDOMAIN}",
        shell=True
    )
except KeyboardInterrupt:
    print("\n\nTunnel stopped by user")
    sys.exit(0)
