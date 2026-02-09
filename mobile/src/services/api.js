/**
 * API Service
 * 
 * Handles all API communication with the trading bot backend.
 * 
 * Configuration:
 * - For production, set API_BASE_URL environment variable
 * - For development, uses localhost:8000
 */

// Configure API base URL
// You can override this by setting window.API_BASE_URL before loading this script
const API_BASE_URL = window.API_BASE_URL || (
  window.location.origin.includes('localhost') 
    ? 'http://localhost:8000' 
    : window.location.origin
);

class APIService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api`;
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || 'Request failed');
    }

    return response.json();
  }

  // Auth endpoints
  async login(username, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    this.setToken(response.access_token);
    return response;
  }

  async logout() {
    await this.request('/auth/logout', { method: 'POST' });
    this.clearToken();
  }

  // Market endpoints
  async getMarkets(page = 1, perPage = 50) {
    return this.request(`/markets?page=${page}&per_page=${perPage}`);
  }

  async getMarket(marketId) {
    return this.request(`/markets/${marketId}`);
  }

  async searchMarkets(query) {
    return this.request(`/markets/search?q=${encodeURIComponent(query)}`);
  }

  // Trading endpoints
  async executeTrade(tradeData) {
    return this.request('/trade', {
      method: 'POST',
      body: JSON.stringify(tradeData),
    });
  }

  async cancelTrade(tradeId) {
    return this.request(`/trade/${tradeId}`, { method: 'DELETE' });
  }

  // Position endpoints
  async getPositions() {
    return this.request('/positions');
  }

  async getPosition(positionId) {
    return this.request(`/positions/${positionId}`);
  }

  async closePosition(positionId) {
    return this.request(`/positions/${positionId}/close`, {
      method: 'PUT',
    });
  }

  // Strategy endpoints
  async getStrategies() {
    return this.request('/strategies');
  }

  async enableStrategy(strategyName) {
    return this.request(`/strategies/${strategyName}/enable`, {
      method: 'PUT',
    });
  }

  async disableStrategy(strategyName) {
    return this.request(`/strategies/${strategyName}/disable`, {
      method: 'PUT',
    });
  }

  async getStrategyConfig(strategyName) {
    return this.request(`/strategies/${strategyName}/config`);
  }

  async updateStrategyConfig(strategyName, config) {
    return this.request(`/strategies/${strategyName}/config`, {
      method: 'PUT',
      body: JSON.stringify({ config }),
    });
  }

  // Health check
  async healthCheck() {
    return fetch(`${API_BASE_URL}/api/health`).then(r => r.json());
  }
}

export default new APIService();
