"""
Keep localtunnel alive - auto-restart if it dies
"""
import subprocess
import time
import sys

SUBDOMAIN = "gokul-patient-discharge"

print("=" * 70)
print("AUTO-RESTARTING LOCALTUNNEL")
print("=" * 70)
print(f"Subdomain: {SUBDOMAIN}")
print(f"Webhook URL: https://{SUBDOMAIN}.loca.lt/api/forms/webhook")
print("\nThis will automatically restart if the tunnel dies!")
print("Press Ctrl+C to stop")
print("=" * 70)

restart_count = 0
process = None

while True:
    try:
        restart_count += 1
        print(f"\n[Attempt {restart_count}] Starting tunnel...")
        
        # Start localtunnel with shell=True for Windows
        process = subprocess.Popen(
            f"npx localtunnel --port 8080 --subdomain {SUBDOMAIN}",
            shell=True
        )
        
        # Wait for it to finish (or crash)
        return_code = process.wait()
        
        print(f"\n[WARNING] Tunnel died with code {return_code}! Restarting in 5 seconds...")
        time.sleep(5)
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        if process:
            process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}. Restarting in 5 seconds...")
        time.sleep(5)
