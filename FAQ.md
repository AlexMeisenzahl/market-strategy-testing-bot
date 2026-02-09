# Frequently Asked Questions (FAQ)

Common questions about the Market Strategy Testing Bot.

---

## 🚀 Getting Started

### Q: Do I need API keys to run the bot?
**A:** No! The bot runs with **mock data** by default - no setup required. Just run `python run_bot.py` and it works immediately with fake data for testing.

### Q: Can I use the bot without any APIs?
**A:** Yes! Mock mode generates realistic prediction markets and crypto prices. Perfect for:
- Testing the bot features
- Learning how strategies work
- Developing new features
- Paper trading practice

### Q: How long does setup take?
**A:**
- **Mock mode**: 0 minutes (instant)
- **Live mode**: 10 minutes (get API keys + configure)

### Q: Is this bot safe to use?
**A:** Yes! The bot:
- Runs in **paper trading mode** by default (no real money)
- Uses reputable, free APIs
- Encrypts all credentials (AES-256)
- Stores data locally (no cloud)
- Open source (you can inspect the code)

---

## 🔑 API Keys

### Q: Which API keys do I need?
**A:** For basic functionality:
- **Polymarket** - Prediction market data (optional, works without key)
- **CoinGecko** - Crypto prices (FREE, no key needed)

Optional:
- **Telegram** - Mobile notifications
- **Email** - Email alerts

