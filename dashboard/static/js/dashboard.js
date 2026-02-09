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

// Auto-refresh interval (15 seconds to prevent spam)
const REFRESH_INTERVAL = 15000;

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

// Update combined status indicator (bot + connection)
function updateCombinedStatus(botStatus = {}, isConnected = true) {
    const indicator = document.getElementById('combined-status');
    const statusText = document.getElementById('combined-status-text');
    const statusDot = document.getElementById('status-dot');
    const statusPing = document.getElementById('status-ping');
    
    if (!indicator || !statusText || !statusDot || !statusPing) return;
    
    // Determine overall status
    const botRunning = botStatus.running || false;
    const mode = botStatus.mode === 'paper' ? 'Paper' : 'Live';
    
    if (!isConnected) {
        // Disconnected - red
        indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-900/20 text-red-400';
        statusDot.className = 'relative inline-flex rounded-full h-3 w-3 bg-red-500';
        statusPing.className = 'hidden';
        statusText.textContent = 'Disconnected';
    } else if (botRunning) {
        // Bot running and connected - green
        indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-900/20 text-green-400';
        statusDot.className = 'relative inline-flex rounded-full h-3 w-3 bg-green-500';
        statusPing.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75';
        statusText.textContent = `Bot Running (${mode}) • Connected`;
    } else if (botStatus.status_text === 'Error') {
        // Bot error - yellow
        indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-900/20 text-yellow-400';
        statusDot.className = 'relative inline-flex rounded-full h-3 w-3 bg-yellow-500';
        statusPing.className = 'hidden';
        statusText.textContent = 'Bot Error • Connected';
    } else {
        // Bot stopped but connected - gray
        indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-700/20 text-gray-400';
        statusDot.className = 'relative inline-flex rounded-full h-3 w-3 bg-gray-500';
        statusPing.className = 'hidden';
        statusText.textContent = 'Bot Stopped • Connected';
    }
}

// Update connection indicator UI (legacy - now uses combined status)
function updateConnectionIndicator(isConnected) {
    // Update combined status with current connection state
    updateCombinedStatus({}, isConnected);
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
        showToast('Auto-refresh enabled (15s interval)', 'success');
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
    } else if (currentPage === 'opportunities') {
        await loadOpportunitiesData();
    } else if (currentPage === 'analytics') {
        await loadAnalyticsData();
    } else if (currentPage === 'tax') {
        await loadTaxData();
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
    } else if (pageName === 'opportunities') {
        loadOpportunitiesData();
    } else if (pageName === 'analytics') {
        loadAnalyticsData();
    } else if (pageName === 'tax') {
        loadTaxData();
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
        
        // Update combined status indicator with bot data
        updateCombinedStatus(data, true);
        
        // Update data source based on bot status
        if (data.running) {
            const mode = data.mode || 'paper';
            updateDataSourceIndicator('live', mode);
        } else {
            updateDataSourceIndicator('historical');
        }
        
        // Update control page
        document.getElementById('control-status').textContent = data.status_text || (data.running ? 'Running' : 'Stopped');
        document.getElementById('bot-mode').textContent = data.mode === 'paper' ? 'Paper Trading' : 'Live Trading';
        document.getElementById('connected-symbols').textContent = data.connected_symbols || 0;
        document.getElementById('active-strategies-count').textContent = data.active_strategies || 0;
        
    } catch (error) {
        console.error('Error loading bot status:', error);
        // Update to show disconnected on error
        updateCombinedStatus({}, false);
        // Default to historical data on error
        updateDataSourceIndicator('historical');
    }
}

