/**
 * Analytics Dashboard JavaScript
 * Handles loading and displaying advanced analytics and risk metrics
 */

class AnalyticsDashboard {
    constructor() {
        this.currentSort = 'total_pnl';
        this.drawdownChart = null;
    }
    
    async init() {
        console.log('Initializing Analytics Dashboard...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load all data in parallel
        try {
            await Promise.all([
                this.loadStrategyPerformance(),
                this.loadRiskMetrics(),
                this.loadHourHeatmap(),
                this.loadDayHeatmap(),
                this.loadBestTimes(),
                this.loadMarketPerformance('total_pnl')
            ]);
            console.log('Analytics Dashboard loaded successfully');
        } catch (error) {
            console.error('Error initializing dashboard:', error);
        }
    }
    
    setupEventListeners() {
        // Market filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sortBy = e.target.dataset.sort;
                this.handleFilterChange(sortBy, e.target);
            });
        });
    }
    
    handleFilterChange(sortBy, targetElement) {
        // Update active button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active', 'bg-blue-600');
            btn.classList.add('bg-gray-700');
        });
        targetElement.classList.add('active', 'bg-blue-600');
        targetElement.classList.remove('bg-gray-700');
        
        // Reload market data with new sort
        this.currentSort = sortBy;
        this.loadMarketPerformance(sortBy);
    }
    
    async loadStrategyPerformance() {
        try {
            const response = await fetch('/api/analytics/strategy_performance');
            const data = await response.json();
            
            if (!data.strategies || data.strategies.length === 0) {
                this.showEmptyState('strategy-performance-body', 11, 'No strategy data available');
                return;
            }
            
            const tbody = document.getElementById('strategy-performance-body');
            tbody.innerHTML = '';
            
            data.strategies.forEach(s => {
                const row = document.createElement('tr');
                row.className = s.total_pnl > 0 ? 'bg-green-900 bg-opacity-20' : 'bg-red-900 bg-opacity-20';
                
                row.innerHTML = `
                    <td class="p-3">${this.escapeHtml(s.strategy_name)}</td>
                    <td class="p-3 text-right">${s.total_trades}</td>
                    <td class="p-3 text-right">${s.win_rate.toFixed(1)}%</td>
                    <td class="p-3 text-right ${s.total_pnl > 0 ? 'text-profit' : 'text-loss'}">$${s.total_pnl.toFixed(2)}</td>
                    <td class="p-3 text-right">$${s.avg_profit.toFixed(2)}</td>
                    <td class="p-3 text-right">${s.profit_factor.toFixed(2)}</td>
                    <td class="p-3 text-right text-profit">$${s.largest_win.toFixed(2)}</td>
                    <td class="p-3 text-right text-loss">$${s.largest_loss.toFixed(2)}</td>
                    <td class="p-3 text-right">$${s.expectancy.toFixed(2)}</td>
                    <td class="p-3 text-right">${s.max_consecutive_wins}</td>
                    <td class="p-3 text-right">${s.recovery_factor.toFixed(2)}</td>
                `;
                
                tbody.appendChild(row);
            });
        } catch (error) {
            console.error('Error loading strategy performance:', error);
            this.showEmptyState('strategy-performance-body', 11, 'Error loading data');
        }
    }
    
    async loadRiskMetrics() {
        try {
            const response = await fetch('/api/analytics/risk_metrics');
            const data = await response.json();
            
            // Update risk metric cards
            document.getElementById('sharpe-ratio').textContent = data.sharpe_ratio.toFixed(2);
            document.getElementById('sortino-ratio').textContent = data.sortino_ratio.toFixed(2);
            document.getElementById('max-drawdown').textContent = data.max_drawdown_pct.toFixed(1) + '%';
            document.getElementById('var-95').textContent = '$' + data.var_95.toFixed(2);
            document.getElementById('var-99').textContent = '$' + data.var_99.toFixed(2);
            document.getElementById('calmar-ratio').textContent = data.calmar_ratio.toFixed(2);
            
            // Color code based on thresholds
            this.colorCodeMetric('sharpe-ratio', data.sharpe_ratio, 2.0, 1.0);
            this.colorCodeMetric('sortino-ratio', data.sortino_ratio, 3.0, 1.5);
            this.colorCodeMetric('calmar-ratio', data.calmar_ratio, 3.0, 1.0);
            
            // Load drawdown chart
            await this.renderDrawdownChart();
        } catch (error) {
            console.error('Error loading risk metrics:', error);
        }
    }
    
    colorCodeMetric(elementId, value, excellentThreshold, goodThreshold) {
        const element = document.getElementById(elementId);
        element.classList.remove('text-blue-400', 'text-green-400', 'text-yellow-400', 'text-red-400');
        
        if (value >= excellentThreshold) {
            element.classList.add('text-green-400');
        } else if (value >= goodThreshold) {
            element.classList.add('text-yellow-400');
        } else {
            element.classList.add('text-red-400');
        }
    }
    
    async renderDrawdownChart() {
        try {
            const response = await fetch('/api/analytics/drawdown_history');
            const data = await response.json();
            
            if (!data.dates || data.dates.length === 0) {
                return;
            }
            
            const ctx = document.getElementById('drawdown-chart').getContext('2d');
            
            // Destroy existing chart if it exists
            if (this.drawdownChart) {
                this.drawdownChart.destroy();
            }
            
            this.drawdownChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates.map(d => {
                        try {
                            return new Date(d).toLocaleDateString();
                        } catch {
                            return d;
                        }
                    }),
                    datasets: [{
                        label: 'Drawdown %',
                        data: data.drawdown_pct,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            reverse: true,
                            ticks: {
                                callback: v => v + '%',
                                color: '#9ca3af'
                            },
                            grid: {
                                color: '#374151'
                            }
                        },
                        x: {
                            ticks: {
                                color: '#9ca3af',
                                maxRotation: 45,
                                minRotation: 45
                            },
                            grid: {
                                color: '#374151'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: '#9ca3af'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error rendering drawdown chart:', error);
        }
    }
    
    async loadHourHeatmap() {
        try {
            const response = await fetch('/api/analytics/time/hour_analysis');
            const data = await response.json();
            
            const container = document.getElementById('hour-heatmap');
            container.innerHTML = '';
            container.className = 'heatmap grid grid-cols-6 md:grid-cols-12 gap-2';
            
            data.hours.forEach((hour, i) => {
                const pnl = data.pnl_per_hour[i];
                const trades = data.trades_per_hour[i];
                const winRate = data.win_rate_per_hour[i];
                
                const cell = document.createElement('div');
                cell.className = 'heatmap-cell rounded p-3 text-center transition hover:scale-105';
                
                // Color based on P&L
                if (pnl > 100) {
                    cell.classList.add('bg-green-600');
                } else if (pnl > 0) {
                    cell.classList.add('bg-green-700');
                } else if (pnl > -100) {
                    cell.classList.add('bg-red-700');
                } else {
                    cell.classList.add('bg-red-600');
                }
                
                cell.innerHTML = `
                    <div class="text-xs font-semibold">${hour}:00</div>
                    <div class="text-lg font-bold">$${pnl.toFixed(0)}</div>
                    <div class="text-xs">${trades} trades</div>
                `;
                
                container.appendChild(cell);
            });
        } catch (error) {
            console.error('Error loading hour heatmap:', error);
        }
    }
    
    async loadDayHeatmap() {
        try {
            const response = await fetch('/api/analytics/time/day_analysis');
            const data = await response.json();
            
            const container = document.getElementById('day-heatmap');
            container.innerHTML = '';
            container.className = 'heatmap grid grid-cols-2 md:grid-cols-7 gap-2';
            
            data.days.forEach((day, i) => {
                const dayName = data.day_names[i];
                const pnl = data.pnl_per_day[i];
                const trades = data.trades_per_day[i];
                const winRate = data.win_rate_per_day[i];
                
                const cell = document.createElement('div');
                cell.className = 'heatmap-cell rounded p-4 text-center transition hover:scale-105';
                
                // Color based on P&L
                if (pnl > 100) {
                    cell.classList.add('bg-green-600');
                } else if (pnl > 0) {
                    cell.classList.add('bg-green-700');
                } else if (pnl > -100) {
                    cell.classList.add('bg-red-700');
                } else {
                    cell.classList.add('bg-red-600');
                }
                
                cell.innerHTML = `
                    <div class="text-sm font-semibold">${dayName}</div>
                    <div class="text-2xl font-bold">$${pnl.toFixed(0)}</div>
                    <div class="text-xs">${trades} trades</div>
                    <div class="text-xs">${winRate.toFixed(1)}% WR</div>
                `;
                
                container.appendChild(cell);
            });
        } catch (error) {
            console.error('Error loading day heatmap:', error);
        }
    }
    
    async loadBestTimes() {
        try {
            const response = await fetch('/api/analytics/time/best_times');
            const data = await response.json();
            
            const container = document.getElementById('best-times-list');
            
            let html = '<div class="space-y-4">';
            
            // Top hours
            html += '<div><h4 class="font-semibold mb-2">📅 Top 5 Hours:</h4><ul class="space-y-1">';
            data.top_hours.forEach((item, index) => {
                html += `<li class="flex justify-between items-center">
                    <span>${index + 1}. ${item.hour}</span>
                    <span class="${item.pnl > 0 ? 'text-profit' : 'text-loss'}">$${item.pnl.toFixed(2)}</span>
                </li>`;
            });
            html += '</ul></div>';
            
            // Top days
            html += '<div><h4 class="font-semibold mb-2">📆 Top 3 Days:</h4><ul class="space-y-1">';
            data.top_days.forEach((item, index) => {
                html += `<li class="flex justify-between items-center">
                    <span>${index + 1}. ${item.day}</span>
                    <span class="${item.pnl > 0 ? 'text-profit' : 'text-loss'}">$${item.pnl.toFixed(2)}</span>
                </li>`;
            });
            html += '</ul></div>';
            
            html += '</div>';
            container.innerHTML = html;
        } catch (error) {
            console.error('Error loading best times:', error);
        }
    }
    
    async loadMarketPerformance(sortBy = 'total_pnl') {
        try {
            // Load top markets
            const topResponse = await fetch(`/api/analytics/market_performance/top?n=10&metric=${sortBy}`);
            const topData = await topResponse.json();
            
            const topBody = document.getElementById('top-markets-body');
            topBody.innerHTML = '';
            
            if (!topData.markets || topData.markets.length === 0) {
                this.showEmptyState('top-markets-body', 5, 'No market data available');
            } else {
                topData.markets.forEach((m, index) => {
                    const row = document.createElement('tr');
                    row.className = 'border-b border-dark-border hover:bg-gray-800';
                    
                    row.innerHTML = `
                        <td class="p-2">${this.escapeHtml(m.market)}</td>
                        <td class="p-2 text-right">${m.total_trades}</td>
                        <td class="p-2 text-right">${m.win_rate.toFixed(1)}%</td>
                        <td class="p-2 text-right ${m.total_pnl > 0 ? 'text-profit' : 'text-loss'}">$${m.total_pnl.toFixed(2)}</td>
                        <td class="p-2 text-right">$${m.avg_profit.toFixed(2)}</td>
                    `;
                    
                    topBody.appendChild(row);
                });
            }
            
            // Load worst markets
            const worstResponse = await fetch(`/api/analytics/market_performance/worst?n=10&metric=${sortBy}`);
            const worstData = await worstResponse.json();
            
            const worstBody = document.getElementById('worst-markets-body');
            worstBody.innerHTML = '';
            
            if (!worstData.markets || worstData.markets.length === 0) {
                this.showEmptyState('worst-markets-body', 5, 'No market data available');
            } else {
                worstData.markets.forEach((m, index) => {
                    const row = document.createElement('tr');
                    row.className = 'border-b border-dark-border hover:bg-gray-800';
                    
                    row.innerHTML = `
                        <td class="p-2">${this.escapeHtml(m.market)}</td>
                        <td class="p-2 text-right">${m.total_trades}</td>
                        <td class="p-2 text-right">${m.win_rate.toFixed(1)}%</td>
                        <td class="p-2 text-right ${m.total_pnl > 0 ? 'text-profit' : 'text-loss'}">$${m.total_pnl.toFixed(2)}</td>
                        <td class="p-2 text-right">$${m.avg_profit.toFixed(2)}</td>
                    `;
                    
                    worstBody.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Error loading market performance:', error);
            this.showEmptyState('top-markets-body', 5, 'Error loading data');
            this.showEmptyState('worst-markets-body', 5, 'Error loading data');
        }
    }
    
    showEmptyState(tbodyId, colspan, message) {
        const tbody = document.getElementById(tbodyId);
        tbody.innerHTML = `
            <tr>
                <td colspan="${colspan}" class="p-6 text-center text-gray-400">${message}</td>
            </tr>
        `;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export analytics function
function exportAnalytics(format) {
    window.location.href = `/api/analytics/export?format=${format}`;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new AnalyticsDashboard();
    dashboard.init();
});
