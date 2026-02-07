/**
 * Market Strategy Testing Bot - Dashboard JavaScript
 * 
 * Handles all frontend interactions, data fetching, and chart rendering
 */

// Global state
let currentPage = 'overview';
let cumulativePNLChart = null;
let dailyPNLChart = null;
let strategyChart = null;
let currentTimeRange = '1M';
let autoRefreshEnabled = true;
let autoRefreshInterval = null;
let isRefreshing = false;

// API Base URL
const API_BASE = window.location.origin;

// Initialize API client
const apiClient = new APIClient(API_BASE);

// Auto-refresh interval (30 seconds instead of 10)
const REFRESH_INTERVAL = 30000;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    
    // Check connection status first
    checkConnectionStatus();
    
    // Load initial data
    loadOverviewData();
    loadBotStatus();
    
    // Setup auto-refresh with longer interval (30s)
    startAutoRefresh();
    
    // Add manual refresh button handler
    const refreshBtn = document.getElementById('manual-refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleManualRefresh);
    }
    
    // Add auto-refresh toggle handler
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', handleAutoRefreshToggle);
    }
});

// Connection status checker
async function checkConnectionStatus() {
    try {
        const isConnected = await checkConnection(`${API_BASE}/health`);
        updateConnectionIndicator(isConnected);
        return isConnected;
    } catch (error) {
        console.error('Connection check failed:', error);
        updateConnectionIndicator(false);
        return false;
    }
}

// Update connection indicator UI
function updateConnectionIndicator(isConnected) {
    const indicator = document.getElementById('connection-status');
    const statusText = document.getElementById('connection-status-text');
    
    if (indicator && statusText) {
        if (isConnected) {
            indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-900/20 text-green-400';
            statusText.textContent = 'Connected';
        } else {
            indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-900/20 text-red-400';
            statusText.textContent = 'Disconnected';
        }
    }
}

// Start auto-refresh
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        if (autoRefreshEnabled && !isRefreshing) {
            refreshCurrentPage();
        }
    }, REFRESH_INTERVAL);
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Handle auto-refresh toggle
function handleAutoRefreshToggle(event) {
    autoRefreshEnabled = event.target.checked;
    
    if (autoRefreshEnabled) {
        startAutoRefresh();
        showToast('Auto-refresh enabled (30s interval)', 'success');
    } else {
        stopAutoRefresh();
        showToast('Auto-refresh disabled', 'info');
    }
    
    // Save preference
    storage.set('autoRefreshEnabled', autoRefreshEnabled);
}

// Handle manual refresh
async function handleManualRefresh() {
    if (isRefreshing) {
        showToast('Refresh already in progress', 'info');
        return;
    }
    
    const refreshBtn = document.getElementById('manual-refresh-btn');
    const refreshIcon = refreshBtn?.querySelector('i');
    
    try {
        isRefreshing = true;
        
        // Add spinning animation to icon
        if (refreshIcon) {
            refreshIcon.classList.add('fa-spin');
        }
        
        await refreshCurrentPage();
        showToast('Data refreshed successfully', 'success');
    } catch (error) {
        console.error('Manual refresh failed:', error);
        showToast('Failed to refresh data', 'error');
    } finally {
        isRefreshing = false;
        
        // Remove spinning animation
        if (refreshIcon) {
            refreshIcon.classList.remove('fa-spin');
        }
    }
}

// Refresh current page data
async function refreshCurrentPage() {
    // Check connection first
    const isConnected = await checkConnectionStatus();
    if (!isConnected) {
        console.warn('Not connected to server, skipping refresh');
        return;
    }
    
    if (currentPage === 'overview') {
        await loadOverviewData();
    } else if (currentPage === 'trades') {
        await loadTradesData();
    } else if (currentPage === 'settings') {
        await loadSettings();
    }
    
    // Always refresh bot status
    await loadBotStatus();
}

// Page Navigation
function showPage(pageName, event) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.classList.add('hidden');
    });
    
    // Show selected page
    document.getElementById(`page-${pageName}`).classList.remove('hidden');
    document.getElementById(`page-${pageName}`).classList.add('slide-in');
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('text-white', 'bg-gray-800');
        link.classList.add('text-gray-300');
    });
    
    event.target.closest('.nav-link').classList.add('text-white', 'bg-gray-800');
    event.target.closest('.nav-link').classList.remove('text-gray-300');
    
    currentPage = pageName;
    
    // Load page-specific data
    if (pageName === 'trades') {
        loadTradesData();
    } else if (pageName === 'settings') {
        loadSettings();
    }
}

