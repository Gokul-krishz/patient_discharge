"""
Persistent Tunnel with Auto-Restart and Keep-Alive
Most reliable solution for keeping tunnel active without expiring
"""
import subprocess
import time
import requests
import threading
import sys
from datetime import datetime

SUBDOMAIN = "gokul-patient-discharge"
TUNNEL_URL = f"https://{SUBDOMAIN}.loca.lt"
PING_INTERVAL = 180  # Ping every 3 minutes
RESTART_DELAY = 5  # Wait 5 seconds before restart

tunnel_process = None
keep_running = True
restart_count = 0

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def ping_tunnel():
    """Ping the tunnel periodically to keep it alive"""
    global keep_running
    consecutive_failures = 0
    
    while keep_running:
        try:
            time.sleep(PING_INTERVAL)
            
            if not keep_running:
                break
                
            # Try to ping the tunnel
            response = requests.get(
                f"{TUNNEL_URL}/api/forms/webhook",
                timeout=10,
                headers={'bypass-tunnel-reminder': 'true'}
            )
            
            if response.status_code in [200, 404, 405]:  # Any response means tunnel is alive
                log(f"✓ Tunnel alive (Status: {response.status_code})")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                log(f"⚠ Tunnel responded with status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            consecutive_failures += 1
            log(f"⚠ Ping failed ({consecutive_failures} consecutive): {str(e)[:50]}")
            
            # If too many failures, the tunnel might be dead
            if consecutive_failures >= 3:
                log("❌ Tunnel appears dead. It will auto-restart...")
                if tunnel_process:
                    tunnel_process.terminate()
                consecutive_failures = 0
                
        except Exception as e:
            log(f"⚠ Ping error: {str(e)[:50]}")

def start_tunnel():
    """Start and monitor the localtunnel"""
    global tunnel_process, keep_running, restart_count
    
    print("=" * 80)
    print("PERSISTENT TUNNEL - AUTO-RESTART WITH KEEP-ALIVE")
    print("=" * 80)
    print(f"Subdomain: {SUBDOMAIN}")
    print(f"Tunnel URL: {TUNNEL_URL}")
    print(f"Webhook URL: {TUNNEL_URL}/api/forms/webhook")
    print(f"Keep-alive: Pinging every {PING_INTERVAL} seconds")
    print("\n✓ Auto-restart enabled")
    print("✓ Keep-alive pings enabled")
    print("✓ Connection monitoring enabled")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)
    
    # Start ping thread
    ping_thread = threading.Thread(target=ping_tunnel, daemon=True)
    ping_thread.start()
    log("✓ Keep-alive monitor started")
    
    while keep_running:
        try:
            restart_count += 1
            log(f"Starting tunnel (Attempt #{restart_count})...")
            
            # Start localtunnel
            tunnel_process = subprocess.Popen(
                f"npx localtunnel --port 8080 --subdomain {SUBDOMAIN}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if it started successfully
            if tunnel_process.poll() is None:
                log(f"✓ Tunnel started successfully!")
                log(f"✓ Your webhook URL: {TUNNEL_URL}/api/forms/webhook")
            else:
                log("⚠ Tunnel failed to start, retrying...")
                time.sleep(RESTART_DELAY)
                continue
            
            # Wait for tunnel to exit (or crash)
            return_code = tunnel_process.wait()
            
            if keep_running:
                log(f"⚠ Tunnel died (exit code: {return_code})")
                log(f"Restarting in {RESTART_DELAY} seconds...")
                time.sleep(RESTART_DELAY)
            
        except KeyboardInterrupt:
            log("Stopping tunnel...")
            keep_running = False
            if tunnel_process:
                tunnel_process.terminate()
            log("✓ Tunnel stopped by user")
            sys.exit(0)
            
        except Exception as e:
            log(f"❌ Error: {str(e)}")
            log(f"Restarting in {RESTART_DELAY} seconds...")
            time.sleep(RESTART_DELAY)

if __name__ == "__main__":
    try:
        start_tunnel()
    except KeyboardInterrupt:
        log("✓ Shutdown complete")
        sys.exit(0)
