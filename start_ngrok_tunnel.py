"""
Start ngrok tunnel - Most reliable option for persistent tunneling
Requires ngrok to be installed and configured
"""
import subprocess
import sys
import time
import re
import requests
from datetime import datetime

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        result = subprocess.run(
            ["ngrok", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def get_ngrok_url():
    """Get the public URL from ngrok API"""
    try:
        time.sleep(2)  # Wait for ngrok to start
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    return tunnel.get('public_url')
    except Exception as e:
        log(f"Could not get ngrok URL from API: {e}")
    return None

def start_ngrok():
    """Start ngrok tunnel"""
    print("=" * 80)
    print("NGROK PERSISTENT TUNNEL")
    print("=" * 80)
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        print("\n❌ ngrok is not installed!")
        print("\nTo install ngrok:")
        print("1. Visit: https://ngrok.com/download")
        print("2. Or install via Homebrew: brew install ngrok/ngrok/ngrok")
        print("3. Sign up at https://ngrok.com/ (free)")
        print("4. Get your auth token from dashboard")
        print("5. Run: ngrok config add-authtoken YOUR_TOKEN")
        print("\nThen run this script again.")
        sys.exit(1)
    
    log("✓ ngrok is installed")
    log("Starting ngrok tunnel on port 8080...")
    print("\n" + "=" * 80)
    
    try:
        # Start ngrok
        process = subprocess.Popen(
            ["ngrok", "http", "8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get the public URL
        public_url = get_ngrok_url()
        
        if public_url:
            print("\n" + "=" * 80)
            print("✓ TUNNEL ACTIVE!")
            print("=" * 80)
            print(f"\nPublic URL: {public_url}")
            print(f"Webhook URL: {public_url}/api/forms/webhook")
            print(f"\nngrok Dashboard: http://localhost:4040")
            print("\n✓ This tunnel will stay active as long as this script runs")
            print("✓ View all requests in the ngrok dashboard")
            print("\nPress Ctrl+C to stop")
            print("=" * 80)
            
            # Save URL to file for easy access
            with open('ngrok_url.txt', 'w') as f:
                f.write(f"Public URL: {public_url}\n")
                f.write(f"Webhook URL: {public_url}/api/forms/webhook\n")
            log("✓ URL saved to ngrok_url.txt")
        else:
            print("\n⚠ Could not retrieve ngrok URL automatically")
            print("Check the ngrok dashboard at: http://localhost:4040")
        
        # Keep running
        process.wait()
        
    except KeyboardInterrupt:
        log("\nStopping ngrok tunnel...")
        process.terminate()
        log("✓ Tunnel stopped")
        sys.exit(0)
    except Exception as e:
        log(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_ngrok()
