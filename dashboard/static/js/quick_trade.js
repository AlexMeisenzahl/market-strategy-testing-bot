/**
 * Quick Trade Widget
 * 
 * Interactive trading interface for:
 * - One-click trading
 * - Position sizing
 * - Order preview
 * - Real-time execution feedback
 */

class QuickTradeWidget {
    constructor() {
        this.currentSymbol = 'BTC';
        this.currentPrice = 0;
        this.orderType = 'market';
        this.side = 'buy';
        this.quantity = 0;
        this.realtimeClient = null;
    }
    
    /**
     * Initialize the quick trade widget
     */
    init() {
        console.log('[QuickTradeWidget] Initializing...');
        
        // Get realtime client if available
        if (window.realtimeClient) {
            this.realtimeClient = window.realtimeClient;
            this.setupRealtimeUpdates();
        }
        
        // Create widget UI
        this.createWidget();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('[QuickTradeWidget] Initialized');
    }
    
    /**
     * Create widget HTML
     */
    createWidget() {
        const container = document.getElementById('quick-trade-widget');
        if (!container) {
            console.warn('[QuickTradeWidget] Container not found');
            return;
        }
        
        container.innerHTML = `
            <div class="pro-card">
                <div class="pro-card-header">
                    <h3 class="pro-card-title">Quick Trade</h3>
                    <select id="qt-symbol" class="pro-select" style="width: auto; padding: 6px 12px; font-size: 13px;">
                        <option value="BTC">BTC/USD</option>
                        <option value="ETH">ETH/USD</option>
                        <option value="SOL">SOL/USD</option>
                        <option value="XRP">XRP/USD</option>
                    </select>
                </div>
                <div class="pro-card-body">
                    <!-- Current Price Display -->
                    <div style="margin-bottom: 20px; text-align: center;">
                        <div class="pro-text-muted" style="font-size: 12px; margin-bottom: 4px;">Current Price</div>
                        <div id="qt-price" class="price-display" style="font-size: 24px;">$--,---</div>
                        <div id="qt-change" class="change-indicator" style="margin-top: 8px;">
                            <i class="fas fa-arrow-up"></i>
                            <span>---%</span>
                        </div>
                    </div>
                    
                    <!-- Order Type Selector -->
                    <div style="margin-bottom: 16px;">
                        <label class="pro-text-muted" style="font-size: 12px; display: block; margin-bottom: 8px;">Order Type</label>
                        <div style="display: flex; gap: 8px;">
                            <button class="pro-btn-secondary qt-order-type active" data-type="market" style="flex: 1;">
                                Market
                            </button>
                            <button class="pro-btn-secondary qt-order-type" data-type="limit" style="flex: 1;">
                                Limit
                            </button>
                        </div>
                    </div>
                    
                    <!-- Quantity Input -->
                    <div style="margin-bottom: 16px;">
                        <label class="pro-text-muted" style="font-size: 12px; display: block; margin-bottom: 8px;">Amount (USD)</label>
                        <input type="number" id="qt-amount" class="pro-input" placeholder="0.00" min="0" step="10" value="100">
                        <div style="display: flex; gap: 8px; margin-top: 8px;">
                            <button class="pro-btn-secondary qt-preset" data-amount="10" style="flex: 1; padding: 6px; font-size: 12px;">$10</button>
                            <button class="pro-btn-secondary qt-preset" data-amount="50" style="flex: 1; padding: 6px; font-size: 12px;">$50</button>
                            <button class="pro-btn-secondary qt-preset" data-amount="100" style="flex: 1; padding: 6px; font-size: 12px;">$100</button>
                            <button class="pro-btn-secondary qt-preset" data-amount="500" style="flex: 1; padding: 6px; font-size: 12px;">$500</button>
                        </div>
                    </div>
                    
                    <!-- Limit Price (if limit order) -->
                    <div id="qt-limit-price-container" style="margin-bottom: 16px; display: none;">
                        <label class="pro-text-muted" style="font-size: 12px; display: block; margin-bottom: 8px;">Limit Price</label>
                        <input type="number" id="qt-limit-price" class="pro-input" placeholder="0.00" min="0" step="0.01">
                    </div>
                    
                    <!-- Order Summary -->
                    <div style="background: var(--secondary-bg); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span class="pro-text-muted" style="font-size: 12px;">Estimated Quantity</span>
                            <span id="qt-estimated-qty" style="font-size: 12px; font-weight: 600;">0.0000</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span class="pro-text-muted" style="font-size: 12px;">Commission (0.1%)</span>
                            <span id="qt-commission" style="font-size: 12px;">$0.00</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; border-top: 1px solid var(--border-color); padding-top: 8px;">
                            <span class="pro-text-muted" style="font-size: 12px; font-weight: 600;">Total Cost</span>
                            <span id="qt-total" style="font-size: 14px; font-weight: 700;">$0.00</span>
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <button id="qt-buy-btn" class="pro-btn pro-btn-buy" style="padding: 12px; font-weight: 600;">
                            <i class="fas fa-arrow-up"></i>
                            Buy
                        </button>
                        <button id="qt-sell-btn" class="pro-btn pro-btn-sell" style="padding: 12px; font-weight: 600;">
                            <i class="fas fa-arrow-down"></i>
                            Sell
                        </button>
                    </div>
                    
                    <!-- Order Confirmation Message -->
                    <div id="qt-message" style="margin-top: 16px; padding: 12px; border-radius: var(--radius-sm); display: none;">
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Symbol selector
        const symbolSelect = document.getElementById('qt-symbol');
        if (symbolSelect) {
            symbolSelect.addEventListener('change', (e) => {
                this.currentSymbol = e.target.value;
                this.updatePrice();
            });
        }
        
        // Order type buttons
        document.querySelectorAll('.qt-order-type').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.qt-order-type').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.orderType = btn.dataset.type;
                this.toggleLimitPrice();
            });
        });
        
        // Preset amount buttons
        document.querySelectorAll('.qt-preset').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const amount = parseFloat(btn.dataset.amount);
                document.getElementById('qt-amount').value = amount;
                this.updateOrderSummary();
            });
        });
        
        // Amount input
        const amountInput = document.getElementById('qt-amount');
        if (amountInput) {
            amountInput.addEventListener('input', () => this.updateOrderSummary());
        }
        
        // Limit price input
        const limitPriceInput = document.getElementById('qt-limit-price');
        if (limitPriceInput) {
            limitPriceInput.addEventListener('input', () => this.updateOrderSummary());
        }
        
        // Buy button
        const buyBtn = document.getElementById('qt-buy-btn');
        if (buyBtn) {
            buyBtn.addEventListener('click', () => this.executeTrade('buy'));
        }
        
        // Sell button
        const sellBtn = document.getElementById('qt-sell-btn');
        if (sellBtn) {
            sellBtn.addEventListener('click', () => this.executeTrade('sell'));
        }
        
        // Initial price update
        this.updatePrice();
    }
    
    /**
     * Toggle limit price input visibility
     */
    toggleLimitPrice() {
        const container = document.getElementById('qt-limit-price-container');
        if (container) {
            container.style.display = this.orderType === 'limit' ? 'block' : 'none';
        }
    }
    
    /**
     * Update current price display
     */
    async updatePrice() {
        try {
            // In a real implementation, this would fetch from API
            // For demo, generate realistic prices
            const prices = {
                'BTC': 67000 + (Math.random() - 0.5) * 1000,
                'ETH': 3800 + (Math.random() - 0.5) * 100,
                'SOL': 150 + (Math.random() - 0.5) * 10,
                'XRP': 0.65 + (Math.random() - 0.5) * 0.05
            };
            
            this.currentPrice = prices[this.currentSymbol] || 0;
            
            // Update UI
            const priceEl = document.getElementById('qt-price');
            if (priceEl) {
                priceEl.textContent = `$${this.currentPrice.toFixed(2)}`;
            }
            
            // Update change indicator (random for demo)
            const change = (Math.random() - 0.5) * 5;
            const changeEl = document.getElementById('qt-change');
            if (changeEl) {
                const isPositive = change >= 0;
                changeEl.className = `change-indicator ${isPositive ? 'positive' : 'negative'}`;
                changeEl.innerHTML = `
                    <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
                    <span>${isPositive ? '+' : ''}${change.toFixed(2)}%</span>
                `;
            }
            
            // Update order summary
            this.updateOrderSummary();
            
        } catch (error) {
            console.error('[QuickTradeWidget] Error updating price:', error);
        }
    }
    
    /**
     * Update order summary
     */
    updateOrderSummary() {
        const amount = parseFloat(document.getElementById('qt-amount')?.value || 0);
        const price = this.orderType === 'limit' 
            ? parseFloat(document.getElementById('qt-limit-price')?.value || this.currentPrice)
            : this.currentPrice;
            
        if (!price || price <= 0) return;
        
        const quantity = amount / price;
        const commission = amount * 0.001; // 0.1%
        const total = amount + commission;
        
        // Update UI
        const qtyEl = document.getElementById('qt-estimated-qty');
        if (qtyEl) {
            qtyEl.textContent = quantity.toFixed(6);
        }
        
        const commissionEl = document.getElementById('qt-commission');
        if (commissionEl) {
            commissionEl.textContent = `$${commission.toFixed(2)}`;
        }
        
        const totalEl = document.getElementById('qt-total');
        if (totalEl) {
            totalEl.textContent = `$${total.toFixed(2)}`;
        }
    }
    
    /**
     * Execute trade
     */
    async executeTrade(side) {
        const amount = parseFloat(document.getElementById('qt-amount')?.value || 0);
        
        if (amount <= 0) {
            this.showMessage('Please enter a valid amount', 'error');
            return;
        }
        
        if (!this.currentPrice || this.currentPrice <= 0) {
            this.showMessage('Invalid price data', 'error');
            return;
        }
        
        const quantity = amount / this.currentPrice;
        
        try {
            // Show loading state
            this.showMessage('Placing order...', 'info');
            
            // In a real implementation, this would call the API
            // For demo, simulate order placement
            await this.simulateOrderPlacement(side, quantity, amount);
            
            // Show success
            this.showMessage(
                `${side.toUpperCase()} order executed: ${quantity.toFixed(6)} ${this.currentSymbol} @ $${this.currentPrice.toFixed(2)}`,
                'success'
            );
            
            // Trigger trade event for other components
            window.dispatchEvent(new CustomEvent('trade_executed', {
                detail: {
                    symbol: this.currentSymbol,
                    side: side,
                    quantity: quantity,
                    price: this.currentPrice,
                    amount: amount
                }
            }));
            
            // Reset form
            setTimeout(() => {
                document.getElementById('qt-amount').value = '100';
                this.updateOrderSummary();
            }, 2000);
            
        } catch (error) {
            console.error('[QuickTradeWidget] Error executing trade:', error);
            this.showMessage('Trade execution failed: ' + error.message, 'error');
        }
    }
    
    /**
     * Simulate order placement (for paper trading)
     */
    async simulateOrderPlacement(side, quantity, amount) {
        return new Promise((resolve) => {
            // Simulate network delay
            setTimeout(() => {
                console.log(`[QuickTradeWidget] Simulated ${side} order:`, {
                    symbol: this.currentSymbol,
                    quantity: quantity,
                    price: this.currentPrice,
                    amount: amount
                });
                resolve();
            }, 500);
        });
    }
    
    /**
     * Show message to user
     */
    showMessage(text, type = 'info') {
        const messageEl = document.getElementById('qt-message');
        if (!messageEl) return;
        
        const colors = {
            info: { bg: 'rgba(33, 150, 243, 0.1)', text: '#2196f3', icon: 'fa-info-circle' },
            success: { bg: 'rgba(38, 166, 154, 0.1)', text: '#26a69a', icon: 'fa-check-circle' },
            error: { bg: 'rgba(239, 83, 80, 0.1)', text: '#ef5350', icon: 'fa-exclamation-circle' },
            warning: { bg: 'rgba(255, 152, 0, 0.1)', text: '#ff9800', icon: 'fa-exclamation-triangle' }
        };
        
        const color = colors[type] || colors.info;
        
        messageEl.style.display = 'flex';
        messageEl.style.alignItems = 'center';
        messageEl.style.gap = '8px';
        messageEl.style.background = color.bg;
        messageEl.style.color = color.text;
        messageEl.innerHTML = `
            <i class="fas ${color.icon}"></i>
            <span style="flex: 1; font-size: 13px;">${text}</span>
        `;
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 5000);
        }
    }
    
    /**
     * Setup real-time updates
     */
    setupRealtimeUpdates() {
        if (!this.realtimeClient) return;
        
        // Listen for price updates
        this.realtimeClient.on('price_update', (data) => {
            if (data.symbol === this.currentSymbol) {
                this.currentPrice = data.price;
                this.updatePrice();
            }
        });
        
        console.log('[QuickTradeWidget] Real-time updates enabled');
    }
    
    /**
     * Start periodic price updates
     */
    startPriceUpdates() {
        // Update price every 2 seconds (for demo)
        this.priceUpdateInterval = setInterval(() => {
            this.updatePrice();
        }, 2000);
    }
    
    /**
     * Stop price updates
     */
    stopPriceUpdates() {
        if (this.priceUpdateInterval) {
            clearInterval(this.priceUpdateInterval);
        }
    }
}

// Global instance
const quickTradeWidget = new QuickTradeWidget();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        quickTradeWidget.init();
        quickTradeWidget.startPriceUpdates();
    });
} else {
    quickTradeWidget.init();
    quickTradeWidget.startPriceUpdates();
}

// Export for global access
window.quickTradeWidget = quickTradeWidget;
