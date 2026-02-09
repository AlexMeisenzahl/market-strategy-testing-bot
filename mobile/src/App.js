/**
 * Trading Bot Mobile App
 * 
 * Main application entry point.
 */

import api from './services/api.js';
import ws from './services/websocket.js';

class TradingBotApp {
  constructor() {
    this.currentView = 'login';
    this.isAuthenticated = false;
    this.data = {
      markets: [],
      positions: [],
      strategies: [],
      botStatus: null
    };
  }

  async init() {
    // Check if already authenticated
    const token = localStorage.getItem('auth_token');
    if (token) {
      try {
        await this.loadBotStatus();
        this.isAuthenticated = true;
        this.showDashboard();
        this.connectWebSocket();
      } catch (error) {
        console.error('Auth check failed:', error);
        this.showLogin();
      }
    } else {
      this.showLogin();
    }

    // Hide loading screen
    document.getElementById('loading').style.display = 'none';
  }

  showLogin() {
    this.currentView = 'login';
    document.getElementById('root').innerHTML = `
      <div class="login-container">
        <div class="login-card card-elevated">
          <h1>🤖 Trading Bot</h1>
          <form id="login-form">
            <div class="form-group">
              <input
                type="text"
                id="username"
                placeholder="Username"
                required
                autocomplete="username"
              />
            </div>
            <div class="form-group">
              <input
                type="password"
                id="password"
                placeholder="Password"
                required
                autocomplete="current-password"
              />
            </div>
            <button type="submit" class="button">Login</button>
            <div id="login-error" class="error-message"></div>
          </form>
        </div>
      </div>
    `;

    document.getElementById('login-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleLogin();
    });
  }

  async handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('login-error');

    try {
      await api.login(username, password);
      this.isAuthenticated = true;
      await this.loadBotStatus();
      this.showDashboard();
      this.connectWebSocket();
    } catch (error) {
      errorEl.textContent = error.message || 'Login failed';
      errorEl.style.display = 'block';
    }
  }

  showDashboard() {
    this.currentView = 'dashboard';
    document.getElementById('root').innerHTML = `
      <div class="app-container">
        <div class="header">
          <h2>Trading Bot</h2>
          <button id="logout-btn" class="button">Logout</button>
        </div>
        
        <div class="content">
          <div class="card">
            <h3>Bot Status</h3>
            <div id="bot-status">
              <div class="loading"><div class="spinner"></div></div>
            </div>
          </div>

          <div class="card">
            <h3>Strategies</h3>
            <div id="strategies-list">
              <div class="loading"><div class="spinner"></div></div>
            </div>
          </div>

          <div class="card">
            <h3>Positions</h3>
            <div id="positions-list">
              <div class="loading"><div class="spinner"></div></div>
            </div>
          </div>
        </div>

        <nav class="nav-bar">
          <a href="#dashboard" class="nav-item active">
            <span>📊</span>
            <span>Dashboard</span>
          </a>
          <a href="#markets" class="nav-item">
            <span>📈</span>
            <span>Markets</span>
          </a>
          <a href="#positions" class="nav-item">
            <span>💼</span>
            <span>Positions</span>
          </a>
          <a href="#settings" class="nav-item">
            <span>⚙️</span>
            <span>Settings</span>
          </a>
        </nav>
      </div>
    `;

    document.getElementById('logout-btn').addEventListener('click', () => this.handleLogout());

    this.loadDashboardData();
  }

  async loadBotStatus() {
    // Implementation would load actual bot status
    // For now, just test API connectivity
    await api.healthCheck();
  }

  async loadDashboardData() {
    try {
      // Load strategies
      const strategies = await api.getStrategies();
      this.renderStrategies(strategies.strategies);

      // Load positions
      const positions = await api.getPositions();
      this.renderPositions(positions.positions);

      // Mock bot status
      this.renderBotStatus({
        status: 'running',
        balance: 10000,
        daily_pnl: 125.50,
        total_pnl: 1250.00,
        active_strategies: 3,
        active_positions: 2
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  }

  renderBotStatus(status) {
    const statusEl = document.getElementById('bot-status');
    const pnlClass = status.daily_pnl >= 0 ? 'status-positive' : 'status-negative';
    
    statusEl.innerHTML = `
      <div class="status-grid">
        <div class="status-item">
          <span class="label">Status</span>
          <span class="value badge badge-success">${status.status}</span>
        </div>
        <div class="status-item">
          <span class="label">Daily P&L</span>
          <span class="value ${pnlClass}">$${status.daily_pnl.toFixed(2)}</span>
        </div>
        <div class="status-item">
          <span class="label">Total P&L</span>
          <span class="value ${pnlClass}">$${status.total_pnl.toFixed(2)}</span>
        </div>
        <div class="status-item">
          <span class="label">Active Strategies</span>
          <span class="value">${status.active_strategies}</span>
        </div>
      </div>
    `;
  }

  renderStrategies(strategies) {
    const listEl = document.getElementById('strategies-list');
    
    if (!strategies || strategies.length === 0) {
      listEl.innerHTML = '<p>No strategies available</p>';
      return;
    }

    listEl.innerHTML = strategies.map(strategy => `
      <div class="list-item">
        <div>
          <strong>${strategy.display_name}</strong>
          <br>
          <small>${strategy.description}</small>
        </div>
        <span class="badge badge-${strategy.status === 'enabled' ? 'success' : 'danger'}">
          ${strategy.status}
        </span>
      </div>
    `).join('');
  }

  renderPositions(positions) {
    const listEl = document.getElementById('positions-list');
    
    if (!positions || positions.length === 0) {
      listEl.innerHTML = '<p>No active positions</p>';
      return;
    }

    listEl.innerHTML = positions.map(position => `
      <div class="list-item">
        <div>
          <strong>${position.market_name}</strong>
          <br>
          <small>Size: $${position.size.toFixed(2)} | Entry: ${position.entry_price.toFixed(4)}</small>
        </div>
        <div>
          <span class="${position.pnl >= 0 ? 'status-positive' : 'status-negative'}">
            ${position.pnl >= 0 ? '+' : ''}$${position.pnl.toFixed(2)}
          </span>
        </div>
      </div>
    `).join('');
  }

  connectWebSocket() {
    ws.connect();

    ws.on('trade', (data) => {
      console.log('Trade update:', data);
      this.loadDashboardData();
    });

    ws.on('position', (data) => {
      console.log('Position update:', data);
      this.loadDashboardData();
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  async handleLogout() {
    try {
      await api.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    ws.disconnect();
    this.isAuthenticated = false;
    this.showLogin();
  }
}

// Initialize app
const app = new TradingBotApp();
app.init();

// Export for debugging
window.app = app;
