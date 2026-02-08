/**
 * Enhanced Chart Controls
 * Adds zoom, pan, technical indicators, and export capabilities to Chart.js charts
 */

class EnhancedChart {
    constructor(canvasId, options = {}) {
        this.canvasId = canvasId;
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('[EnhancedChart] Canvas not found:', canvasId);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.chart = null;
        this.originalData = null;
        this.indicators = new Map();
        this.options = options;
        
        this.init();
    }
    
    init() {
        // Create enhanced chart with zoom/pan capabilities
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.1
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'xy'
                    },
                    pan: {
                        enabled: true,
                        mode: 'xy'
                    },
                    limits: {
                        x: { min: 'original', max: 'original' },
                        y: { min: 'original', max: 'original' }
                    }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: (context) => {
                            // Show indicator values in tooltip
                            let labels = [];
                            this.indicators.forEach((config, name) => {
                                if (config.dataset && context.datasetIndex === config.dataset.index) {
                                    labels.push(`${name}: ${context.parsed.y.toFixed(2)}`);
                                }
                            });
                            return labels.join('\n');
                        }
                    }
                },
                legend: {
                    display: true,
                    position: 'top',
                    onClick: (e, legendItem, legend) => {
                        // Toggle dataset visibility
                        const index = legendItem.datasetIndex;
                        const chart = legend.chart;
                        const meta = chart.getDatasetMeta(index);
                        meta.hidden = !meta.hidden;
                        chart.update();
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            },
            ...this.options
        };
        
        // Note: To use zoom plugin, you need to include chartjs-plugin-zoom
        // For now, we'll provide the structure
        console.log('[EnhancedChart] Initialized for', canvasId);
    }
    
    create(type, data, options = {}) {
        this.originalData = JSON.parse(JSON.stringify(data));
        
        if (this.chart) {
            this.chart.destroy();
        }
        
        this.chart = new Chart(this.ctx, {
            type: type,
            data: data,
            options: {
                ...this.options,
                ...options
            }
        });
        
        return this.chart;
    }
    
    // Technical Indicators
    
    addIndicator(type, period = 20, options = {}) {
        if (!this.chart || !this.originalData) {
            console.error('[EnhancedChart] Chart not initialized');
            return;
        }
        
        let indicatorData;
        let label;
        let color;
        
        switch (type) {
            case 'sma':
                indicatorData = this.calculateSMA(this.getDataValues(), period);
                label = `SMA(${period})`;
                color = 'rgba(255, 99, 132, 1)';
                break;
            case 'ema':
                indicatorData = this.calculateEMA(this.getDataValues(), period);
                label = `EMA(${period})`;
                color = 'rgba(54, 162, 235, 1)';
                break;
            case 'bb':
                return this.addBollingerBands(period, options.stdDev || 2);
            case 'rsi':
                return this.addRSI(period);
            default:
                console.warn('[EnhancedChart] Unknown indicator:', type);
                return;
        }
        
        const dataset = {
            label: label,
            data: indicatorData,
            borderColor: color,
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1
        };
        
        this.chart.data.datasets.push(dataset);
        this.indicators.set(label, { type, period, dataset });
        this.chart.update();
        
        console.log('[EnhancedChart] Added indicator:', label);
    }
    
    removeIndicator(label) {
        if (!this.chart) return;
        
        const index = this.chart.data.datasets.findIndex(ds => ds.label === label);
        if (index > -1) {
            this.chart.data.datasets.splice(index, 1);
            this.indicators.delete(label);
            this.chart.update();
            console.log('[EnhancedChart] Removed indicator:', label);
        }
    }
    
    calculateSMA(data, period) {
        const sma = [];
        for (let i = 0; i < data.length; i++) {
            if (i < period - 1) {
                sma.push(null);
            } else {
                let sum = 0;
                for (let j = 0; j < period; j++) {
                    sum += data[i - j];
                }
                sma.push(sum / period);
            }
        }
        return sma;
    }
    
    calculateEMA(data, period) {
        const ema = [];
        const multiplier = 2 / (period + 1);
        
        // First EMA is SMA
        let sum = 0;
        for (let i = 0; i < period; i++) {
            sum += data[i];
        }
        ema[period - 1] = sum / period;
        
        // Calculate EMA for rest
        for (let i = period; i < data.length; i++) {
            ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1];
        }
        
        // Fill nulls at start
        for (let i = 0; i < period - 1; i++) {
            ema[i] = null;
        }
        
        return ema;
    }
    
    addBollingerBands(period = 20, stdDevMultiplier = 2) {
        if (!this.chart) return;
        
        const data = this.getDataValues();
        const sma = this.calculateSMA(data, period);
        
        // Calculate standard deviation
        const upperBand = [];
        const lowerBand = [];
        
        for (let i = 0; i < data.length; i++) {
            if (i < period - 1) {
                upperBand.push(null);
                lowerBand.push(null);
            } else {
                let sumSquaredDiff = 0;
                for (let j = 0; j < period; j++) {
                    const diff = data[i - j] - sma[i];
                    sumSquaredDiff += diff * diff;
                }
                const stdDev = Math.sqrt(sumSquaredDiff / period);
                upperBand.push(sma[i] + (stdDev * stdDevMultiplier));
                lowerBand.push(sma[i] - (stdDev * stdDevMultiplier));
            }
        }
        
        // Add datasets
        this.chart.data.datasets.push({
            label: `BB Upper(${period})`,
            data: upperBand,
            borderColor: 'rgba(255, 206, 86, 0.8)',
            backgroundColor: 'transparent',
            borderWidth: 1,
            pointRadius: 0,
            borderDash: [5, 5]
        });
        
        this.chart.data.datasets.push({
            label: `BB Middle(${period})`,
            data: sma,
            borderColor: 'rgba(255, 206, 86, 1)',
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0
        });
        
        this.chart.data.datasets.push({
            label: `BB Lower(${period})`,
            data: lowerBand,
            borderColor: 'rgba(255, 206, 86, 0.8)',
            backgroundColor: 'transparent',
            borderWidth: 1,
            pointRadius: 0,
            borderDash: [5, 5]
        });
        
        this.indicators.set('Bollinger Bands', { type: 'bb', period });
        this.chart.update();
    }
    
    addRSI(period = 14) {
        // RSI would typically be on a separate chart/axis
        // This is a simplified implementation
        const data = this.getDataValues();
        const rsi = [];
        
        // Calculate gains and losses
        const gains = [];
        const losses = [];
        
        for (let i = 1; i < data.length; i++) {
            const diff = data[i] - data[i - 1];
            gains.push(diff > 0 ? diff : 0);
            losses.push(diff < 0 ? -diff : 0);
        }
        
        // Calculate RSI
        for (let i = 0; i < data.length; i++) {
            if (i < period) {
                rsi.push(null);
            } else {
                let avgGain = 0;
                let avgLoss = 0;
                
                for (let j = 0; j < period; j++) {
                    avgGain += gains[i - j - 1];
                    avgLoss += losses[i - j - 1];
                }
                
                avgGain /= period;
                avgLoss /= period;
                
                const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
                const rsiValue = 100 - (100 / (1 + rs));
                rsi.push(rsiValue);
            }
        }
        
        // Note: RSI should ideally be on a separate chart
        // This adds it to main chart for simplicity
        this.chart.data.datasets.push({
            label: `RSI(${period})`,
            data: rsi,
            borderColor: 'rgba(153, 102, 255, 1)',
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 0,
            yAxisID: 'y-rsi'
        });
        
        // Add RSI axis
        if (!this.chart.options.scales['y-rsi']) {
            this.chart.options.scales['y-rsi'] = {
                type: 'linear',
                position: 'right',
                min: 0,
                max: 100,
                ticks: {
                    callback: (value) => value
                }
            };
        }
        
        this.indicators.set('RSI', { type: 'rsi', period });
        this.chart.update();
    }
    
    getDataValues() {
        // Get main dataset values
        if (!this.chart || !this.chart.data.datasets[0]) {
            return [];
        }
        return this.chart.data.datasets[0].data;
    }
    
    // Chart Controls
    
    zoomIn() {
        if (this.chart && this.chart.zoom) {
            this.chart.zoom(1.1);
        }
    }
    
    zoomOut() {
        if (this.chart && this.chart.zoom) {
            this.chart.zoom(0.9);
        }
    }
    
    resetZoom() {
        if (this.chart && this.chart.resetZoom) {
            this.chart.resetZoom();
        }
    }
    
    exportPNG(filename = 'chart.png') {
        if (!this.canvas) return;
        
        const link = document.createElement('a');
        link.download = filename;
        link.href = this.canvas.toDataURL('image/png');
        link.click();
        
        console.log('[EnhancedChart] Exported as PNG:', filename);
    }
    
    saveConfiguration() {
        const config = {
            indicators: Array.from(this.indicators.entries()),
            type: this.chart?.config.type,
            options: this.options
        };
        
        localStorage.setItem(`chart-config-${this.canvasId}`, JSON.stringify(config));
        console.log('[EnhancedChart] Configuration saved');
    }
    
    loadConfiguration() {
        const saved = localStorage.getItem(`chart-config-${this.canvasId}`);
        if (saved) {
            const config = JSON.parse(saved);
            // Restore indicators
            config.indicators.forEach(([name, indicator]) => {
                this.addIndicator(indicator.type, indicator.period);
            });
            console.log('[EnhancedChart] Configuration loaded');
        }
    }
}