### Q: Are these APIs safe?
**A:** Yes! All are:
- Reputable services used by thousands of developers
- Have robust security practices
- Support read-only access (bot doesn't need write permissions)
- Free tiers available

### Q: Will I be charged for these APIs?
**A:** No! All services offer generous free tiers:
- CoinGecko: 50 calls/min (free forever)
- Polymarket: Public access (free)
- Telegram: Unlimited messages (free)
- Email: Gmail SMTP (free with Gmail account)

### Q: Can I switch APIs later?
**A:** Yes! Just update credentials in Settings → Data Sources anytime. Changes take effect on next bot restart.

### Q: What if an API goes down?
**A:** The bot automatically falls back to mock data if live APIs fail. You'll see warnings in logs but the bot keeps running.

---

## 🔐 Security

### Q: Where are my API keys stored?
**A:** Locally in `config/credentials.json` (encrypted with AES-256). Keys never leave your machine.

### Q: How secure is the encryption?
**A:** Very secure:
- AES-256 encryption (military-grade)
- Fernet symmetric encryption library
- Encryption key stored in `config/encryption.key`
- Keys masked in UI (****last6chars)

### Q: Can others see my API keys?
**A:** No, if you follow best practices:
- Don't commit `config/` directory to git (already in `.gitignore`)
- Don't share `config/encryption.key`
- Don't screenshot settings page with keys visible

### Q: What if my keys are compromised?
**A:** 
1. Revoke keys immediately at the service provider
2. Delete `config/credentials.json` and `config/encryption.key`
3. Generate new keys
4. Reconfigure in dashboard

---

## 💰 Trading

### Q: Does this bot trade with real money?
**A:** No, by default the bot runs in **paper trading mode** (simulated trading only). You can enable live trading in config, but:
- ⚠️ NOT RECOMMENDED without extensive testing
- ⚠️ Use at your own risk
- ⚠️ Start with small amounts

### Q: How much money do I need?
**A:**
- **Paper trading**: $0 (simulated capital)
- **Live trading**: Start with $100-500 for testing
- **Production**: $1,000+ recommended

### Q: What returns can I expect?
**A:** Based on backtesting (past performance ≠ future results):
- **Conservative** (Arbitrage only): 2-4%/month
- **Balanced** (Multiple strategies): 8-12%/month
- **Aggressive** (All strategies): 15-25%/month

⚠️ These are theoretical - real results will vary!

### Q: What are the risks?
**A:**
- Market risk (prices move against you)
- Execution risk (slippage, fees)
- API risk (downtime, rate limits)
- Technical risk (bugs, connectivity)
- Strategy risk (logic flaws)

**Mitigation**: Start in paper trading mode!

---

## 🤖 Bot Operation

### Q: How often does the bot trade?
**A:** The bot:
- Scans markets every **60 seconds**
- Only trades when opportunities meet criteria
- May go hours without a trade (normal!)

### Q: Can I run the bot 24/7?
**A:** Yes! Designed for continuous operation:
```bash
# Run in background
nohup python run_bot.py &

# Or use screen/tmux
screen -S tradingbot
python run_bot.py
# Ctrl+A, D to detach
```

### Q: How do I stop the bot?
**A:** Press `Ctrl+C` in the terminal. The bot will:
- Stop gracefully
- Close all positions (if configured)
- Save final state
- Log shutdown activity

### Q: Does the bot need internet?
**A:** Yes, for live data. But it will run in mock mode without internet.

---

## 📊 Dashboard

### Q: How do I access the dashboard?
**A:**
```bash
python start_dashboard.py
```
Then open: http://localhost:5000

### Q: Can others access my dashboard?
**A:** Only on your local network by default. To allow external access:
```bash
# Listen on all interfaces (INSECURE on public networks!)
python start_dashboard.py --host 0.0.0.0
```

### Q: Dashboard not loading?
**A:** Try:
1. Check if port 5000 is in use: `lsof -i :5000`
2. Use different port: `PORT=5001 python start_dashboard.py`
3. Clear browser cache
4. Check logs: `tail -f logs/dashboard.log`

---

## 🔍 Troubleshooting

### Q: Bot shows "MOCK DATA" after adding keys
**A:**
1. Verify you clicked **Save** after entering credentials
2. Click **Test Connection** - should show ✅
3. Restart bot: `Ctrl+C` then `python run_bot.py`
4. Check logs for errors: `tail -f logs/bot.log`

### Q: "Connection Failed" error
**A:** Check:
- Internet connection works
- API endpoints are correct
- API keys are valid
- Not hitting rate limits
- Service isn't down (check status pages)

### Q: No opportunities found
**A:** This is normal! Real markets don't always have arbitrage opportunities. Options:
- Wait longer (opportunities come and go)
- Lower `min_margin` threshold in config
- Switch to mock mode to see how bot works
- Check Polymarket.com for available markets

### Q: Bot crashes or freezes
**A:**
1. Check logs: `tail -f logs/bot.log`
2. Check disk space: `df -h`
3. Check memory: `free -h`
4. Restart bot
5. Report issue on GitHub with logs

---

## 🛠️ Configuration

### Q: How do I enable/disable strategies?
**A:** Edit `config.yaml`:
```yaml
strategies:
  enabled:
    - arbitrage         # Enable
    - momentum          # Enable
    # - news            # Disabled (commented out)
    # - statistical_arb # Disabled
```

### Q: How do I adjust strategy parameters?
**A:** Edit strategy-specific settings in `config.yaml`:
```yaml
arbitrage:
  min_margin: 0.02      # Require 2% profit minimum
  max_position: 0.20    # Use 20% of capital max
```

### Q: Can I backtest strategies?
**A:** Yes! Use the backtester:
```bash
python backtester.py --strategy arbitrage --days 30
```

---

## 📈 Performance

### Q: How do I track performance?
**A:** Multiple ways:
1. **Dashboard**: Real-time metrics at http://localhost:5000
2. **Logs**: Detailed trades in `logs/trades.json`
3. **Activity log**: `logs/activity.json`
4. **Analytics**: Dashboard → Analytics tab

### Q: Can I export trade history?
**A:** Yes! The bot logs all trades to:
- `logs/trades.json` - Machine-readable
- `logs/bot.log` - Human-readable
- Dashboard exports (CSV coming soon)

### Q: How accurate is the performance tracking?
**A:** In paper trading mode:
- Simulates slippage and fees
- Uses realistic execution assumptions
- Close to real-world results
- But still an approximation

---

## 🔄 Updates

### Q: How do I update the bot?
**A:**
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Q: Will updates break my configuration?
**A:** No, but:
- Always backup `config/` directory first
- Read CHANGELOG.md before updating
- Test in separate environment if possible

### Q: How do I know if an update is available?
**A:** Check GitHub releases page or:
```bash
git fetch
git status
```

---

## 💬 Support

### Q: Where can I get help?
**A:**
- 📖 **Documentation**: [SETUP.md](SETUP.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/AlexMeisenzahl/market-strategy-testing-bot/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/AlexMeisenzahl/market-strategy-testing-bot/discussions)
- 📧 **Email**: Check repo for contact

### Q: How do I report a bug?
**A:** Open GitHub Issue with:
1. Bug description
2. Steps to reproduce
3. Expected vs actual behavior
4. Logs (sanitize API keys!)
5. Environment (OS, Python version)

### Q: Can I contribute?
**A:** Yes! Contributions welcome:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation
- Share strategies

---

## 🎓 Advanced

### Q: Can I add custom strategies?
**A:** Yes! Create a new strategy class in `strategies/`:
```python
from strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def find_opportunities(self, markets, prices):
        # Your logic here
        pass
```

### Q: Can I use other exchanges?
**A:** Potentially! You'd need to:
1. Create new client in `clients/`
2. Implement same interface
3. Update `run_bot.py` to use it

### Q: Can I run multiple bots?
**A:** Yes, in separate directories:
```bash
# Bot 1 (conservative)
cd bot1/
python run_bot.py

# Bot 2 (aggressive)
cd bot2/
python run_bot.py
```

### Q: How do I optimize strategies?
**A:** Use the optimizer:
```bash
python performance_optimizer.py
```

It will:
- Test parameter combinations
- Find optimal settings
- Generate performance reports

---

## 📱 Mobile Access

### Q: Can I access the dashboard from my phone?
**A:** Yes! If bot is running:
1. Find computer's local IP: `ifconfig` or `ipconfig`
2. On phone, visit: `http://192.168.1.X:5000`
3. Works on same WiFi network

### Q: Can I get mobile notifications?
**A:** Yes! Configure Telegram bot in Settings → Data Sources. You'll receive:
- New opportunities
- Trades executed
- Profit/loss updates
- Error alerts

---

## ⚖️ Legal

### Q: Is automated trading legal?
**A:** Generally yes, but:
- Check your local regulations
- Some jurisdictions restrict prediction markets
- Bot is for educational/research purposes
- Use at your own risk

### Q: Do I need to pay taxes on profits?
**A:** Consult a tax professional! Trading profits are typically taxable.

### Q: What's the license?
**A:** Check `LICENSE` file in repository. Most likely MIT or similar permissive license.

---

## 🎯 Best Practices

### Recommendations:
1. ✅ **Start with mock mode** - Learn before risking real money
2. ✅ **Use paper trading** - Test strategies extensively  
3. ✅ **Start small** - If going live, use minimal capital
4. ✅ **Monitor actively** - Don't set and forget
5. ✅ **Diversify strategies** - Don't rely on one approach
6. ✅ **Set stop losses** - Limit downside risk
7. ✅ **Keep learning** - Markets evolve
8. ✅ **Backup configs** - Save your settings
9. ✅ **Rotate API keys** - Security best practice
10. ✅ **Stay updated** - Pull latest code regularly

### Don'ts:
1. ❌ Don't trade with money you can't afford to lose
2. ❌ Don't ignore risk management settings
3. ❌ Don't use production keys for testing
4. ❌ Don't leave bot unattended long-term
5. ❌ Don't share API keys
6. ❌ Don't commit credentials to git
7. ❌ Don't trust blindly - verify everything
8. ❌ Don't chase losses
9. ❌ Don't over-optimize (overfitting)
10. ❌ Don't skip documentation

---

**Still have questions? Ask on [GitHub Discussions](https://github.com/AlexMeisenzahl/market-strategy-testing-bot/discussions)!**

**Happy Trading! 📈🚀**