// Update data source indicator
function updateDataSourceIndicator(source, tradingMode = null) {
    const indicator = document.getElementById('data-source-indicator');
    const text = document.getElementById('data-source-text');
    
    if (!indicator || !text) return;
    
    if (source === 'live') {
        indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-900/20 text-green-400';
        const modeText = tradingMode === 'paper' ? 'Paper' : 'Live';
        text.innerHTML = `🟢 Live APIs (${modeText})`;
    } else {
        indicator.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-900/20 text-blue-400';
        text.innerHTML = '📊 Historical Data';
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

// Opportunities Page Functions
let currentOpportunities = [];

async function loadOpportunitiesData() {
    try {
        const strategy = document.getElementById('opp-filter-strategy')?.value || '';
        const symbol = document.getElementById('opp-filter-symbol')?.value || '';
        const status = document.getElementById('opp-filter-status')?.value || '';
        
        const params = new URLSearchParams();
        if (strategy) params.append('strategy', strategy);
        if (symbol) params.append('symbol', symbol);
        if (status) params.append('status', status);
        
        const response = await fetch(`${API_BASE}/api/opportunities?${params.toString()}`);
        const data = await response.json();
        
        // Handle both array and object responses
        const opportunities = Array.isArray(data) ? data : (data.opportunities || []);
        currentOpportunities = opportunities;
        renderOpportunities(opportunities);
    } catch (error) {
        console.error('Error loading opportunities:', error);
        showToast('Error loading opportunities', 'error');
    }
}

function renderOpportunities(opportunities) {
    const tbody = document.getElementById('opportunities-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!opportunities || opportunities.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-gray-400">
                    <i class="fas fa-search text-3xl mb-2"></i>
                    <p>No opportunities found</p>
                </td>
            </tr>
        `;
        document.getElementById('opportunities-count').textContent = 'No opportunities';
        return;
    }
    
    opportunities.forEach(opp => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-800 transition cursor-pointer';
        row.dataset.opportunity = JSON.stringify(opp);
        
        // Format timestamp
        const timestamp = new Date(opp.timestamp).toLocaleString();
        
        // Status badge
        let statusBadge = '';
        let status = opp.status || (opp.action_taken ? 'executed' : 'pending');
        if (status === 'executed' || opp.action_taken) {
            statusBadge = '<span class="px-2 py-1 text-xs font-semibold rounded bg-green-900/20 text-green-400">Executed</span>';
        } else if (status === 'pending') {
            statusBadge = '<span class="px-2 py-1 text-xs font-semibold rounded bg-yellow-900/20 text-yellow-400">Pending</span>';
        } else {
            statusBadge = '<span class="px-2 py-1 text-xs font-semibold rounded bg-red-900/20 text-red-400">Rejected</span>';
        }
        
        // Confidence color
        const confidence = parseFloat(opp.confidence) || 0;
        let confidenceColor = 'text-gray-400';
        if (confidence >= 85) confidenceColor = 'text-green-400';
        else if (confidence >= 70) confidenceColor = 'text-yellow-400';
        else confidenceColor = 'text-red-400';
        
        // Signal type
        const signal = opp.signal || opp.signal_type || 'BUY';
        
        // Price display
        const price = opp.price;
        let priceDisplay = 'N/A';
        if (price !== null && price !== undefined && !isNaN(price)) {
            priceDisplay = `$${parseFloat(price).toFixed(2)}`;
        }
        
        row.innerHTML = `
            <td class="px-6 py-4 text-sm text-gray-400">${timestamp}</td>
            <td class="px-6 py-4 text-sm font-medium">${opp.symbol}</td>
            <td class="px-6 py-4 text-sm">${opp.strategy}</td>
            <td class="px-6 py-4 text-sm">
                <span class="px-2 py-1 text-xs font-semibold rounded ${signal === 'BUY' ? 'bg-green-900/20 text-green-400' : 'bg-red-900/20 text-red-400'}">
                    ${signal}
                </span>
            </td>
            <td class="px-6 py-4 text-sm font-medium ${confidenceColor}">${confidence}%</td>
            <td class="px-6 py-4 text-sm">${priceDisplay}</td>
            <td class="px-6 py-4 text-sm">${statusBadge}</td>
            <td class="px-6 py-4 text-sm">
                <button class="text-blue-400 hover:text-blue-300 view-details-btn">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        
        // Add click event listener
        row.addEventListener('click', function() {
            const oppData = JSON.parse(this.dataset.opportunity);
            viewOpportunityDetails(oppData);
        });
        
        tbody.appendChild(row);
    });
    
    document.getElementById('opportunities-count').textContent = 
        `Showing ${opportunities.length} opportunit${opportunities.length === 1 ? 'y' : 'ies'}`;
}

function applyOpportunityFilters() {
    loadOpportunitiesData();
    showToast('Filters applied', 'success');
}

function viewOpportunityDetails(opp) {
    alert(`Opportunity Details:\n\nSymbol: ${opp.symbol}\nStrategy: ${opp.strategy}\nSignal: ${opp.signal}\nConfidence: ${opp.confidence}%\nPrice: $${opp.price}\nStatus: ${opp.status}\nNotes: ${opp.notes || 'N/A'}`);
}

// Initialize opportunities page
document.addEventListener('DOMContentLoaded', function() {
    const oppFilterBtn = document.getElementById('opp-apply-filters-btn');
    if (oppFilterBtn) {
        oppFilterBtn.addEventListener('click', applyOpportunityFilters);
    }
});

// Tax Page Functions
async function loadTaxData() {
    try {
        const year = new Date().getFullYear();
        
        // Load tax summary
        const summaryResponse = await fetch(`${API_BASE}/api/tax/summary?year=${year}`);
        const summary = await summaryResponse.json();
        
        // Update summary cards (if they have IDs)
        console.log('Tax summary loaded:', summary);
        
        // Load tax positions
        const positionsResponse = await fetch(`${API_BASE}/api/tax/positions?year=${year}`);
        const positions = await positionsResponse.json();
        
        console.log('Tax positions loaded:', positions);
        showToast('Tax data loaded', 'success');
    } catch (error) {
        console.error('Error loading tax data:', error);
        showToast('Error loading tax data', 'error');
    }
}

// Analytics Page Functions
async function loadAnalyticsData() {
    try {
        // Load risk analytics
        const riskResponse = await fetch(`${API_BASE}/api/analytics/risk`);
        const risk = await riskResponse.json();
        
        console.log('Risk analytics loaded:', risk);
        
        // Load strategy breakdown
        const strategyResponse = await fetch(`${API_BASE}/api/analytics/strategy-breakdown`);
        const strategies = await strategyResponse.json();
        
        console.log('Strategy breakdown loaded:', strategies);
        showToast('Analytics loaded', 'success');
    } catch (error) {
        console.error('Error loading analytics:', error);
        showToast('Error loading analytics', 'error');
    }
}

// ========================================================================
// ACTIVITY FEED FUNCTIONS
// ========================================================================

let activityPaused = false;
let activityFilter = 'all';
let activityRefreshInterval = null;
let allActivities = [];

/**
 * Load and display recent activity feed
 */
async function loadRecentActivity() {
    if (activityPaused) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/recent_activity`);
        if (!response.ok) throw new Error('Failed to load activity');
        
        allActivities = await response.json();
        displayActivityFeed();
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

/**
 * Display activity feed with current filter
 */
function displayActivityFeed() {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    // Filter activities
    let filtered = allActivities;
    if (activityFilter !== 'all') {
        filtered = allActivities.filter(a => a.type === activityFilter);
    }
    
    // Apply search if any
    const searchInput = document.getElementById('activity-search');
    if (searchInput && searchInput.value) {
        const searchTerm = searchInput.value.toLowerCase();
        filtered = filtered.filter(a => 
            a.message.toLowerCase().includes(searchTerm)
        );
    }
    
    // Clear container
    container.innerHTML = '';
    
    if (filtered.length === 0) {
        container.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                <i class="fas fa-inbox mb-2"></i>
                <p class="text-sm">No activities found</p>
            </div>
        `;
        return;
    }
    
    // Render activities (max 20)
    filtered.slice(0, 20).forEach(activity => {
        const activityEl = createActivityElement(activity);
        container.appendChild(activityEl);
    });
}