// Utility function to create chart controls UI
function createChartControls(chartId, enhancedChart) {
    const container = document.getElementById(chartId)?.parentElement;
    if (!container) return;
    
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'chart-controls';
    controlsDiv.style.cssText = 'display: flex; gap: 8px; margin: 12px 0; flex-wrap: wrap; align-items: center;';
    
    controlsDiv.innerHTML = `
        <button onclick="window.charts['${chartId}'].zoomIn()" class="chart-btn" title="Zoom In">🔍 +</button>
        <button onclick="window.charts['${chartId}'].zoomOut()" class="chart-btn" title="Zoom Out">🔍 -</button>
        <button onclick="window.charts['${chartId}'].resetZoom()" class="chart-btn" title="Reset Zoom">↺ Reset</button>
        <select id="${chartId}-indicator-select" class="chart-select" style="padding: 8px; border-radius: 4px; background: var(--dark-card); color: white; border: 1px solid var(--dark-border);">
            <option value="">Add Indicator...</option>
            <option value="sma">SMA (Simple Moving Average)</option>
            <option value="ema">EMA (Exponential Moving Average)</option>
            <option value="bb">Bollinger Bands</option>
            <option value="rsi">RSI (Relative Strength Index)</option>
        </select>
        <button onclick="window.charts['${chartId}'].exportPNG('${chartId}.png')" class="chart-btn" title="Save as PNG">💾 Save PNG</button>
    `;
    
    container.insertBefore(controlsDiv, container.firstChild);
    
    // Add indicator selector handler
    document.getElementById(`${chartId}-indicator-select`).addEventListener('change', (e) => {
        const type = e.target.value;
        if (type) {
            const period = prompt('Enter period (default: 20):', '20');
            enhancedChart.addIndicator(type, parseInt(period) || 20);
            e.target.value = '';
        }
    });
    
    // Style buttons
    const style = document.createElement('style');
    style.textContent = `
        .chart-btn {
            padding: 8px 16px;
            background: var(--dark-card, #1e293b);
            color: white;
            border: 1px solid var(--dark-border, #334155);
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
            font-size: 14px;
        }
        .chart-btn:hover {
            background: #3b82f6;
        }
        .chart-controls {
            user-select: none;
        }
        @media (max-width: 767px) {
            .chart-controls {
                gap: 4px;
            }
            .chart-btn {
                padding: 6px 10px;
                font-size: 12px;
            }
        }
    `;
    document.head.appendChild(style);
}

// Initialize enhanced charts
window.charts = window.charts || {};

document.addEventListener('DOMContentLoaded', () => {
    console.log('[EnhancedCharts] Module loaded');
    
    // Note: Chart.js zoom plugin needs to be included separately
    // Add to HTML: <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.0"></script>
});
