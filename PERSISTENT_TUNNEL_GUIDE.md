# Persistent Tunnel Guide - Keep Your Webhook Active 24/7

## 🎯 Problem
Temporary tunnels expire, disconnect, or change URLs causing webhook failures.

## ✅ Solutions (Ranked by Reliability)

---

## 🥇 Option 1: Enhanced Persistent Tunnel (RECOMMENDED)

**Best for:** Development and testing with auto-recovery

### Features:
- ✅ Auto-restart if tunnel dies
- ✅ Keep-alive pings every 3 minutes
- ✅ Connection monitoring
- ✅ Fixed subdomain (URL never changes)
- ✅ Detailed logging with timestamps

### Run:
```bash
python persistent_tunnel.py
```

### Your Fixed URL:
```
https://gokul-patient-discharge.loca.lt/api/forms/webhook
```

### What It Does:
1. Starts tunnel with fixed subdomain
2. Pings tunnel every 3 minutes to keep it alive
3. Monitors connection health
4. Auto-restarts if tunnel dies
5. Logs all activity with timestamps

### Output Example:
```
[2026-05-21 11:30:00] ✓ Keep-alive monitor started
[2026-05-21 11:30:03] ✓ Tunnel started successfully!
[2026-05-21 11:30:03] ✓ Your webhook URL: https://gokul-patient-discharge.loca.lt/api/forms/webhook
[2026-05-21 11:33:00] ✓ Tunnel alive (Status: 404)
[2026-05-21 11:36:00] ✓ Tunnel alive (Status: 404)
```

---

## 🥈 Option 2: ngrok (MOST RELIABLE)

**Best for:** Production-like stability

### Why ngrok?
- ✅ More stable than localtunnel
- ✅ Better performance
- ✅ Web dashboard to inspect requests
- ✅ Free tier is generous
- ✅ Rarely disconnects

### Setup (One-time):

1. **Install ngrok:**
   ```bash
   # macOS
   brew install ngrok/ngrok/ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. **Sign up (FREE):**
   - Visit: https://ngrok.com/
   - Create free account

3. **Get auth token:**
   - Go to dashboard: https://dashboard.ngrok.com/
   - Copy your auth token

4. **Configure ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

### Run:
```bash
python start_ngrok_tunnel.py
```

### Features:
- ✅ Auto-extracts and displays webhook URL
- ✅ Saves URL to `ngrok_url.txt`
- ✅ Web dashboard at `http://localhost:4040`
- ✅ Inspect all webhook requests in real-time

### Output:
```
================================================================================
✓ TUNNEL ACTIVE!
================================================================================

Public URL: https://abc123.ngrok.io
Webhook URL: https://abc123.ngrok.io/api/forms/webhook

ngrok Dashboard: http://localhost:4040

✓ This tunnel will stay active as long as this script runs
✓ View all requests in the ngrok dashboard
```

---

## 🥉 Option 3: Simple Auto-Restart

**Best for:** Quick testing

### Run:
```bash
python keep_tunnel_alive.py
```

- Auto-restarts if tunnel dies
- Fixed subdomain
- No keep-alive pings

---

## 📊 Comparison

| Feature | persistent_tunnel.py | ngrok | keep_tunnel_alive.py |
|---------|---------------------|-------|---------------------|
| Auto-restart | ✅ | ✅ | ✅ |
| Keep-alive pings | ✅ | ❌ (not needed) | ❌ |
| Fixed URL | ✅ | ⚠️ (changes on restart) | ✅ |
| Stability | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Web dashboard | ❌ | ✅ | ❌ |
| Setup required | ❌ | ✅ (one-time) | ❌ |
| Free | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start

### For Immediate Use:
```bash
python persistent_tunnel.py
```

### For Best Reliability:
```bash
# One-time setup
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken YOUR_TOKEN

# Then run
python start_ngrok_tunnel.py
```

---

## 🔧 Troubleshooting

### Tunnel keeps disconnecting?
- Use `persistent_tunnel.py` (has auto-restart)
- Or switch to ngrok for better stability

### URL keeps changing?
- Use fixed subdomain scripts (persistent_tunnel.py or keep_tunnel_alive.py)
- Or use ngrok with a paid plan for static domain

### Can't install ngrok?
- Use `persistent_tunnel.py` - works without any installation
- Just needs Python and npm (already installed)

### Webhook not receiving data?
1. Check tunnel is running: `curl https://your-url.loca.lt/api/forms/webhook`
2. Check backend is running: `curl http://localhost:8080/api/forms/webhook`
3. Check Google Apps Script has correct URL
4. Check ngrok dashboard (if using ngrok) for incoming requests

---

## 💡 Pro Tips

### 1. Run in Background (macOS/Linux):
```bash
# Using screen
screen -S tunnel
python persistent_tunnel.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r tunnel
```

### 2. Run on Startup (macOS):
Create `~/Library/LaunchAgents/com.patient.tunnel.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.patient.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/persistent_tunnel.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

### 3. Monitor Tunnel Health:
```bash
# Check if tunnel is responding
curl -I https://gokul-patient-discharge.loca.lt/api/forms/webhook

# Should return HTTP 404 or 405 (means tunnel is alive)
```

---

## 🎯 Recommendation

**For Development:** Use `persistent_tunnel.py`
- No setup required
- Auto-restart + keep-alive
- Fixed URL

**For Production-like Testing:** Use `ngrok`
- Most reliable
- Best performance
- Web dashboard

**For Quick Tests:** Use `keep_tunnel_alive.py`
- Simple and fast
- Auto-restart only

---

## 📝 Update Google Apps Script

Once you have your stable URL, update your Google Apps Script:

```javascript
// Use your persistent tunnel URL
var WEBHOOK_URL = "https://gokul-patient-discharge.loca.lt/api/forms/webhook";

// Or if using ngrok
var WEBHOOK_URL = "https://abc123.ngrok.io/api/forms/webhook";
```

**This URL will now stay active and won't expire!** 🎉
