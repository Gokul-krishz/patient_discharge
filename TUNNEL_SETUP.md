# Tunnel Setup Guide - Stop Disconnections!

## Problem
Localtunnel keeps disconnecting, causing webhook failures.

## Solutions (Choose One)

---

## ✅ Option 1: Use Fixed Subdomain (Easiest)

This keeps the same URL even if you restart!

### Run:
```bash
python start_stable_tunnel.py
```

### Your Fixed URL:
```
https://patient-discharge-gokul.loca.lt/api/forms/webhook
```

**Update Google Apps Script once with this URL and you're done!**

---

## ✅ Option 2: Auto-Restart Tunnel (Best for Development)

Automatically restarts if tunnel dies.

### Run:
```bash
python keep_tunnel_alive.py
```

This will:
- Use fixed subdomain
- Auto-restart if connection drops
- Keep running until you stop it

---

## ✅ Option 3: Use ngrok (Most Reliable - Recommended for Production)

ngrok is more stable than localtunnel.

### Setup:

1. **Install ngrok:**
   ```bash
   npm install -g ngrok
   ```

2. **Sign up (free):** https://ngrok.com/

3. **Get auth token** from dashboard

4. **Configure:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

5. **Start ngrok:**
   ```bash
   ngrok http 8080
   ```

6. **Copy the URL** (e.g., `https://abc123.ngrok.io`)

7. **Update Google Apps Script:**
   ```javascript
   var WEBHOOK_URL = "https://abc123.ngrok.io/api/forms/webhook";
   ```

### Advantages:
- ✅ More stable connection
- ✅ Better performance
- ✅ Web dashboard to see requests
- ✅ Free tier is generous

---

## ✅ Option 4: Deploy to Production (Best Long-Term)

For production, deploy to:
- **Heroku** (free tier)
- **Railway** (free tier)
- **Render** (free tier)
- **AWS/Azure/GCP** (requires setup)

Then you get a permanent URL that never changes!

---

## Quick Fix for Now

**Use the fixed subdomain approach:**

1. Stop current localtunnel (Ctrl+C)

2. Run:
   ```bash
   python start_stable_tunnel.py
   ```

3. Update Google Apps Script to:
   ```javascript
   var WEBHOOK_URL = "https://patient-discharge-gokul.loca.lt/api/forms/webhook";
   ```

4. This URL will stay the same even if you restart!

---

## Why Localtunnel Disconnects

1. **Free tier limitations** - Disconnects after inactivity
2. **No subdomain** - Gets random URL each time
3. **Network instability** - Connection drops
4. **Rate limiting** - Too many requests

Using a **fixed subdomain** solves most of these issues!
