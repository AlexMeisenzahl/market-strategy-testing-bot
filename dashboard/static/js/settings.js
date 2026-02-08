/**
 * Settings Manager
 * Handles all settings page functionality including tabs, themes, notifications, and API interactions
 */

class SettingsManager {
    // Default theme constant
    static DEFAULT_THEME = 'dark';
    
    constructor() {
        this.currentTab = 'notifications';
        this.currentTheme = SettingsManager.DEFAULT_THEME;
        this.currentTradingMode = 'paper';
        this.settings = {};
    }

    /**
     * Initialize the settings manager
     */
    async init() {
        console.log('Initializing SettingsManager...');
        
        // Setup event listeners
        this.setupTabSwitching();
        this.setupThemeSelector();
        this.setupTradingModeSelector();
        
        // Load saved theme from localStorage
        const savedTheme = localStorage.getItem('theme') || SettingsManager.DEFAULT_THEME;
        this.applyTheme(savedTheme);
        
        // Load settings from API
        await this.loadSettings();
        
        console.log('SettingsManager initialized');
    }

    /**
     * Setup tab switching functionality
     */
    setupTabSwitching() {
        const tabButtons = document.querySelectorAll('.tab-button');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
    }

    /**
     * Switch between tabs
     * @param {string} tabName - The name of the tab to switch to
     */
    switchTab(tabName) {
        // Update active tab button
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update active tab panel
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        this.currentTab = tabName;
    }