/**
 * Create activity element
 */
function createActivityElement(activity) {
    const div = document.createElement('div');
    div.className = 'p-3 rounded-lg cursor-pointer hover:bg-gray-800 transition';
    
    // Color coding
    let bgColor = 'bg-gray-800';
    let textColor = 'text-gray-300';
    let icon = 'fa-circle';
    
    if (activity.type === 'trade') {
        if (activity.profit > 0) {
            bgColor = 'bg-green-900/20';
            textColor = 'text-green-400';
            icon = 'fa-arrow-up';
        } else if (activity.profit < 0) {
            bgColor = 'bg-red-900/20';
            textColor = 'text-red-400';
            icon = 'fa-arrow-down';
        }
    } else if (activity.type === 'opportunity') {
        bgColor = 'bg-yellow-900/20';
        textColor = 'text-yellow-400';
        icon = 'fa-lightbulb';
    } else if (activity.type === 'error') {
        bgColor = 'bg-orange-900/20';
        textColor = 'text-orange-400';
        icon = 'fa-exclamation-triangle';
    }
    
    // Format timestamp
    const time = new Date(activity.timestamp).toLocaleTimeString();
    
    div.className = `p-3 rounded-lg cursor-pointer hover:bg-gray-700 transition ${bgColor}`;
    div.innerHTML = `
        <div class="flex items-start">
            <i class="fas ${icon} ${textColor} mt-1 mr-3"></i>
            <div class="flex-1">
                <p class="text-sm ${textColor}">${activity.message}</p>
                <p class="text-xs text-gray-500 mt-1">${time}</p>
            </div>
        </div>
    `;
    
    // Click to see details
    div.onclick = () => showActivityDetails(activity);
    
    return div;
}

