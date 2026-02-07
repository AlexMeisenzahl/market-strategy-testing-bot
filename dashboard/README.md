# 📊 Market Strategy Testing Bot - Web Dashboard

A professional-grade web dashboard for monitoring and controlling your trading bot with real-time analytics, comprehensive customization, and beautiful UI/UX.

![Dashboard Preview](https://via.placeholder.com/1200x600/0f172a/ffffff?text=Professional+Trading+Dashboard)

## ✨ Features

### 📈 Overview Dashboard
- **Real-time Performance Metrics**: Total P&L, Win Rate, Active Trades, and more
- **Interactive Charts**:
  - Cumulative P&L line chart with multiple time ranges (1W, 1M, 3M, ALL)
  - Daily P&L bar chart with moving average
  - Strategy performance comparison
- **Recent Activity Feed**: Latest trades and opportunities
- **Beautiful Cards**: Animated, hover effects, gradient backgrounds

### 💼 Trading History
- **Comprehensive Trade Table**: View all your trades with detailed information
- **Advanced Filters**:
  - Date range (Today, This Week, This Month, Custom)
  - Symbol filter
  - Strategy filter
  - Outcome filter (Win/Loss)
- **Pagination**: Handle large datasets efficiently
- **Export Functionality**: Download trades as CSV
- **Summary Statistics**: Quick overview of filtered results

### 🔔 Notifications Settings
- **Email Notifications**:
  - SMTP configuration (Gmail, Outlook, etc.)
  - Test email functionality
  - Enable/disable per notification type
- **Desktop Notifications**:
  - Native OS notifications
  - Test functionality
- **Telegram Integration**:
  - Bot token and chat ID configuration
  - Test message sending
  - Real-time trading alerts
- **Granular Controls**: Enable/disable specific event types

### 🎛️ Bot Control
- **Start/Stop/Restart**: Full control over bot operation
- **Status Monitoring**:
  - Real-time status indicator
  - Uptime tracking
  - Mode display (Paper/Live)
- **System Info**: Connected symbols, active strategies

### 🎨 Professional Design
- **Dark Theme**: Easy on the eyes, professional look
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Smooth Animations**: Subtle transitions and hover effects
- **Modern UI Components**: Tailwind CSS with custom styling
- **Chart.js Integration**: Interactive, animated charts
- **Font Awesome Icons**: Beautiful, consistent iconography

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or newer
- pip (Python package installer)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Install Dashboard Dependencies**

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- Flask-CORS (API security)
- PyYAML (configuration management)
- And all other required packages

2. **Configure Your Bot**

Make sure you have a `config.yaml` file in the root directory. If not, copy from the example:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to configure your notification preferences and trading strategies.

### Running the Dashboard

1. **Start the Dashboard Server**

```bash
cd market-strategy-testing-bot
python dashboard/app.py
```

Or if using Python 3:

```bash
python3 dashboard/app.py
```

2. **Access the Dashboard**

Open your web browser and navigate to:

```
http://localhost:5000
```

You should see:
```
============================================================
🚀 Market Strategy Testing Bot - Web Dashboard
============================================================

📊 Dashboard URL: http://localhost:5000
📁 Config file: /path/to/config.yaml
📂 Logs directory: /path/to/logs

Press Ctrl+C to stop the server
```

3. **Start Exploring!**

- **Overview**: View your performance metrics and charts
- **Trades**: Browse your trading history
- **Settings**: Configure notifications and preferences
- **Control**: Start/stop the bot

## 📁 Project Structure

```
market-strategy-testing-bot/
├── dashboard/
│   ├── app.py                      # Main Flask application
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_parser.py          # Parse trading logs
│   │   ├── analytics.py            # Calculate metrics
│   │   ├── chart_data.py           # Prepare chart data
│   │   └── config_manager.py       # Manage config.yaml
│   ├── static/
│   │   ├── css/
│   │   │   └── custom.css          # Custom styles
│   │   └── js/
│   │       └── dashboard.js        # Frontend JavaScript
│   └── templates/
│       └── index.html              # Main dashboard template
├── logs/                            # Trading logs (auto-created)
├── config.yaml                      # Your configuration
└── config.example.yaml              # Example configuration
```

## 🔧 Configuration

### Dashboard Settings

The dashboard reads from `config.yaml`. Here's what you can configure:

#### Notifications

```yaml
notifications:
  email:
    enabled: false                  # Enable/disable email notifications
    from_email: "your@email.com"
    to_email: "alerts@email.com"
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    password: "your_app_password"
  
  desktop:
    enabled: true                   # Enable/disable desktop notifications
  
  telegram:
    enabled: false                  # Enable/disable Telegram
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
```

#### Trading Strategies

```yaml
strategies:
  rsi_scalp:
    enabled: true
    period: 14
    oversold: 30
    overbought: 70
  
  macd_trend:
    enabled: true
    fast_period: 12
    slow_period: 26
    signal_period: 9
```

### Gmail SMTP Setup

To use email notifications with Gmail:

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the generated password
3. Use the app password in your `config.yaml`

### Telegram Setup

To use Telegram notifications:

1. Create a bot with [@BotFather](https://t.me/botfather)
2. Copy the bot token
3. Get your chat ID:
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Copy the chat ID from the response
4. Add both to your `config.yaml`

## 🎯 API Endpoints

The dashboard provides a REST API that you can use programmatically:

### Overview
- `GET /api/overview` - Get dashboard summary statistics

### Trades
- `GET /api/trades?start_date=&end_date=&symbol=&strategy=` - Get filtered trades
- `POST /api/export/trades` - Export trades to CSV

### Charts
- `GET /api/charts/cumulative-pnl?range=1M` - Cumulative P&L data
- `GET /api/charts/daily-pnl` - Daily P&L data
- `GET /api/charts/strategy-performance` - Strategy comparison

### Settings
- `GET /api/settings` - Get all settings
- `PUT /api/settings/notifications` - Update notification settings
- `PUT /api/settings/strategies` - Update strategy settings

### Notifications
- `POST /api/notifications/test` - Send test notification
- `GET /api/notifications/history` - Get notification history

### Bot Control
- `GET /api/bot/status` - Get bot status
- `POST /api/bot/start` - Start the bot
- `POST /api/bot/stop` - Stop the bot
- `POST /api/bot/restart` - Restart the bot

## 🔒 Security

- **Paper Trading Only**: The dashboard is designed for paper trading
- **Local Access**: Dashboard runs on localhost by default
- **Config Backups**: Automatic backups before any config changes
- **No External Data**: All data stays on your machine

## 🐛 Troubleshooting

### Dashboard won't start

**Error: "Config file not found"**
```bash
# Copy the example config
cp config.example.yaml config.yaml
```

**Error: "Port 5000 already in use"**
```bash
# Kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or change the port in dashboard/app.py
app.run(host='0.0.0.0', port=5001)  # Use port 5001 instead
```

### Charts not loading

- Check browser console for errors (F12)
- Ensure Chart.js CDN is accessible
- Verify API endpoints are returning data

### Notifications not working

- **Email**: Verify SMTP credentials and app password
- **Desktop**: Ensure `plyer` is installed: `pip install plyer`
- **Telegram**: Check bot token and chat ID
- Use the "Test" buttons to diagnose issues

## 🎨 Customization

### Changing the Theme

Edit `dashboard/templates/index.html`:

```javascript
// Change accent colors
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'profit': '#10b981',  // Change profit color
                'loss': '#ef4444',    // Change loss color
                // ... more colors
            }
        }
    }
}
```

### Adding Custom Charts

1. Create a new chart data method in `dashboard/services/chart_data.py`
2. Add an API endpoint in `dashboard/app.py`
3. Add chart rendering in `dashboard/static/js/dashboard.js`
4. Add HTML canvas in `dashboard/templates/index.html`

## 🚧 Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Advanced analytics (Sharpe ratio, drawdown analysis)
- [ ] Custom alert creation
- [ ] Trade journal with notes
- [ ] Strategy backtesting interface
- [ ] Multi-bot management
- [ ] Mobile app companion
- [ ] Voice notifications
- [ ] AI-powered insights

## 📝 Contributing

Feel free to submit issues, feature requests, or pull requests!

## 📄 License

This project is part of the Market Strategy Testing Bot.

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Charts powered by [Chart.js](https://www.chartjs.org/)
- Icons from [Font Awesome](https://fontawesome.com/)

---

**⚠️ Disclaimer**: This dashboard is for educational and paper trading purposes only. Always test thoroughly before considering real money trading.
