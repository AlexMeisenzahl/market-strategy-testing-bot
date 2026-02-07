// Main Dashboard JavaScript - Core Logic

// Global state
let currentPage = 1;
let tradesPerPage = 50;
let currentChartView = 'pnl';

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
    
    // Load initial data
    loadAllData();
    
    // Setup auto-refresh
    setupAutoRefresh();
    
    // Setup event source for real-time updates
    setupEventSource();
    
    // Load configuration
    loadConfiguration();
});

// Load all dashboard data
function loadAllData() {
    loadStatus();
    loadMetrics();
    loadStrategies();
    loadTrades();
    loadOpportunities();
    loadAlerts();
}

// Load bot status
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateStatusDisplay(data);
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

// Load metrics
async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        updateMetricsDisplay(data);
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

// Load strategies
async function loadStrategies() {
    try {
        const response = await fetch('/api/strategies');
        const strategies = await response.json();
        
        updateStrategiesTable(strategies);
    } catch (error) {
        console.error('Error loading strategies:', error);
    }
}

// Load trades
async function loadTrades() {
    try {
        const response = await fetch(`/api/trades?page=${currentPage}&per_page=${tradesPerPage}`);
        const data = await response.json();
        
        updateTradesTable(data.trades);
        updatePagination(data.page, Math.ceil(data.total / data.per_page));
    } catch (error) {
        console.error('Error loading trades:', error);
    }
}

// Load opportunities
async function loadOpportunities() {
    try {
        const response = await fetch('/api/opportunities');
        const data = await response.json();
        
        updateOpportunitiesDisplay(data.opportunities);
    } catch (error) {
        console.error('Error loading opportunities:', error);
    }
}

// Load alerts
async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        
        updateAlertsDisplay(data.alerts);
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Update status display
function updateStatusDisplay(data) {
    const badge = document.getElementById('status-badge');
    const uptimeText = document.getElementById('uptime-text');
    const infoUptime = document.getElementById('info-uptime');
    const infoLastUpdate = document.getElementById('info-last-update');
    const infoConnection = document.getElementById('info-connection');
    
    // Update status badge
    badge.className = 'badge';
    if (data.status === 'running') {
        badge.classList.add('badge-running');
        badge.textContent = '● Running';
    } else if (data.status === 'paused') {
        badge.classList.add('badge-paused');
        badge.textContent = '● Paused';
    } else {
        badge.classList.add('badge-stopped');
        badge.textContent = '● Stopped';
    }
    
    // Update uptime
    const hours = Math.floor(data.uptime / 3600);
    const minutes = Math.floor((data.uptime % 3600) / 60);
    const uptimeStr = `Uptime: ${hours}h ${minutes}m`;
    uptimeText.textContent = uptimeStr;
    
    if (infoUptime) {
        infoUptime.textContent = `${hours}h ${minutes}m`;
    }
    
    // Update last update time
    if (infoLastUpdate) {
        const updateTime = new Date(data.last_update);
        infoLastUpdate.textContent = updateTime.toLocaleTimeString();
    }
    
    // Update connection status
    if (infoConnection) {
        infoConnection.className = 'info-value badge';
        if (data.connection_healthy) {
            infoConnection.classList.add('badge-success');
            infoConnection.textContent = 'Connected';
        } else {
            infoConnection.classList.add('badge-danger');
            infoConnection.textContent = 'Disconnected';
        }
    }
}

// Update metrics display
function updateMetricsDisplay(data) {
    // Total P&L
    const pnlElement = document.getElementById('metric-pnl');
    const pnlPctElement = document.getElementById('metric-pnl-pct');
    pnlElement.textContent = `$${data.total_pnl.toFixed(2)}`;
    pnlPctElement.textContent = `${data.pnl_percentage >= 0 ? '+' : ''}${data.pnl_percentage.toFixed(1)}%`;
    pnlPctElement.className = 'metric-change ' + (data.pnl_percentage >= 0 ? 'positive' : 'negative');
    
    // Win Rate
    document.getElementById('metric-winrate').textContent = `${data.win_rate.toFixed(1)}%`;
    
    // Total Trades
    document.getElementById('metric-trades').textContent = data.total_trades;
    
    // Current Balance
    document.getElementById('metric-balance').textContent = `$${data.current_balance.toFixed(2)}`;
    
    // Active Opportunities
    document.getElementById('metric-opportunities').textContent = data.active_opportunities;
    
    // Best Strategy
    document.getElementById('metric-strategy').textContent = data.best_strategy;
}

