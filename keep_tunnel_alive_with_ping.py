"""
Keep localtunnel alive with periodic pings
"""
import subprocess
import time
import requests
import threading
import sys

SUBDOMAIN = "gokul-patient-discharge"
TUNNEL_URL = f"https://{SUBDOMAIN}.loca.lt"
PING_INTERVAL = 300  # Ping every 5 minutes (300 seconds)

tunnel_process = None
keep_running = True

def ping_tunnel():
    """Ping the tunnel periodically to keep it alive"""
    while keep_running:
        try:
            time.sleep(PING_INTERVAL)
            response = requests.get(f"{TUNNEL_URL}/api/forms/webhook", timeout=10)
            print(f"[PING] Tunnel alive - Status: {response.status_code}")
        except Exception as e:
            print(f"[PING] Warning: {e}")

def start_tunnel():
    """Start the localtunnel"""
    global tunnel_process
    print("=" * 70)
    print("STARTING LOCALTUNNEL WITH KEEP-ALIVE")
    print("=" * 70)
    print(f"Subdomain: {SUBDOMAIN}")
    print(f"Webhook URL: {TUNNEL_URL}/api/forms/webhook")
    print(f"Keep-alive: Pinging every {PING_INTERVAL} seconds")
    print("\nThis will stay alive as long as this script runs!")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    try:
        # Start ping thread
        ping_thread = threading.Thread(target=ping_tunnel, daemon=True)
        ping_thread.start()
        
        # Start localtunnel
        print("\nStarting tunnel...")
        tunnel_process = subprocess.Popen(
            f"npx localtunnel --port 8080 --subdomain {SUBDOMAIN}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor tunnel output
        for line in tunnel_process.stdout:
            print(line.strip())
            
    except KeyboardInterrupt:
        print("\n\nStopping tunnel...")
        global keep_running
        keep_running = False
        if tunnel_process:
            tunnel_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    start_tunnel()
