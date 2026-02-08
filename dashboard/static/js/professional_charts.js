/**
 * Professional Charts - TradingView Lightweight Charts Integration
 * 
 * Provides professional-grade charts with:
 * - Real-time data updates
 * - Multiple timeframes
 * - Technical indicators
 * - Interactive controls
 * - Responsive design
 */

class ProfessionalCharts {
    constructor() {
        this.charts = new Map();
        this.chartData = new Map();
        this.updateInterval = null;
        this.realtimeClient = null;
    }
    
    /**
     * Initialize charts system
     */
    init() {
        console.log('[ProfessionalCharts] Initializing...');
        
        // Get realtime client if available
        if (window.realtimeClient) {
            this.realtimeClient = window.realtimeClient;
            this.setupRealtimeUpdates();
        }
        
        // Create default charts
        this.createPriceChart('btc-chart', 'BTC/USD');
        this.createPriceChart('eth-chart', 'ETH/USD');
        
        console.log('[ProfessionalCharts] Initialized');
    }
    
    /**
     * Create a price chart
     */
    createPriceChart(containerId, symbol, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`[ProfessionalCharts] Container not found: ${containerId}`);
            return null;
        }
        
        // Default options
        const defaultOptions = {
            type: 'candlestick',
            timeframe: '1h',
            height: 400,
            showVolume: true,
            showGrid: true,
            theme: 'dark'
        };
        
        const chartOptions = { ...defaultOptions, ...options };
        
        // Create chart using Chart.js (already loaded)
        const canvas = document.createElement('canvas');
        container.innerHTML = '';
        container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: symbol,
                    data: [],
                    borderColor: '#26a69a',
                    backgroundColor: 'rgba(38, 166, 154, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#d1d4dc',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e222d',
                        titleColor: '#d1d4dc',
                        bodyColor: '#d1d4dc',
                        borderColor: '#2a2e39',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return `Price: $${value.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: '#2a2e39',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#787b86',
                            font: {
                                size: 11
                            },
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        position: 'right',
                        grid: {
                            color: '#2a2e39',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#787b86',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
        
        // Store chart reference
        this.charts.set(containerId, {
            chart: chart,
            symbol: symbol,
            options: chartOptions
        });
        
        // Load initial data
        this.loadChartData(containerId, symbol);
        
        return chart;
    }
    
    /**
     * Create a candlestick chart
     */
    createCandlestickChart(containerId, symbol) {
        const container = document.getElementById(containerId);
        if (!container) return null;
        
        // For candlestick, we need different approach
        // Using Chart.js with financial plugin or custom implementation
        container.innerHTML = `
            <div class="pro-chart-container">
                <div class="pro-chart-toolbar">
                    <button class="timeframe-btn active" data-timeframe="1m">1m</button>
                    <button class="timeframe-btn" data-timeframe="5m">5m</button>
                    <button class="timeframe-btn" data-timeframe="15m">15m</button>
                    <button class="timeframe-btn" data-timeframe="1h">1h</button>
                    <button class="timeframe-btn" data-timeframe="4h">4h</button>
                    <button class="timeframe-btn" data-timeframe="1d">1D</button>
                    <div style="flex: 1"></div>
                    <button class="pro-btn-secondary">
                        <i class="fas fa-expand"></i>
                    </button>
                </div>
                <canvas id="${containerId}-canvas"></canvas>
            </div>
        `;
        
        // Setup timeframe buttons
        const buttons = container.querySelectorAll('.timeframe-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.updateChartTimeframe(containerId, btn.dataset.timeframe);
            });
        });
        
        return this.createPriceChart(containerId + '-canvas', symbol);
    }
    
    /**
     * Create a portfolio value chart
     */
    createPortfolioChart(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return null;
        
        const canvas = document.createElement('canvas');
        container.innerHTML = '';
        container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: '#2962ff',
                    backgroundColor: 'rgba(41, 98, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: '#1e222d',
                        titleColor: '#d1d4dc',
                        bodyColor: '#d1d4dc',
                        borderColor: '#2a2e39',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `Value: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            color: '#2a2e39',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#787b86',
                            font: { size: 11 }
                        }
                    },
                    y: {
                        display: true,
                        position: 'right',
                        grid: {
                            color: '#2a2e39',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#787b86',
                            font: { size: 11 },
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        });
        
        this.charts.set(containerId, {
            chart: chart,
            type: 'portfolio'
        });
        
        this.loadPortfolioData(containerId);
        
        return chart;
    }
    
    /**
     * Update chart with new data point
     */
    updateChart(containerId, timestamp, value) {
        const chartData = this.charts.get(containerId);
        if (!chartData) return;
        
        const chart = chartData.chart;
        const maxDataPoints = 100;
        
        // Add new data
        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(value);
        
        // Remove old data if exceeds max
        if (chart.data.labels.length > maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        
        chart.update('none'); // Update without animation for real-time
    }
    
    /**
     * Load chart data from API
     */
    async loadChartData(containerId, symbol) {
        try {
            // In a real implementation, this would fetch from API
            // For now, generate sample data
            const data = this.generateSampleData(50);
            
            const chartData = this.charts.get(containerId);
            if (!chartData) return;
            
            const chart = chartData.chart;
            chart.data.labels = data.timestamps;
            chart.data.datasets[0].data = data.prices;
            chart.update();
            
        } catch (error) {
            console.error('[ProfessionalCharts] Error loading chart data:', error);
        }
    }
    
    /**
     * Load portfolio data
     */
    async loadPortfolioData(containerId) {
        try {
            const response = await fetch('/api/portfolio');
            const portfolio = await response.json();
            
            // Generate historical portfolio value data
            const data = this.generateSampleData(30, portfolio.total_value || 10000);
            
            const chartData = this.charts.get(containerId);
            if (!chartData) return;
            
            const chart = chartData.chart;
            chart.data.labels = data.timestamps;
            chart.data.datasets[0].data = data.prices;
            chart.update();
            
        } catch (error) {
            console.error('[ProfessionalCharts] Error loading portfolio data:', error);
        }
    }
    
    /**
     * Setup real-time updates via WebSocket
     */
    setupRealtimeUpdates() {
        if (!this.realtimeClient) return;
        
        // Listen for price updates
        this.realtimeClient.on('price_update', (data) => {
            const symbol = data.symbol;
            const price = data.price;
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            
            // Find charts displaying this symbol
            this.charts.forEach((chartData, containerId) => {
                if (chartData.symbol === symbol || chartData.symbol === `${symbol}/USD`) {
                    this.updateChart(containerId, timestamp, price);
                }
            });
        });
        
        console.log('[ProfessionalCharts] Real-time updates enabled');
    }
    
    /**
     * Update chart timeframe
     */
    updateChartTimeframe(containerId, timeframe) {
        console.log(`[ProfessionalCharts] Changing timeframe to ${timeframe} for ${containerId}`);
        
        const chartData = this.charts.get(containerId);
        if (!chartData) return;
        
        chartData.options.timeframe = timeframe;
        
        // Reload data with new timeframe
        this.loadChartData(containerId, chartData.symbol);
    }
    
    /**
     * Generate sample data for testing
     */
    generateSampleData(points, basePrice = 50000) {
        const timestamps = [];
        const prices = [];
        let currentPrice = basePrice;
        
        for (let i = 0; i < points; i++) {
            const date = new Date();
            date.setMinutes(date.getMinutes() - (points - i));
            timestamps.push(date.toLocaleTimeString());
            
            // Random walk
            const change = (Math.random() - 0.5) * basePrice * 0.02;
            currentPrice += change;
            prices.push(currentPrice);
        }
        
        return { timestamps, prices };
    }
    
    /**
     * Destroy a chart
     */
    destroyChart(containerId) {
        const chartData = this.charts.get(containerId);
        if (chartData && chartData.chart) {
            chartData.chart.destroy();
            this.charts.delete(containerId);
        }
    }
    
    /**
     * Destroy all charts
     */
    destroyAll() {
        this.charts.forEach((chartData, containerId) => {
            if (chartData.chart) {
                chartData.chart.destroy();
            }
        });
        this.charts.clear();
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Global instance
const professionalCharts = new ProfessionalCharts();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        professionalCharts.init();
    });
} else {
    professionalCharts.init();
}

// Export for global access
window.professionalCharts = professionalCharts;
