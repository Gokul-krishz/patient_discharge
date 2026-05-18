"""
Start localtunnel to expose Flask app
Run this in a separate terminal: python start_tunnel.py
"""
import subprocess
import sys

print("Starting localtunnel on port 8080...")
print("Keep this terminal open to maintain the tunnel")
print("="*60)

try:
    # Run localtunnel using subprocess
    process = subprocess.Popen(
        ["npx", "localtunnel", "--port", "8080"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in process.stdout:
        print(line, end='')
        sys.stdout.flush()
        
except KeyboardInterrupt:
    print("\n\nTunnel stopped by user")
    process.terminate()
except Exception as e:
    print(f"\nError: {e}")
    print("\nAlternatively, run this command manually in a new terminal:")
    print("npx localtunnel --port 8080")