/**
 * Show activity details in modal
 */
function showActivityDetails(activity) {
    const details = JSON.stringify(activity.details, null, 2);
    alert(`Activity Details:\n\n${details}`);
}

/**
 * Toggle activity feed pause
 */
function toggleActivityPause() {
    activityPaused = !activityPaused;
    const btn = document.getElementById('pause-activity');
    
    if (activityPaused) {
        btn.innerHTML = '<i class="fas fa-play"></i> Resume';
        btn.classList.remove('bg-gray-700');
        btn.classList.add('bg-green-600');
    } else {
        btn.innerHTML = '<i class="fas fa-pause"></i> Pause';
        btn.classList.remove('bg-green-600');
        btn.classList.add('bg-gray-700');
        loadRecentActivity();
    }
}

/**
 * Filter activity by type
 */
function filterActivity(filter, event) {
    activityFilter = filter;
    
    // Update button styles
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-600');
        btn.classList.add('bg-gray-700');
    });
    
    if (event && event.target) {
        event.target.classList.remove('bg-gray-700');
        event.target.classList.add('active', 'bg-blue-600');
    }
    
    displayActivityFeed();
}

/**
 * Search activity
 */
function searchActivity() {
    displayActivityFeed();
}

/**
 * Start activity feed auto-refresh
 */
function startActivityRefresh() {
    // Load immediately
    loadRecentActivity();
    
    // Then refresh every 15 seconds
    if (activityRefreshInterval) {
        clearInterval(activityRefreshInterval);
    }
    activityRefreshInterval = setInterval(loadRecentActivity, 15000);
}

// ========================================================================
// DATA QUALITY VERIFICATION
// ========================================================================

/**
 * Verify data quality
 */
async function verifyDataQuality() {
    const statusEl = document.getElementById('health-status');
    const statusIcon = statusEl.querySelector('.status-icon');
    const statusText = statusEl.querySelector('.status-text');
    
    // Show loading state
    statusIcon.textContent = '⏳';
    statusText.textContent = 'Verifying...';
    
    try {
        const response = await fetch(`${API_BASE}/api/data/verify`);
        if (!response.ok) throw new Error('Verification failed');
        
        const results = await response.json();
        
        // Update status based on results
        if (results.status === 'healthy') {
            statusEl.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-900/20 text-green-400 cursor-pointer';
            statusIcon.textContent = '🟢';
            statusText.textContent = 'Data Healthy';
            showToast('Data verification passed', 'success');
        } else if (results.status === 'warning') {
            statusEl.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-900/20 text-yellow-400 cursor-pointer';
            statusIcon.textContent = '🟡';
            statusText.textContent = 'Minor Issues';
            showToast(`${results.issues.length} warnings found`, 'warning');
        } else {
            statusEl.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-900/20 text-red-400 cursor-pointer';
            statusIcon.textContent = '🔴';
            statusText.textContent = 'Issues Detected';
            showToast(`${results.issues.length} errors found`, 'error');
        }
        
        // Show detailed report if there are issues
        if (results.issues.length > 0) {
            const issuesList = results.issues.join('\n• ');
            alert(`Data Quality Issues:\n\n• ${issuesList}`);
        }
    } catch (error) {
        console.error('Error verifying data:', error);
        statusEl.className = 'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-900/20 text-red-400 cursor-pointer';
        statusIcon.textContent = '🔴';
        statusText.textContent = 'Verification Failed';
        showToast('Data verification failed', 'error');
    }
}

