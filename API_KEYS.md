# API Keys Guide - Market Strategy Testing Bot

Complete guide to obtaining and configuring API keys for all supported services.

---

## 🎯 Quick Reference

| Service | Cost | Signup Time | Difficulty | Purpose |
|---------|------|-------------|------------|---------|
| **CoinGecko** | FREE | 0 min | ⭐ Easy | Crypto prices |
| **Polymarket** | FREE | 2 min | ⭐ Easy | Market data |
| **Telegram** | FREE | 3 min | ⭐⭐ Medium | Notifications |
| **Email SMTP** | FREE | 5 min | ⭐⭐ Medium | Email alerts |

---

## 1. CoinGecko API (FREE - Crypto Prices)

### What It Does
Fetches real-time cryptocurrency prices for BTC, ETH, SOL, XRP and more.

### Free Tier Benefits
- ✅ **No API key required** for basic access
- ✅ 50 calls/minute (plenty for this bot)
- ✅ Real-time price data
- ✅ No credit card needed

### How to Get Started

**Option 1: No API Key (Recommended)**
1. Leave API Key field **blank** in dashboard
2. Use default endpoint: `https://api.coingecko.com/api/v3`
3. Click **Save** - done!

**Option 2: With API Key (Higher Limits)**
1. Visit: https://www.coingecko.com/en/api
2. Click "Get Your Free API Key"
3. Sign up with email
4. Copy API key from dashboard
5. Paste in Settings → Data Sources → Crypto API Key
6. Click **Test Connection** to verify

### Rate Limits
- **Free (no key)**: 50 calls/minute
- **Free (with key)**: Same limits, but tracked per user
- **Pro**: 500 calls/minute ($129/month - not needed)

### Configuration in Dashboard

```
Provider: CoinGecko (Free)
Endpoint: https://api.coingecko.com/api/v3
API Key: [Leave blank or enter key]
```

### Supported Symbols
- BTC (Bitcoin)
- ETH (Ethereum)
- SOL (Solana)
- XRP (Ripple)

---

## 2. Polymarket API (FREE - Prediction Markets)

### What It Does
Fetches real prediction market data including:
- Market questions and categories
- YES/NO prices
- Trading volume (24h)
- Liquidity levels

### Free Tier Benefits
- ✅ **Read-only access** without API key
- ✅ Public endpoints available
- ✅ Real market data
- ✅ Sufficient for bot operations

### How to Get Started

**For Public Access (Recommended)**
1. Use default endpoint: `https://clob.polymarket.com`
2. Leave API Key field **blank**
3. Click **Test Connection** to verify
4. Click **Save** - done!

**For Authenticated Access (Optional)**
1. Visit: https://polymarket.com
2. Create account (if needed)
3. Navigate to API settings in your profile
4. Generate API key
5. Paste key in Settings → Data Sources → Polymarket API Key
6. Click **Test Connection** to verify

### API Documentation
- Official Docs: https://docs.polymarket.com/
- CLOB API: https://docs.polymarket.com/#clob-api
- GraphQL: https://docs.polymarket.com/#graphql-api

### Configuration in Dashboard

```
Endpoint: https://clob.polymarket.com
API Key: [Leave blank for public access]
```

### Rate Limits
- Public: Reasonable rate limiting (exact limits not published)
- Authenticated: Higher limits
- Be respectful: This bot queries once per minute by default

---

## 3. Telegram Bot Token (FREE - Notifications)

### What It Does
Sends real-time trading notifications to your Telegram app:
- New opportunities found
- Trades executed
- Profit/loss updates
- Error alerts

### How to Get It (3 Minutes)

**Step 1: Create Bot**
1. Open Telegram app
2. Search for `@BotFather`
3. Start chat and send: `/newbot`
4. Follow prompts:
   - Choose bot name (e.g., "My Trading Bot")
   - Choose username (e.g., "mytradingbot123_bot")
5. **Copy the token** - looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

**Step 2: Get Your Chat ID**
1. Search for `@userinfobot` in Telegram
2. Start chat
3. It will reply with your user ID (e.g., `123456789`)
4. **Copy this number** - this is your Chat ID

**Step 3: Configure in Dashboard**
1. Go to Settings → Data Sources → Telegram
2. Paste Bot Token
3. Paste Chat ID
4. Click **Save**

**Step 4: Test It**
1. Click **Send Test Message**
2. Check your Telegram app
3. You should receive a test notification!

### Configuration in Dashboard

```
Bot Token: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
Chat ID: 123456789
```

### Troubleshooting

**Not receiving messages?**
- Ensure you started a chat with your bot (send `/start`)
- Verify Chat ID is correct
- Check bot token is valid
- Make sure bot has permission to message you

**Multiple users?**
- Each user needs their own Chat ID
- Share bot username for others to start chat
- Get their Chat ID from @userinfobot
- Configure multiple notification targets (feature coming soon)

---

## 4. Email SMTP (FREE - Email Alerts)

### What It Does
Sends email notifications for important events:
- Daily performance summaries
- Critical alerts (large losses)
- Weekly reports
- System errors

