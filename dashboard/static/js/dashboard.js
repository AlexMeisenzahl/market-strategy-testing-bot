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

// API Base URL
const API_BASE = window.location.origin;

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    loadOverviewData();
    loadBotStatus();
    
    // Auto-refresh every 10 seconds
    setInterval(() => {
        if (currentPage === 'overview') {
            loadOverviewData();
        }
        loadBotStatus();
    }, 10000);
});

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
        const response = await fetch(`${API_BASE}/api/overview`);
        const data = await response.json();
        
        // Update key metrics
        document.getElementById('total-pnl').textContent = formatCurrency(data.total_pnl);
        document.getElementById('total-pnl').className = data.total_pnl >= 0 ? 'text-3xl font-bold mb-1 text-profit' : 'text-3xl font-bold mb-1 text-loss';
        
        document.getElementById('pnl-change').textContent = (data.pnl_change_pct >= 0 ? '+' : '') + data.pnl_change_pct.toFixed(2) + '%';
        document.getElementById('pnl-change').className = data.pnl_change_pct >= 0 ? 'text-profit' : 'text-loss';
        
        document.getElementById('win-rate').textContent = data.win_rate.toFixed(1) + '%';
        document.getElementById('win-rate-bar').style.width = data.win_rate + '%';
        
        document.getElementById('active-trades').textContent = data.active_trades;
        document.getElementById('total-trades').textContent = data.total_trades;
        
        // Load charts
        loadCumulativePNLChart(currentTimeRange);
        loadDailyPNLChart();
        loadStrategyPerformance();
        loadRecentActivity();
        
    } catch (error) {
        console.error('Error loading overview data:', error);
        showToast('Error loading data', 'error');
    }
}

// Load Cumulative P&L Chart
async function loadCumulativePNLChart(timeRange) {
    try {
        const response = await fetch(`${API_BASE}/api/charts/cumulative-pnl?range=${timeRange}`);
        const data = await response.json();
        
        const ctx = document.getElementById('cumulative-pnl-chart');
        
        // Destroy existing chart
        if (cumulativePNLChart) {
            cumulativePNLChart.destroy();
        }
        
        // Prepare data
        const labels = data.data.map(d => new Date(d.timestamp).toLocaleDateString());
        const values = data.data.map(d => d.value);
        
        cumulativePNLChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Cumulative P&L',
                    data: values,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading cumulative P&L chart:', error);
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
        const response = await fetch(`${API_BASE}/api/charts/daily-pnl`);
        const data = await response.json();
        
        const ctx = document.getElementById('daily-pnl-chart');
        
        // Destroy existing chart
        if (dailyPNLChart) {
            dailyPNLChart.destroy();
        }
        
        // Prepare data
        const labels = data.data.map(d => new Date(d.date).toLocaleDateString());
        const values = data.data.map(d => d.pnl);
        const colors = data.data.map(d => d.pnl >= 0 ? '#10b981' : '#ef4444');
        
        dailyPNLChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Daily P&L',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading daily P&L chart:', error);
    }
}

// Load Strategy Performance Chart
async function loadStrategyPerformance() {
    try {
        const response = await fetch(`${API_BASE}/api/charts/strategy-performance`);
        const data = await response.json();
        
        const ctx = document.getElementById('strategy-performance-chart');
        
        // Destroy existing chart
        if (strategyChart) {
            strategyChart.destroy();
        }
        
        // Prepare data
        const labels = data.strategies.map(s => s.name);
        const values = data.strategies.map(s => s.pnl);
        const colors = values.map(v => v >= 0 ? '#10b981' : '#ef4444');
        
        strategyChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'P&L by Strategy',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(30, 41, 59, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: '#334155'
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading strategy performance:', error);
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
