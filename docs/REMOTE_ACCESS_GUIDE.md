# Remote Access Guide

## Accessing Your Trading Bot Dashboard from iPhone

This guide covers different methods to securely access your trading bot dashboard from your iPhone, whether you're at home or away.

## Table of Contents

1. [Local Network Access](#local-network-access)
2. [Tailscale Setup (Recommended)](#tailscale-setup-recommended)
3. [ngrok Alternative](#ngrok-alternative)
4. [Security Best Practices](#security-best-practices)
5. [Troubleshooting](#troubleshooting)

---

## Local Network Access

### When to Use
- You're on the same WiFi network as your server
- Simple setup for home use
- No external access needed

### Setup Steps

1. **Find Your Server's IP Address**
   
   On your server (Mac/Linux):
   ```bash
   # Mac
   ipconfig getifaddr en0
   
   # Linux
   hostname -I | awk '{print $1}'
   ```
   
   Example output: `192.168.1.100`

2. **Start the Dashboard**
   ```bash
   python start_dashboard.py
   ```
   
   Note the port (default: 5000)

3. **Access from iPhone**
   - Open Safari on iPhone
   - Navigate to: `http://192.168.1.100:5000`
   - Bookmark for easy access

### Pros & Cons

✅ **Pros:**
- No configuration needed
- Fast and secure (local network only)
- No external dependencies

❌ **Cons:**
- Only works on same WiFi network
- Can't access remotely
- IP may change if using DHCP

---

## Tailscale Setup (Recommended)

### Why Tailscale?

Tailscale creates a secure, encrypted VPN between your devices using WireGuard. It's the **recommended solution** for remote access because:

- ✅ End-to-end encrypted
- ✅ No port forwarding needed
- ✅ Works behind NAT/firewalls
- ✅ Free for personal use (up to 100 devices)
- ✅ Easy setup on Mac and iPhone

### Part 1: Mac Setup

#### 1. Install Tailscale on Mac

```bash
# Using Homebrew
brew install --cask tailscale

# Or download from https://tailscale.com/download/mac
```

#### 2. Sign Up and Login

1. Open Tailscale from Applications
2. Click "Log in to Tailscale"
3. Create account (or use Google/GitHub/Microsoft)
4. Authorize the Mac device

#### 3. Get Your Tailscale IP

```bash
# Check Tailscale status
tailscale status

# Note your Tailscale IP (e.g., 100.x.x.x)
tailscale ip -4
```

Example: `100.101.102.103`

#### 4. Start Dashboard on All Interfaces

Edit your dashboard startup to listen on all interfaces:

```python
# In start_dashboard.py or app.py
app.run(host='0.0.0.0', port=5000)
```

Or start with:
```bash
python start_dashboard.py --host 0.0.0.0
```

### Part 2: iPhone Setup

#### 1. Install Tailscale App

1. Open App Store on iPhone
2. Search for "Tailscale"
3. Install the official Tailscale app
4. Open the app

#### 2. Sign In

1. Tap "Sign in"
2. Use same account as Mac
3. Authorize iPhone device
4. Enable "On-Demand VPN" if desired

#### 3. Connect to VPN

1. Tap the toggle to connect
2. Approve VPN configuration
3. Check that you see your Mac in device list

#### 4. Access Dashboard

1. Open Safari on iPhone
2. Navigate to: `http://100.101.102.103:5000`
   (Use your Mac's Tailscale IP)
3. Add to Home Screen for app experience

### Tailscale Tips

#### Set a Machine Name
Make it easier to remember:
```bash
# On Mac
tailscale up --hostname my-trading-bot
```

Then access via: `http://my-trading-bot:5000`

#### Keep Connected
- Tailscale auto-connects when needed
- Uses minimal battery
- Can run in background

#### Share Access
Share with family/trusted users:
1. Go to Tailscale admin console
2. Invite users to your tailnet
3. Set access controls if needed

---

## ngrok Alternative

### When to Use
- Quick temporary access needed
- Don't want to install Tailscale
- Testing or demos

### Setup

#### 1. Install ngrok

```bash
# Mac
brew install ngrok

# Or download from https://ngrok.com/download
```

#### 2. Sign Up

1. Create free account at https://ngrok.com
2. Get your auth token
3. Configure ngrok:
   ```bash
   ngrok authtoken YOUR_TOKEN
   ```

#### 3. Start Tunnel

```bash
# Start dashboard first
python start_dashboard.py

# In another terminal, start ngrok
ngrok http 5000
```

#### 4. Get Public URL

ngrok will display a URL like:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:5000
```

#### 5. Access from iPhone

1. Open Safari
2. Navigate to the ngrok URL
3. Dashboard will be accessible

### ngrok Limitations

⚠️ **Important Notes:**
- URL changes each time (unless paid plan)
- Session timeout on free tier
- Public URL (anyone with link can access)
- Not suitable for production

---

## Security Best Practices

### General Security

1. **Use HTTPS in Production**
   ```bash
   # Generate SSL certificate
   openssl req -x509 -newkey rsa:4096 -nodes \
     -keyout key.pem -out cert.pem -days 365
   
   # Start with SSL
   python start_dashboard.py --ssl
   ```

2. **Enable Authentication**
   - Implement login system
   - Use strong passwords
   - Consider 2FA for sensitive operations

3. **Firewall Configuration**
   ```bash
   # Mac: Allow only specific port
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /path/to/python
   ```

4. **Regular Updates**
   - Keep dashboard updated
   - Update Tailscale/ngrok
   - Update iOS regularly

### Network Security

#### For Local Network:
- Use WPA3 WiFi encryption
- Change default router password
- Enable router firewall
- Disable UPnP if not needed

#### For Tailscale:
- Enable MFA on Tailscale account
- Use ACLs to restrict access
- Regularly review connected devices
- Revoke access for unused devices

#### For ngrok:
- Don't share URLs publicly
- Stop tunnel when not needed
- Use password protection:
  ```bash
  ngrok http 5000 --auth="username:password"
  ```
- Monitor access logs

### API Security

If exposing APIs:
1. Use API keys
2. Implement rate limiting
3. Validate all inputs
4. Log all access attempts

---

## Troubleshooting

### Can't Connect on Local Network

**Problem:** iPhone can't reach server IP
**Solutions:**
1. Check both devices on same WiFi
2. Disable VPN on iPhone temporarily
3. Check server firewall allows port 5000
4. Try server's hostname instead of IP
5. Restart router if needed

### Tailscale Not Working

**Problem:** Can't access via Tailscale IP
**Solutions:**
1. Check both devices connected to Tailscale
2. Verify dashboard listening on 0.0.0.0
3. Check Tailscale status: `tailscale status`
4. Try pinging Tailscale IP: `ping 100.x.x.x`
5. Restart Tailscale on both devices

### ngrok Connection Issues

**Problem:** ngrok tunnel not accessible
**Solutions:**
1. Check ngrok is still running
2. Verify dashboard is running
3. Try new tunnel: `ngrok http 5000`
4. Check ngrok dashboard for errors
5. Verify auth token configured

### Slow Performance

**Problem:** Dashboard loads slowly on mobile
**Solutions:**
1. Check network speed
2. Use local network if possible
3. Reduce refresh frequency
4. Close other apps
5. Restart phone/server

### SSL Certificate Warnings

**Problem:** Browser shows security warning
**Solutions:**
1. For local/Tailscale: Safe to proceed
2. For production: Use proper SSL certificate
3. Consider Let's Encrypt for free SSL
4. Add exception in browser (local only)

### Connection Drops

**Problem:** Connection keeps disconnecting
**Solutions:**
1. Check phone isn't going to sleep
2. Enable "Keep Alive" in server
3. Check router stability
4. Update Tailscale/ngrok
5. Use WebSocket for persistent connection

---

## Performance Optimization

### For Best Mobile Experience:

1. **Use Tailscale** for secure remote access
2. **Local Network** when at home for speed
3. **Enable Caching** in service worker
4. **Reduce Polling** frequency for mobile
5. **Compress Responses** in Flask

### Server Configuration:

```python
# In app.py
from flask_compress import Compress

app = Flask(__name__)
Compress(app)  # Enable compression

# Optimize for mobile
@app.after_request
def add_mobile_headers(response):
    response.headers['Cache-Control'] = 'public, max-age=300'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
```

---

## Getting Help

### Resources:
- [Tailscale Documentation](https://tailscale.com/kb/)
- [ngrok Documentation](https://ngrok.com/docs)
- [Flask SSL Setup](https://flask.palletsprojects.com/en/latest/deploying/)

### Support:
- Check troubleshooting section first
- Review server logs for errors
- Test from different devices
- Contact support with details

---

**Last Updated:** February 2026  
**Tested On:** macOS Sonoma, iOS 17