// Load Overview Data
async function loadOverviewData() {
    try {
        const data = await apiClient.get('/api/overview');
        
        // Update key metrics
        document.getElementById('total-pnl').textContent = formatCurrency(data.total_pnl);
        document.getElementById('total-pnl').className = data.total_pnl >= 0 ? 'text-3xl font-bold mb-1 text-profit' : 'text-3xl font-bold mb-1 text-loss';
        
        document.getElementById('pnl-change').textContent = formatPercentage(data.pnl_change_pct);
        document.getElementById('pnl-change').className = data.pnl_change_pct >= 0 ? 'text-profit' : 'text-loss';
        
        document.getElementById('win-rate').textContent = data.win_rate.toFixed(1) + '%';
        document.getElementById('win-rate-bar').style.width = data.win_rate + '%';
        
        document.getElementById('active-trades').textContent = data.active_trades;
        document.getElementById('total-trades').textContent = data.total_trades;
        
        // Load charts (debounced to prevent too many updates)
        debouncedLoadCharts();
        loadRecentActivity();
        
    } catch (error) {
        console.error('Error loading overview data:', error);
        showToast('Error loading data', 'error');
    }
}

// Debounced chart loading to prevent flickering
const debouncedLoadCharts = debounce(() => {
    loadCumulativePNLChart(currentTimeRange);
    loadDailyPNLChart();
    loadStrategyPerformance();
}, 500);