    /**
     * Setup theme selector buttons
     */
    setupThemeSelector() {
        const themeButtons = document.querySelectorAll('.theme-option');
        
        themeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const theme = button.getAttribute('data-theme');
                this.applyTheme(theme);
            });
        });
    }

    /**
     * Apply theme to the page
     * @param {string} theme - The theme to apply ('dark' or 'light')
     */
    applyTheme(theme) {
        // Update HTML data-theme attribute
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update active theme button
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-theme="${theme}"]`)?.classList.add('active');
        
        // Save to localStorage
        localStorage.setItem('theme', theme);
        
        this.currentTheme = theme;
        console.log(`Theme changed to: ${theme}`);
    }

    /**
     * Setup trading mode selector
     */
    setupTradingModeSelector() {
        const modeButtons = document.querySelectorAll('.mode-option');
        
        modeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const mode = button.getAttribute('data-mode');
                
                if (mode === 'live') {
                    // Show confirmation panel for live trading
                    document.getElementById('liveTradingConfirm').style.display = 'block';
                } else {
                    this.setTradingMode('paper');
                }
            });
        });
    }

    /**
     * Set trading mode
     * @param {string} mode - The trading mode ('paper' or 'live')
     */
    setTradingMode(mode) {
        // Update active mode button
        document.querySelectorAll('.mode-option').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-mode="${mode}"]`)?.classList.add('active');
        
        this.currentTradingMode = mode;
        
        // Hide confirmation panel if showing
        document.getElementById('liveTradingConfirm').style.display = 'none';
        
        // Reset checkbox
        const checkbox = document.getElementById('liveConfirmCheck');
        if (checkbox) checkbox.checked = false;
        
        const confirmBtn = document.getElementById('confirmLiveBtn');
        if (confirmBtn) confirmBtn.disabled = true;
        
        this.showNotification(
            `Trading mode set to ${mode === 'paper' ? 'Paper Trading' : 'Live Trading'}`,
            mode === 'live' ? 'warning' : 'success'
        );
        
        console.log(`Trading mode changed to: ${mode}`);
    }

    /**
     * Load settings from the API
     */
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            
            if (!response.ok) {
                // If settings don't exist, use defaults
                if (response.status === 404) {
                    console.log('No saved settings found, using defaults');
                    this.settings = this.getDefaultSettings();
                    return;
                }
                throw new Error(`Failed to load settings: ${response.statusText}`);
            }
            
            this.settings = await response.json();
            this.applySettingsToUI(this.settings);
            console.log('Settings loaded successfully');
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showNotification('Failed to load settings. Using defaults.', 'error');
            this.settings = this.getDefaultSettings();
        }
    }

    /**
     * Get default settings
     */
    getDefaultSettings() {
        return {
            notifications: {
                enabled: true,
                sound: true,
                channels: {
                    discord: { enabled: false, webhook: '' },
                    slack: { enabled: false, webhook: '' },
                    email: { enabled: false, address: '' },
                    telegram: { enabled: false, apiKey: '', chatId: '' },
                    webhook: { enabled: false, url: '' }
                },
                types: {},
                filters: {
                    minProfitThreshold: 0,
                    minConfidence: 70,
                    strategyFilter: ''
                }
            },
            display: {
                theme: SettingsManager.DEFAULT_THEME,
                timezone: 'UTC',
                currency: 'USD',
                dateFormat: 'YYYY-MM-DD',
                timeFormat: '24h',
                dashboard: {
                    defaultTimeframe: '24h',
                    refreshInterval: 30,
                    showNotifications: true
                }
            },
            strategies: {
                tradingMode: 'paper',
                requireConfirmation: false,
                enabled: {
                    arbitrage: true,
                    momentum: false,
                    reversion: false
                }
            },
            dataSources: {
                predictionMarkets: {
                    polymarket: { enabled: true, apiKey: '' },
                    predictit: { enabled: false, apiKey: '' },
                    kalshi: { enabled: false, apiKey: '' }
                },
                cryptoSources: {
                    coingecko: { enabled: true },
                    binance: { enabled: true },
                    coinbase: { enabled: false }
                }
            }
        };
    }

    /**
     * Apply loaded settings to the UI
     * @param {Object} settings - The settings object to apply
     */
    applySettingsToUI(settings) {
        // Notifications
        if (settings.notifications) {
            document.getElementById('enableNotifications').checked = settings.notifications.enabled ?? true;
            document.getElementById('notificationSound').checked = settings.notifications.sound ?? true;
            
            // Channels
            if (settings.notifications.channels) {
                const channels = settings.notifications.channels;
                
                if (channels.discord) {
                    document.getElementById('discordEnabled').checked = channels.discord.enabled ?? false;
                    document.getElementById('discordWebhook').value = channels.discord.webhook ?? '';
                }
                if (channels.slack) {
                    document.getElementById('slackEnabled').checked = channels.slack.enabled ?? false;
                    document.getElementById('slackWebhook').value = channels.slack.webhook ?? '';
                }
                if (channels.email) {
                    document.getElementById('emailEnabled').checked = channels.email.enabled ?? false;
                    document.getElementById('emailAddress').value = channels.email.address ?? '';
                }
                if (channels.telegram) {
                    document.getElementById('telegramEnabled').checked = channels.telegram.enabled ?? false;
                    document.getElementById('telegramApiKey').value = channels.telegram.apiKey ?? '';
                    document.getElementById('telegramChatId').value = channels.telegram.chatId ?? '';
                }
                if (channels.webhook) {
                    document.getElementById('webhookEnabled').checked = channels.webhook.enabled ?? false;
                    document.getElementById('webhookUrl').value = channels.webhook.url ?? '';
                }
            }
            
            // Notification types
            if (settings.notifications.types) {
                Object.keys(settings.notifications.types).forEach(type => {
                    const checkbox = document.getElementById(`notif-${type}`);
                    if (checkbox) {
                        checkbox.checked = settings.notifications.types[type];
                    }
                });
            }
            
            // Filters
            if (settings.notifications.filters) {
                document.getElementById('minProfitThreshold').value = settings.notifications.filters.minProfitThreshold ?? 0;
                document.getElementById('minConfidence').value = settings.notifications.filters.minConfidence ?? 70;
                document.getElementById('strategyFilter').value = settings.notifications.filters.strategyFilter ?? '';
            }
        }
        
        // Display
        if (settings.display) {
            if (settings.display.theme) {
                this.applyTheme(settings.display.theme);
            }
            document.getElementById('timezone').value = settings.display.timezone ?? 'UTC';
            document.getElementById('currency').value = settings.display.currency ?? 'USD';
            document.getElementById('dateFormat').value = settings.display.dateFormat ?? 'YYYY-MM-DD';
            document.getElementById('timeFormat').value = settings.display.timeFormat ?? '24h';
            
            if (settings.display.dashboard) {
                document.getElementById('defaultTimeframe').value = settings.display.dashboard.defaultTimeframe ?? '24h';
                document.getElementById('refreshInterval').value = settings.display.dashboard.refreshInterval ?? 30;
                document.getElementById('showNotifications').checked = settings.display.dashboard.showNotifications ?? true;
            }
        }
        
        // Strategies
        if (settings.strategies) {
            if (settings.strategies.tradingMode) {
                this.setTradingMode(settings.strategies.tradingMode);
            }
            document.getElementById('requireConfirmation').checked = settings.strategies.requireConfirmation ?? false;
            
            if (settings.strategies.enabled) {
                document.getElementById('strategy-arbitrage').checked = settings.strategies.enabled.arbitrage ?? true;
                document.getElementById('strategy-momentum').checked = settings.strategies.enabled.momentum ?? false;
                document.getElementById('strategy-reversion').checked = settings.strategies.enabled.reversion ?? false;
            }
        }
        
        // Data Sources
        if (settings.dataSources) {
            if (settings.dataSources.predictionMarkets) {
                const markets = settings.dataSources.predictionMarkets;
                
                if (markets.polymarket) {
                    document.getElementById('polymarket-enabled').checked = markets.polymarket.enabled ?? true;
                    document.getElementById('polymarket-api-key').value = markets.polymarket.apiKey ?? '';
                }
                if (markets.predictit) {
                    document.getElementById('predictit-enabled').checked = markets.predictit.enabled ?? false;
                    document.getElementById('predictit-api-key').value = markets.predictit.apiKey ?? '';
                }
                if (markets.kalshi) {
                    document.getElementById('kalshi-enabled').checked = markets.kalshi.enabled ?? false;
                    document.getElementById('kalshi-api-key').value = markets.kalshi.apiKey ?? '';
                }
            }
            
            if (settings.dataSources.cryptoSources) {
                const crypto = settings.dataSources.cryptoSources;
                
                document.getElementById('coingecko-enabled').checked = crypto.coingecko?.enabled ?? true;
                document.getElementById('binance-enabled').checked = crypto.binance?.enabled ?? true;
                document.getElementById('coinbase-enabled').checked = crypto.coinbase?.enabled ?? false;
            }
        }
    }

    /**
     * Save settings to the API
     */
    async saveSettings() {
        try {
            const settings = this.gatherSettings();
            
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save settings: ${response.statusText}`);
            }
            
            this.settings = settings;
            this.showNotification('Settings saved successfully!', 'success');
            console.log('Settings saved:', settings);
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showNotification('Failed to save settings. Please try again.', 'error');
        }
    }

    /**
     * Gather all settings from the UI
     * @returns {Object} The settings object
     */
    gatherSettings() {
        const settings = {
            notifications: {
                enabled: document.getElementById('enableNotifications').checked,
                sound: document.getElementById('notificationSound').checked,
                channels: {
                    discord: {
                        enabled: document.getElementById('discordEnabled').checked,
                        webhook: document.getElementById('discordWebhook').value
                    },
                    slack: {
                        enabled: document.getElementById('slackEnabled').checked,
                        webhook: document.getElementById('slackWebhook').value
                    },
                    email: {
                        enabled: document.getElementById('emailEnabled').checked,
                        address: document.getElementById('emailAddress').value
                    },
                    telegram: {
                        enabled: document.getElementById('telegramEnabled').checked,
                        apiKey: document.getElementById('telegramApiKey').value,
                        chatId: document.getElementById('telegramChatId').value
                    },
                    webhook: {
                        enabled: document.getElementById('webhookEnabled').checked,
                        url: document.getElementById('webhookUrl').value
                    }
                },
                types: {},
                filters: {
                    minProfitThreshold: parseFloat(document.getElementById('minProfitThreshold').value) || 0,
                    minConfidence: parseInt(document.getElementById('minConfidence').value) || 70,
                    strategyFilter: document.getElementById('strategyFilter').value
                }
            },
            display: {
                theme: this.currentTheme,
                timezone: document.getElementById('timezone').value,
                currency: document.getElementById('currency').value,
                dateFormat: document.getElementById('dateFormat').value,
                timeFormat: document.getElementById('timeFormat').value,
                dashboard: {
                    defaultTimeframe: document.getElementById('defaultTimeframe').value,
                    refreshInterval: parseInt(document.getElementById('refreshInterval').value),
                    showNotifications: document.getElementById('showNotifications').checked
                }
            },
            strategies: {
                tradingMode: this.currentTradingMode,
                requireConfirmation: document.getElementById('requireConfirmation').checked,
                enabled: {
                    arbitrage: document.getElementById('strategy-arbitrage').checked,
                    momentum: document.getElementById('strategy-momentum').checked,
                    reversion: document.getElementById('strategy-reversion').checked
                }
            },
            dataSources: {
                predictionMarkets: {
                    polymarket: {
                        enabled: document.getElementById('polymarket-enabled').checked,
                        apiKey: document.getElementById('polymarket-api-key').value
                    },
                    predictit: {
                        enabled: document.getElementById('predictit-enabled').checked,
                        apiKey: document.getElementById('predictit-api-key').value
                    },
                    kalshi: {
                        enabled: document.getElementById('kalshi-enabled').checked,
                        apiKey: document.getElementById('kalshi-api-key').value
                    }
                },
                cryptoSources: {
                    coingecko: {
                        enabled: document.getElementById('coingecko-enabled').checked
                    },
                    binance: {
                        enabled: document.getElementById('binance-enabled').checked
                    },
                    coinbase: {
                        enabled: document.getElementById('coinbase-enabled').checked
                    }
                }
            }
        };
        
        // Gather notification types
        const notificationCheckboxes = document.querySelectorAll('[id^="notif-"]');
        notificationCheckboxes.forEach(checkbox => {
            const type = checkbox.id.replace('notif-', '');
            settings.notifications.types[type] = checkbox.checked;
        });
        
        return settings;
    }

    /**
     * Show a notification toast
     * @param {string} message - The message to display
     * @param {string} type - The notification type ('success', 'error', 'warning', 'info')
     */
    showNotification(message, type = 'info') {
        const toast = document.getElementById('notificationToast');
        const toastBody = toast.querySelector('.toast-body');
        
        // Set message
        toastBody.textContent = message;
        
        // Set color based on type
        toast.className = 'toast';
        if (type === 'success') {
            toast.classList.add('bg-success', 'text-white');
        } else if (type === 'error') {
            toast.classList.add('bg-danger', 'text-white');
        } else if (type === 'warning') {
            toast.classList.add('bg-warning', 'text-dark');
        } else {
            toast.classList.add('bg-info', 'text-white');
        }
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

/**
 * Global function to save settings (called by Save button)
 */
async function saveSettings() {
    if (window.settingsManager) {
        await window.settingsManager.saveSettings();
    }
}

/**
 * Global function to reset settings (called by Reset button)
 */
async function resetSettings() {
    if (!confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/settings/reset', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to reset settings');
        }
        
        // Reload settings
        if (window.settingsManager) {
            await window.settingsManager.loadSettings();
        }
        
        window.settingsManager.showNotification('Settings reset to defaults', 'success');
    } catch (error) {
        console.error('Error resetting settings:', error);
        window.settingsManager.showNotification('Failed to reset settings', 'error');
    }
}

/**
 * Enable live trading (called by confirm button)
 */
function enableLiveTrading() {
    const checkbox = document.getElementById('liveConfirmCheck');
    
    if (!checkbox.checked) {
        alert('Please confirm that you understand the risks of live trading.');
        return;
    }
    
    // Double confirmation
    if (!confirm('FINAL CONFIRMATION: Are you absolutely sure you want to enable LIVE TRADING with REAL MONEY?')) {
        return;
    }
    
    if (window.settingsManager) {
        window.settingsManager.setTradingMode('live');
    }
}

/**
 * Test a notification channel
 * @param {string} channelType - The type of channel to test
 */
async function testChannel(channelType) {
    try {
        window.settingsManager.showNotification(`Testing ${channelType} channel...`, 'info');
        
        const response = await fetch(`/api/notifications/test/${channelType}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                webhook: document.getElementById(`${channelType}Webhook`)?.value,
                apiKey: document.getElementById(`${channelType}ApiKey`)?.value,
                chatId: document.getElementById(`${channelType}ChatId`)?.value,
                email: document.getElementById(`${channelType === 'email' ? 'emailAddress' : channelType}`)?.value,
                url: document.getElementById(`${channelType}Url`)?.value
            })
        });
        
        if (!response.ok) {
            throw new Error(`Test failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            window.settingsManager.showNotification(`${channelType} test successful!`, 'success');
        } else {
            window.settingsManager.showNotification(`${channelType} test failed: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error(`Error testing ${channelType}:`, error);
        window.settingsManager.showNotification(`Failed to test ${channelType} channel`, 'error');
    }
}