/**
 * Navigate to a page/URL
 */
function navigateTo(url) {
    // For now, just show alert since we're in SPA mode
    // In full implementation, this would handle routing
    console.log('Navigate to:', url);
    
    if (url.includes('analytics')) {
        showPage('analytics');
    } else if (url.includes('trades')) {
        showPage('trades');
    } else {
        showToast(`Navigation: ${url}`, 'info');
    }
}

// Initialize activity feed when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Start activity feed refresh
    setTimeout(startActivityRefresh, 1000);
    
    // Run initial data verification
    setTimeout(verifyDataQuality, 2000);
    
    // Initialize mobile features
    initializeMobileFeatures();
});

// ========================================================================
// MOBILE-SPECIFIC FEATURES
// ========================================================================

/**
 * Initialize mobile-specific features
 */
function initializeMobileFeatures() {
    // Only run on mobile devices
    if (!window.DeviceDetector || !window.DeviceDetector.isMobile()) {
        return;
    }
    
    console.log('Initializing mobile features...');
    
    // Setup pull-to-refresh
    setupPullToRefresh();
    
    // Setup haptic feedback
    setupHapticFeedback();
    
    // Initialize bottom nav active states
    updateBottomNavActiveState(currentPage);
}

/**
 * Toggle mobile menu (for "More" button in bottom nav)
 */
function toggleMobileMenu(event) {
    if (event) event.preventDefault();
    
    const menu = document.querySelector('.mobile-menu-overlay');
    const backdrop = document.querySelector('.mobile-menu-backdrop');
    const hamburger = document.querySelector('.hamburger-menu');
    
    if (menu) {
        const isActive = menu.classList.contains('active');
        
        if (isActive) {
            menu.classList.remove('active');
            if (backdrop) backdrop.classList.remove('active');
            if (hamburger) hamburger.classList.remove('active');
        } else {
            menu.classList.add('active');
            if (backdrop) backdrop.classList.add('active');
            if (hamburger) hamburger.classList.add('active');
        }
    }
}

/**
 * Update bottom navigation active state
 */