### Gmail Setup (Most Common - 5 Minutes)

**Step 1: Enable 2-Factor Authentication**
1. Go to: https://myaccount.google.com/security
2. Enable "2-Step Verification" if not already on
3. Follow Google's setup wizard

**Step 2: Create App Password**
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it "Trading Bot"
4. Click **Generate**
5. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

**Step 3: Configure in Dashboard**
```
SMTP Server: smtp.gmail.com
Port: 587
Email Address: your.email@gmail.com
App Password: abcd efgh ijkl mnop
```

**Step 4: Test**
1. Click **Send Test Email**
2. Check your inbox (and spam folder)
3. You should receive a test email!

### Other Email Providers

**Outlook/Hotmail**
```
SMTP Server: smtp.office365.com
Port: 587
Username: your.email@outlook.com
Password: Your Outlook password
```

**Yahoo Mail**
```
SMTP Server: smtp.mail.yahoo.com
Port: 587
Username: your.email@yahoo.com
Password: App-specific password (generate at account security)
```

**Custom SMTP**
- Check your email provider's documentation
- Most use port 587 (TLS) or 465 (SSL)
- Some require app-specific passwords

### Configuration in Dashboard

```
SMTP Server: smtp.gmail.com
Port: 587
Email: your.email@gmail.com
App Password: [16-character password]
```

### Troubleshooting

**"Authentication failed" error?**
- Ensure you're using an **App Password**, not your regular password
- Verify 2-Factor Authentication is enabled
- Check SMTP server and port are correct

**Not receiving emails?**
- Check spam/junk folder
- Verify email address is correct
- Test SMTP settings with an email client first
- Some providers block automated emails - use Gmail

---

## Security Best Practices

### ✅ Do This
- ✅ Use **read-only API keys** when possible
- ✅ **Rotate keys** every 90 days
- ✅ Use **app passwords** (not regular passwords)
- ✅ Keep **encryption key** secure (`config/encryption.key`)
- ✅ Add `config/` to `.gitignore`
- ✅ Never commit credentials to git

### ❌ Don't Do This
- ❌ Share API keys publicly
- ❌ Use same key across multiple services
- ❌ Store keys in plaintext files
- ❌ Commit `credentials.json` to git
- ❌ Use production keys for testing

### Key Storage
All credentials are **encrypted** using AES-256 encryption:
- Keys stored in: `config/credentials.json` (encrypted)
- Encryption key: `config/encryption.key` (keep secure!)
- Keys masked in UI: `****abc123`

### If Keys Are Compromised
1. **Revoke immediately** at the service provider
2. **Generate new keys**
3. **Delete** `config/credentials.json`
4. **Delete** `config/encryption.key`
5. **Reconfigure** in dashboard with new keys

---

## Cost Comparison

| Service | Free Tier | Paid Tier | Bot Usage |
|---------|-----------|-----------|-----------|
| **CoinGecko** | 50 calls/min | $129/mo (500 calls/min) | ~1 call/min ✅ |
| **Polymarket** | Public access | N/A | ~1 call/min ✅ |
| **Telegram** | Unlimited | Free forever | ~10 msgs/day ✅ |
| **Gmail SMTP** | Unlimited | Free with Gmail | ~5 emails/day ✅ |

**Bottom line**: All services are **FREE** for this bot's usage! 💰

---

## Testing Your Setup

### 1. Test Connections
In Dashboard → Settings → Data Sources:
- Click **Test Connection** for each service
- All should show ✅ **Connected**

### 2. Verify Data Mode
- Check indicator shows: 🟢 **LIVE DATA**
- If showing 🔴 **MOCK DATA**, check API keys

### 3. Run Bot
```bash
python run_bot.py
```

Look for:
```
✅ Successfully connected to Polymarket API
📊 Using LIVE Polymarket data

✅ Successfully connected to CoinGecko API (BTC: $45,234.56)
💰 Using LIVE crypto price data
```

### 4. Monitor Dashboard
- Open: http://localhost:5000
- Navigate to **Opportunities**
- Should see real markets with live data
- Check **Settings → Data Sources** shows 🟢 **LIVE DATA**

---

## FAQ

**Q: Do I need ALL API keys?**
A: No! Start with just CoinGecko (optional) and Polymarket. Add notifications later.

**Q: Are these APIs safe to use?**
A: Yes! All are reputable services used by thousands of developers.

**Q: Will I be charged?**
A: No! Free tiers are sufficient for this bot.

**Q: Can I switch APIs later?**
A: Yes! Just update credentials in dashboard anytime.

**Q: What if an API goes down?**
A: Bot automatically falls back to mock data if API fails.

**Q: How secure are my keys?**
A: Encrypted with AES-256 and stored locally (not in database or cloud).

---

## Getting Help

- 📖 **Setup Guide**: [SETUP.md](SETUP.md)
- 🐛 **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- ❓ **FAQ**: [FAQ.md](FAQ.md)
- 💬 **Issues**: [GitHub Issues](https://github.com/AlexMeisenzahl/market-strategy-testing-bot/issues)

---

**Happy Trading! 🔑🚀**