// Load Cumulative P&L Chart
async function loadCumulativePNLChart(timeRange) {
    try {
        const response = await apiClient.get('/api/charts/cumulative-pnl', { range: timeRange });
        const data = response;
        
        const ctx = document.getElementById('cumulative-pnl-chart');
        if (!ctx) return;
        
        // Properly destroy existing chart
        cumulativePNLChart = destroyChart(cumulativePNLChart);
        
        // Prepare data
        const labels = data.data.map(d => new Date(d.timestamp).toLocaleDateString());
        const values = data.data.map(d => d.value);
        
        // Create chart with no animations
        cumulativePNLChart = createChart(ctx, 'line', {
            labels: labels,
            datasets: [{
                label: 'Cumulative P&L',
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4
            }]
        }, {
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading cumulative P&L chart:', error);
        showToast('Error loading cumulative P&L chart', 'error');
    }
}

// Update cumulative P&L time range
function updateCumulativePNL(timeRange, event) {
    currentTimeRange = timeRange;
    
    // Update button states
    event.target.parentElement.querySelectorAll('button').forEach(btn => {
        btn.classList.remove('bg-blue-600');
        btn.classList.add('bg-gray-700', 'hover:bg-gray-600');
    });
    event.target.classList.add('bg-blue-600');
    event.target.classList.remove('bg-gray-700', 'hover:bg-gray-600');
    
    loadCumulativePNLChart(timeRange);
}

// Load Daily P&L Chart
async function loadDailyPNLChart() {
    try {
        const response = await apiClient.get('/api/charts/daily-pnl');
        const data = response;
        
        const ctx = document.getElementById('daily-pnl-chart');
        if (!ctx) return;
        
        // Properly destroy existing chart
        dailyPNLChart = destroyChart(dailyPNLChart);
        
        // Prepare data
        const labels = data.data.map(d => new Date(d.date).toLocaleDateString());
        const values = data.data.map(d => d.pnl);
        const colors = data.data.map(d => d.pnl >= 0 ? '#10b981' : '#ef4444');
        
        // Create chart with no animations
        dailyPNLChart = createChart(ctx, 'bar', {
            labels: labels,
            datasets: [{
                label: 'Daily P&L',
                data: values,
                backgroundColor: colors,
                borderRadius: 4
            }]
        }, {
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading daily P&L chart:', error);
        showToast('Error loading daily P&L chart', 'error');
    }
}

// Load Strategy Performance Chart
async function loadStrategyPerformance() {
    try {
        const response = await apiClient.get('/api/charts/strategy-performance');
        const data = response;
        
        const ctx = document.getElementById('strategy-performance-chart');
        if (!ctx) return;
        
        // Properly destroy existing chart
        strategyChart = destroyChart(strategyChart);
        
        // Prepare data
        const labels = data.strategies.map(s => s.name);
        const values = data.strategies.map(s => s.pnl);
        const colors = values.map(v => v >= 0 ? '#10b981' : '#ef4444');
        
        // Create chart with no animations
        strategyChart = createChart(ctx, 'bar', {
            labels: labels,
            datasets: [{
                label: 'P&L by Strategy',
                data: values,
                backgroundColor: colors,
                borderRadius: 4
            }]
        }, {
            indexAxis: 'y',
            scales: {
                x: {
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading strategy performance:', error);
        showToast('Error loading strategy performance', 'error');
    }
}

// Load Recent Activity
async function loadRecentActivity() {
    try {
        // For now, just show a placeholder
        const activityDiv = document.getElementById('recent-activity');
        activityDiv.innerHTML = `
            <div class="text-center py-8 text-gray-400">
                <i class="fas fa-clock text-3xl mb-2"></i>
                <p>No recent activity</p>
            </div>
        `;
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

// Load Trades Data
async function loadTradesData() {
    try {
        const response = await fetch(`${API_BASE}/api/trades?page=1&per_page=25`);
        const data = await response.json();
        
        const tbody = document.getElementById('trades-table-body');
        tbody.innerHTML = '';
        
        data.trades.forEach(trade => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-800 transition';
            
            const pnlClass = trade.pnl_usd >= 0 ? 'text-profit' : 'text-loss';
            const entryDate = new Date(trade.entry_time).toLocaleString();
            const exitDate = new Date(trade.exit_time).toLocaleString();
            
            row.innerHTML = `
                <td class="px-6 py-4 text-sm">#${trade.id}</td>
                <td class="px-6 py-4 text-sm font-medium">${trade.symbol}</td>
                <td class="px-6 py-4 text-sm">${trade.strategy}</td>
                <td class="px-6 py-4 text-sm text-gray-400">${entryDate}</td>
                <td class="px-6 py-4 text-sm text-gray-400">${exitDate}</td>
                <td class="px-6 py-4 text-sm">${trade.duration_minutes}m</td>
                <td class="px-6 py-4 text-sm font-medium ${pnlClass}">
                    ${formatCurrency(trade.pnl_usd)} (${trade.pnl_pct.toFixed(2)}%)
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
        document.getElementById('trades-count').textContent = 
            `Showing ${data.trades.length} of ${data.total_count} trades`;
        
    } catch (error) {
        console.error('Error loading trades:', error);
        showToast('Error loading trades', 'error');
    }
}

// Apply Trade Filters
function applyTradeFilters() {
    // TODO: Implement filtering
    showToast('Filters applied', 'success');
    loadTradesData();
}

// Export Trades
function exportTrades() {
    showToast('Exporting trades...', 'info');
    // TODO: Implement export
}

// Load Bot Status
async function loadBotStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/bot/status`);
        const data = await response.json();
        
        // Update status indicator
        const statusText = document.getElementById('bot-status-text');
        const statusDot = document.getElementById('status-dot');
        const statusPing = document.getElementById('status-ping');
        
        if (data.running) {
            statusText.textContent = 'Running';
            statusDot.className = 'relative inline-flex rounded-full h-3 w-3 bg-green-500';
            statusPing.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75';
        } else {
            statusText.textContent = 'Stopped';
            statusDot.className = 'relative inline-flex rounded-full h-3 w-3 bg-red-500';
            statusPing.className = 'hidden';
        }
        
        // Update control page
        document.getElementById('control-status').textContent = data.running ? 'Running' : 'Stopped';
        document.getElementById('bot-mode').textContent = data.mode === 'paper' ? 'Paper Trading' : 'Live Trading';
        document.getElementById('connected-symbols').textContent = data.connected_symbols;
        document.getElementById('active-strategies-count').textContent = data.active_strategies;
        
    } catch (error) {
        console.error('Error loading bot status:', error);
    }
}

// Bot Control Functions
async function startBot() {
    try {
        const response = await fetch(`${API_BASE}/api/bot/start`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot started successfully', 'success');
            loadBotStatus();
        } else {
            showToast('Failed to start bot', 'error');
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showToast('Error starting bot', 'error');
    }
}

async function stopBot() {
    if (!confirm('Are you sure you want to stop the bot?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/bot/stop`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot stopped successfully', 'success');
            loadBotStatus();
        } else {
            showToast('Failed to stop bot', 'error');
        }
    } catch (error) {
        console.error('Error stopping bot:', error);
        showToast('Error stopping bot', 'error');
    }
}

async function restartBot() {
    try {
        const response = await fetch(`${API_BASE}/api/bot/restart`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showToast('Bot restarted successfully', 'success');
            loadBotStatus();
        } else {
            showToast('Failed to restart bot', 'error');
        }
    } catch (error) {
        console.error('Error restarting bot:', error);
        showToast('Error restarting bot', 'error');
    }
}

// Settings Functions
function showSettingsTab(tabName, event) {
    // Hide all settings content
    document.querySelectorAll('.settings-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Show selected content
    document.getElementById(`settings-${tabName}`).classList.remove('hidden');
    
    // Update tab styles
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.classList.remove('border-blue-500', 'text-blue-500');
        tab.classList.add('text-gray-400');
    });
    
    event.target.classList.add('border-blue-500', 'text-blue-500');
    event.target.classList.remove('text-gray-400');
}

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings`);
        const settings = await response.json();
        
        // Load email settings
        if (settings.notifications && settings.notifications.email) {
            const email = settings.notifications.email;
            document.getElementById('email-enabled').checked = email.enabled || false;
            document.getElementById('email-from').value = email.from_email || '';
            document.getElementById('email-to').value = email.to_email || '';
            document.getElementById('email-smtp').value = email.smtp_server || 'smtp.gmail.com';
            document.getElementById('email-port').value = email.smtp_port || 587;
            
            if (email.enabled) {
                document.getElementById('email-settings').classList.remove('hidden');
            }
        }
        
        // Load desktop settings
        if (settings.notifications && settings.notifications.desktop) {
            document.getElementById('desktop-enabled').checked = 
                settings.notifications.desktop.enabled !== false;
        }
        
        // Load telegram settings
        if (settings.notifications && settings.notifications.telegram) {
            const telegram = settings.notifications.telegram;
            document.getElementById('telegram-enabled').checked = telegram.enabled || false;
            document.getElementById('telegram-token').value = telegram.bot_token || '';
            document.getElementById('telegram-chat-id').value = telegram.chat_id || '';
            
            if (telegram.enabled) {
                document.getElementById('telegram-settings').classList.remove('hidden');
            }
        }
        
    } catch (error) {
        console.error('Error loading settings:', error);
        showToast('Error loading settings', 'error');
    }
}

function toggleEmailSettings() {
    const enabled = document.getElementById('email-enabled').checked;
    const settings = document.getElementById('email-settings');
    
    if (enabled) {
        settings.classList.remove('hidden');
    } else {
        settings.classList.add('hidden');
    }
}

function toggleTelegramSettings() {
    const enabled = document.getElementById('telegram-enabled').checked;
    const settings = document.getElementById('telegram-settings');
    
    if (enabled) {
        settings.classList.remove('hidden');
    } else {
        settings.classList.add('hidden');
    }
}

async function saveNotificationSettings() {
    try {
        const settings = {
            email: {
                enabled: document.getElementById('email-enabled').checked,
                from_email: document.getElementById('email-from').value,
                to_email: document.getElementById('email-to').value,
                smtp_server: document.getElementById('email-smtp').value,
                smtp_port: parseInt(document.getElementById('email-port').value) || 587,
                password: document.getElementById('email-password').value
            },
            desktop: {
                enabled: document.getElementById('desktop-enabled').checked
            },
            telegram: {
                enabled: document.getElementById('telegram-enabled').checked,
                bot_token: document.getElementById('telegram-token').value,
                chat_id: document.getElementById('telegram-chat-id').value
            }
        };
        
        const response = await fetch(`${API_BASE}/api/settings/notifications`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Settings saved successfully', 'success');
        } else {
            showToast('Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showToast('Error saving settings', 'error');
    }
}

// Test Notification Functions
async function testEmailNotification() {
    try {
        const response = await fetch(`${API_BASE}/api/notifications/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'email' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Test email sent successfully', 'success');
        } else {
            showToast('Failed to send test email', 'error');
        }
    } catch (error) {
        console.error('Error sending test email:', error);
        showToast('Error sending test email', 'error');
    }
}

async function testDesktopNotification() {
    try {
        const response = await fetch(`${API_BASE}/api/notifications/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'desktop' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Test desktop notification sent', 'success');
        } else {
            showToast('Failed to send desktop notification', 'error');
        }
    } catch (error) {
        console.error('Error sending desktop notification:', error);
        showToast('Error sending desktop notification', 'error');
    }
}

async function testTelegramNotification() {
    try {
        const response = await fetch(`${API_BASE}/api/notifications/test`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type: 'telegram' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Test Telegram message sent', 'success');
        } else {
            showToast('Failed to send Telegram message', 'error');
        }
    } catch (error) {
        console.error('Error sending Telegram message:', error);
        showToast('Error sending Telegram message', 'error');
    }
}

// Utility Functions
function formatCurrency(value) {
    const sign = value >= 0 ? '+' : '';
    return sign + '$' + value.toFixed(2);
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const icon = document.getElementById('toast-icon');
    const messageEl = document.getElementById('toast-message');
    
    // Set icon based on type
    if (type === 'success') {
        icon.className = 'fas fa-check-circle text-green-500 text-xl mr-3';
    } else if (type === 'error') {
        icon.className = 'fas fa-exclamation-circle text-red-500 text-xl mr-3';
    } else {
        icon.className = 'fas fa-info-circle text-blue-500 text-xl mr-3';
    }
    
    messageEl.textContent = message;
    
    // Show toast
    toast.classList.remove('hidden');
    toast.classList.add('slide-in');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