function updateBottomNavActiveState(pageName) {
    const bottomNavItems = document.querySelectorAll('.bottom-nav-item[data-page]');
    const menuItems = document.querySelectorAll('.mobile-menu-overlay a[data-page]');
    
    bottomNavItems.forEach(item => {
        const itemPage = item.getAttribute('data-page');
        if (itemPage === pageName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    menuItems.forEach(item => {
        const itemPage = item.getAttribute('data-page');
        if (itemPage === pageName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

/**
 * Setup pull-to-refresh functionality
 */
function setupPullToRefresh() {
    let startY = 0;
    let pulling = false;
    const threshold = 80;
    
    const container = document.querySelector('.main-content') || document.body;
    
    container.addEventListener('touchstart', (e) => {
        // Only trigger if at top of page
        if (container.scrollTop === 0) {
            startY = e.touches[0].pageY;
            pulling = true;
        }
    }, { passive: true });
    
    container.addEventListener('touchmove', (e) => {
        if (!pulling) return;
        
        // Track touch position for potential future UI feedback
        const currentY = e.touches[0].pageY;
    }, { passive: true });
    
    container.addEventListener('touchend', (e) => {
        if (!pulling) return;
        
        const currentY = e.changedTouches[0].pageY;
        const distance = currentY - startY;
        
        pulling = false;
        
        if (distance > threshold) {
            // Trigger refresh
            console.log('Pull-to-refresh triggered');
            refreshCurrentPage();
            
            // Show feedback
            showToast('Refreshing...', 'info');
            
            // Haptic feedback if available
            triggerHapticFeedback();
        }
    }, { passive: true });
}

/**
 * Setup haptic feedback for iOS
 */
function setupHapticFeedback() {
    // Add haptic feedback to buttons on mobile
    if (window.DeviceDetector && window.DeviceDetector.isIOS()) {
        const buttons = document.querySelectorAll('button, .clickable');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                triggerHapticFeedback('light');
            }, { passive: true });
        });
    }
}

/**
 * Trigger haptic feedback (iOS only)
 */
function triggerHapticFeedback(style = 'medium') {
    if (window.navigator && window.navigator.vibrate) {
        // Android vibration
        switch (style) {
            case 'light':
                window.navigator.vibrate(10);
                break;
            case 'medium':
                window.navigator.vibrate(20);
                break;
            case 'heavy':
                window.navigator.vibrate(30);
                break;
        }
    }
    
    // iOS haptic feedback (if available)
    if (window.Haptic && typeof window.Haptic.impact === 'function') {
        window.Haptic.impact(style);
    }
}

/**
 * Convert table to mobile card layout
 */
function convertTableToCards(tableSelector) {
    const table = document.querySelector(tableSelector);
    if (!table) return;
    
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    const rows = table.querySelectorAll('tbody tr');
    
    const cardList = document.createElement('div');
    cardList.className = 'mobile-card-list';
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const card = document.createElement('div');
        card.className = 'mobile-card';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'mobile-card-body';
        
        cells.forEach((cell, index) => {
            if (headers[index]) {
                const label = document.createElement('div');
                label.className = 'mobile-card-label';
                label.textContent = headers[index];
                
                const value = document.createElement('div');
                value.className = 'mobile-card-value';
                value.innerHTML = cell.innerHTML;
                
                cardBody.appendChild(label);
                cardBody.appendChild(value);
            }
        });
        
        card.appendChild(cardBody);
        cardList.appendChild(card);
    });
    
    // Insert cards after table
    table.parentNode.insertBefore(cardList, table.nextSibling);
}

/**
 * Enhanced showPage function with mobile support
 * Wraps the original showPage function if it exists, or creates a basic implementation
 */
function initializeMobilePageNavigation() {
    const originalShowPage = window.showPage;
    
    window.showPage = function(page, event) {
        // For mobile navigation, create a synthetic event if needed
        if (event && event.target && !event.target.closest('.nav-link')) {
            // Call original with a modified event that won't break desktop nav update
            if (typeof originalShowPage === 'function') {
                try {
                    // Hide all pages
                    document.querySelectorAll('.page-content').forEach(p => {
                        p.classList.add('hidden');
                    });
                    
                    // Show selected page
                    const targetPage = document.getElementById(`page-${page}`);
                    if (targetPage) {
                        targetPage.classList.remove('hidden');
                        targetPage.classList.add('slide-in');
                    }
                    
                    // Update desktop nav links if they exist
                    document.querySelectorAll('.nav-link').forEach(link => {
                        link.classList.remove('text-white', 'bg-gray-800');
                        link.classList.add('text-gray-300');
                    });
                    
                    currentPage = page;
                    
                    // Load page-specific data
                    if (page === 'trades') {
                        loadTradesData();
                    } else if (page === 'opportunities') {
                        loadOpportunitiesData();
                    } else if (page === 'analytics') {
                        loadAnalyticsData();
                    } else if (page === 'tax') {
                        loadTaxData();
                    } else if (page === 'settings') {
                        loadSettings();
                    }
                } catch (error) {
                    console.error('Error in page navigation:', error);
                }
            }
        } else {
            // Call original function for desktop navigation
            if (typeof originalShowPage === 'function') {
                originalShowPage.call(this, page, event);
            } else {
                // Basic fallback implementation
                currentPage = page;
            }
        }
        
        // Update mobile navigation
        updateBottomNavActiveState(page);
        
        // Close mobile menu if open
        const menu = document.querySelector('.mobile-menu-overlay');
        const backdrop = document.querySelector('.mobile-menu-backdrop');
        const hamburger = document.querySelector('.hamburger-menu');
        
        if (menu && menu.classList.contains('active')) {
            menu.classList.remove('active');
            if (backdrop) backdrop.classList.remove('active');
            if (hamburger) hamburger.classList.remove('active');
        }
        
        // Trigger haptic feedback
        triggerHapticFeedback('light');
        
        // Scroll to top on page change
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };
}

// Initialize mobile page navigation on load
document.addEventListener('DOMContentLoaded', function() {
    initializeMobilePageNavigation();
});