// Update strategies table
function updateStrategiesTable(strategies) {
    const tbody = document.getElementById('strategy-tbody');
    
    if (!strategies || strategies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="no-data">No strategy data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    strategies.forEach(strategy => {
        const row = document.createElement('tr');
        
        const pnlClass = strategy.total_pnl >= 0 ? 'profit-positive' : 'profit-negative';
        
        row.innerHTML = `
            <td>${strategy.name}</td>
            <td>${strategy.total_trades}</td>
            <td>${strategy.win_rate.toFixed(1)}%</td>
            <td class="${pnlClass}">$${strategy.total_pnl.toFixed(2)}</td>
            <td class="${pnlClass}">$${strategy.avg_profit.toFixed(2)}</td>
            <td>${strategy.roi.toFixed(1)}%</td>
            <td class="profit-positive">$${strategy.best_trade.toFixed(2)}</td>
            <td class="profit-negative">$${strategy.worst_trade.toFixed(2)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update trades table
function updateTradesTable(trades) {
    const tbody = document.getElementById('trades-tbody');
    
    if (!trades || trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="no-data">No trades executed yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    trades.forEach(trade => {
        const row = document.createElement('tr');
        
        const timestamp = new Date(trade.executed_at).toLocaleString();
        const profitClass = trade.expected_profit >= 0 ? 'profit-positive' : 'profit-negative';
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${trade.market_name}</td>
            <td>Arbitrage</td>
            <td>$${parseFloat(trade.yes_price).toFixed(2)}</td>
            <td>$${parseFloat(trade.no_price).toFixed(2)}</td>
            <td>$${parseFloat(trade.trade_size).toFixed(2)}</td>
            <td class="${profitClass}">$${parseFloat(trade.expected_profit).toFixed(2)}</td>
            <td class="${profitClass}">${parseFloat(trade.profit_percentage).toFixed(2)}%</td>
            <td>${trade.status}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update opportunities display
function updateOpportunitiesDisplay(opportunities) {
    const container = document.getElementById('opportunities-container');
    
    if (!opportunities || opportunities.length === 0) {
        container.innerHTML = '<p class="no-data">No opportunities detected</p>';
        return;
    }
    
    container.innerHTML = '';
    
    // Show most recent opportunities first
    const recentOpps = opportunities.slice(-20).reverse();
    
    recentOpps.forEach(opp => {
        const card = document.createElement('div');
        card.className = 'opportunity-card';
        
        if (opp.profit_margin > 5) {
            card.classList.add('high-profit');
        }
        
        const timestamp = new Date(opp.detected_at).toLocaleTimeString();
        
        card.innerHTML = `
            <div class="opportunity-header">
                <div class="opportunity-title">${opp.market_name}</div>
                <div class="opportunity-profit">${parseFloat(opp.profit_margin).toFixed(2)}%</div>
            </div>
            <div class="opportunity-details">
                <span><i class="fas fa-check"></i> YES: $${parseFloat(opp.yes_price).toFixed(2)}</span>
                <span><i class="fas fa-times"></i> NO: $${parseFloat(opp.no_price).toFixed(2)}</span>
                <span><i class="fas fa-clock"></i> ${timestamp}</span>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// Update alerts display
function updateAlertsDisplay(alerts) {
    const container = document.getElementById('alerts-container');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="no-data">No alerts</p>';
        return;
    }
    
    container.innerHTML = '';
    
    // Show most recent alerts first
    const recentAlerts = alerts.slice(-10).reverse();
    
    recentAlerts.forEach(alert => {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert-item ${alert.type}`;
        
        const icons = {
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            success: 'fa-check-circle'
        };
        
        const timestamp = new Date(alert.timestamp).toLocaleTimeString();
        
        alertDiv.innerHTML = `
            <div class="alert-icon">
                <i class="fas ${icons[alert.type] || 'fa-info-circle'}"></i>
            </div>
            <div class="alert-content">
                <div class="alert-time">${timestamp}</div>
                <div class="alert-message">${alert.message}</div>
            </div>
        `;
        
        container.appendChild(alertDiv);
    });
}

// Update pagination
function updatePagination(currentPage, totalPages) {
    const pageInfo = document.getElementById('page-info');
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
}

// Change trade page
function changeTradePage(delta) {
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    loadTrades();
}

// Setup auto-refresh
function setupAutoRefresh() {
    setInterval(() => {
        loadStatus();
        loadMetrics();
        loadOpportunities();
        loadAlerts();
    }, 2000); // Refresh every 2 seconds
}

// Setup Server-Sent Events for real-time updates
function setupEventSource() {
    try {
        const eventSource = new EventSource('/api/stream');
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('Real-time update:', data);
            
            // Reload specific data if there are new items
            if (data.new_opportunities > 0) {
                loadOpportunities();
            }
            if (data.new_trades > 0) {
                loadTrades();
                loadMetrics();
                loadStrategies();
            }
        };
        
        eventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            // Fallback to polling if SSE fails
            eventSource.close();
        };
    } catch (error) {
        console.error('Error setting up EventSource:', error);
    }
}

// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Add active class to clicked button
    event.target.closest('.tab-button').classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'charts') {
        loadCharts();
    } else if (tabName === 'trades') {
        loadTrades();
    } else if (tabName === 'opportunities') {
        loadOpportunities();
    }
}

// Refresh all data
function refreshData() {
    showToast('Refreshing data...', 'info');
    loadAllData();
    setTimeout(() => {
        showToast('Data refreshed successfully', 'success');
    }, 500);
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            container.removeChild(toast);
        }, 300);
    }, 3000);
}

// Sort table
function sortTable(columnIndex) {
    const table = document.getElementById('strategy-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Skip if no data
    if (rows.length === 1 && rows[0].querySelector('.no-data')) {
        return;
    }
    
    // Toggle sort direction
    const currentDir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
    table.dataset.sortDir = currentDir;
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try to parse as number
        const aNum = parseFloat(aValue.replace(/[$%,]/g, ''));
        const bNum = parseFloat(bValue.replace(/[$%,]/g, ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return currentDir === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return currentDir === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));
}

// Export trades to CSV
function exportTradesCSV() {
    fetch('/api/trades?per_page=10000')
        .then(response => response.json())
        .then(data => {
            const trades = data.trades;
            
            if (!trades || trades.length === 0) {
                showToast('No trades to export', 'warning');
                return;
            }
            
            // Create CSV content
            const headers = ['Timestamp', 'Market', 'Strategy', 'YES Price', 'NO Price', 
                             'Trade Size', 'Profit/Loss', 'Profit %', 'Status'];
            let csv = headers.join(',') + '\n';
            
            trades.forEach(trade => {
                const row = [
                    new Date(trade.executed_at).toISOString(),
                    trade.market_name,
                    'Arbitrage',
                    trade.yes_price,
                    trade.no_price,
                    trade.trade_size,
                    trade.expected_profit,
                    trade.profit_percentage,
                    trade.status
                ];
                csv += row.join(',') + '\n';
            });
            
            // Download CSV
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `trades_${new Date().toISOString()}.csv`;
            a.click();
            
            showToast('Trades exported successfully', 'success');
        })
        .catch(error => {
            console.error('Error exporting trades:', error);
            showToast('Error exporting trades', 'error');
        });
}

// Load configuration
async function loadConfiguration() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Update form fields
        document.getElementById('config-min-profit').value = (config.min_profit_margin * 100).toFixed(2);
        document.getElementById('config-max-trade').value = config.max_trade_size;
        document.getElementById('config-max-per-hour').value = config.max_trades_per_hour;
        
        // Update notification toggles
        document.getElementById('toggle-desktop').checked = config.desktop_notifications;
    } catch (error) {
        console.error('Error loading configuration:', error);
    }
}

// Save configuration
async function saveConfiguration() {
    try {
        const config = {
            min_profit_margin: parseFloat(document.getElementById('config-min-profit').value) / 100,
            max_trade_size: parseFloat(document.getElementById('config-max-trade').value),
            max_trades_per_hour: parseInt(document.getElementById('config-max-per-hour').value),
        };
        
        const response = await fetch('/api/config/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast('Configuration saved successfully', 'success');
        } else {
            showToast('Error saving configuration: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        showToast('Error saving configuration', 'error');
    }
}

// Reset configuration
function resetConfiguration() {
    document.getElementById('config-min-profit').value = '2.00';
    document.getElementById('config-max-trade').value = '10';
    document.getElementById('config-max-per-hour').value = '10';
    
    showToast('Configuration reset to defaults', 'info');
}

// Toggle notification
async function toggleNotification(type, enabled) {
    try {
        const response = await fetch('/api/notifications/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type, enabled }),
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} notifications ${enabled ? 'enabled' : 'disabled'}`, 'success');
        } else {
            showToast('Error updating notification setting: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Error toggling notification:', error);
        showToast('Error updating notification setting', 'error');
    }
}
