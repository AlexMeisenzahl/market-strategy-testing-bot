/**
 * CryptoTicker - Real-time cryptocurrency price ticker
 * Fetches and displays current prices with 24h changes
 */
class CryptoTicker {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.staleThreshold = 120000; // 2 minutes
        this.symbols = ['BTC', 'ETH', 'SOL', 'XRP'];
        this.lastUpdate = null;
        this.updateTimer = null;
        this.isUpdating = false;
    }

    /**
     * Initialize the ticker
     */
    init() {
        this.updatePrices();
        this.startAutoUpdate();
        this.setupStaleDataCheck();
    }

    /**
     * Fetch current prices from API
     */
    async fetchPrices() {
        try {
            const response = await fetch('/api/crypto/current_prices');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching crypto prices:', error);
            this.showError('Failed to fetch prices');
            return null;
        }
    }

    /**
     * Update ticker display with latest prices
     */
    async updatePrices() {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        const data = await this.fetchPrices();
        
        if (data && data.prices) {
            this.lastUpdate = Date.now();
            this.renderPrices(data.prices);
            this.updateTimestamp();
            this.hideError();
        }
        
        this.isUpdating = false;
    }

    /**
     * Render prices in the ticker
     */
    renderPrices(prices) {
        this.symbols.forEach(symbol => {
            const priceData = prices[symbol];
            if (!priceData) return;

            const priceElement = document.getElementById(`ticker-price-${symbol}`);
            const changeElement = document.getElementById(`ticker-change-${symbol}`);

            if (priceElement) {
                const formattedPrice = this.formatPrice(priceData.price);
                priceElement.textContent = `$${formattedPrice}`;
                
                // Add flash animation
                priceElement.classList.add('price-flash');
                setTimeout(() => priceElement.classList.remove('price-flash'), 300);
            }

            if (changeElement) {
                const change = priceData.change_24h || 0;
                const isPositive = change >= 0;
                
                changeElement.textContent = `${isPositive ? '+' : ''}${change.toFixed(2)}%`;
                changeElement.className = `ticker-change ${isPositive ? 'text-profit' : 'text-loss'}`;
            }
        });
    }

    /**
     * Format price based on value
     */
    formatPrice(price) {
        if (price >= 1000) {
            return price.toLocaleString('en-US', { 
                minimumFractionDigits: 0, 
                maximumFractionDigits: 0 
            });
        } else if (price >= 1) {
            return price.toLocaleString('en-US', { 
                minimumFractionDigits: 2, 
                maximumFractionDigits: 2 
            });
        } else {
            return price.toLocaleString('en-US', { 
                minimumFractionDigits: 4, 
                maximumFractionDigits: 4 
            });
        }
    }

    /**
     * Update the last updated timestamp
     */
    updateTimestamp() {
        const timestampElement = document.getElementById('ticker-timestamp');
        if (timestampElement && this.lastUpdate) {
            const date = new Date(this.lastUpdate);
            const timeString = date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            });
            timestampElement.textContent = `Updated: ${timeString}`;
        }
    }

    /**
     * Check if data is stale and show warning
     */
    setupStaleDataCheck() {
        setInterval(() => {
            const warningIcon = document.getElementById('ticker-stale-warning');
            if (warningIcon && this.lastUpdate) {
                const isStale = (Date.now() - this.lastUpdate) > this.staleThreshold;
                warningIcon.style.display = isStale ? 'inline-flex' : 'none';
            }
        }, 10000); // Check every 10 seconds
    }

    /**
     * Start automatic price updates
     */
    startAutoUpdate() {
        this.updateTimer = setInterval(() => {
            this.updatePrices();
        }, this.refreshInterval);
    }

    /**
     * Stop automatic updates
     */
    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorElement = document.getElementById('ticker-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    /**
     * Hide error message
     */
    hideError() {
        const errorElement = document.getElementById('ticker-error');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    /**
     * Destroy the ticker and cleanup
     */
    destroy() {
        this.stopAutoUpdate();
    }
}

// Initialize ticker when DOM is ready
let cryptoTicker;
document.addEventListener('DOMContentLoaded', () => {
    cryptoTicker = new CryptoTicker();
    cryptoTicker.init();
});
