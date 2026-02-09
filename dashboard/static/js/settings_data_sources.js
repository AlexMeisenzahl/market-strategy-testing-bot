/**
 * Data Sources Settings Manager
 * 
 * Manages configuration of data sources (Polymarket, CoinGecko, Telegram, Email)
 * with encrypted credential storage and connection testing.
 */

class DataSourcesSettings {
    constructor() {
        this.apiEndpoint = '/api/settings';
        this.currentMode = 'mock';
    }

    /**
     * Initialize the data sources settings
     */
    async init() {
        console.log('Initializing Data Sources Settings...');
        await this.loadSettings();
        this.attachEventListeners();
        await this.updateDataMode();
    }

    /**
     * Load current settings from API
     */
    async loadSettings() {
        try {
            const response = await fetch(`${this.apiEndpoint}/data-sources`);
            const data = await response.json();
            
            if (data.success) {
                this.populateForm(data);
                this.currentMode = data.data_mode;
                this.updateDataModeIndicator(data.data_mode);
            } else {
                console.error('Failed to load settings:', data.error);
                this.showToast('error', 'Failed to load settings');
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showToast('error', 'Error connecting to server');
        }
    }

    /**
     * Populate form with loaded settings
     */
    populateForm(data) {
        // Polymarket
        if (data.polymarket) {
            document.getElementById('polymarket-endpoint').value = data.polymarket.endpoint || '';
            document.getElementById('polymarket-api-key').value = data.polymarket.api_key || '';
        }

        // Crypto
        if (data.crypto) {
            document.getElementById('crypto-provider').value = data.crypto.provider || 'coingecko';
            document.getElementById('crypto-endpoint').value = data.crypto.endpoint || '';
            document.getElementById('crypto-api-key').value = data.crypto.api_key || '';
        }

        // Telegram
        if (data.telegram) {
            document.getElementById('telegram-bot-token').value = data.telegram.bot_token || '';
            document.getElementById('telegram-chat-id').value = data.telegram.chat_id || '';
        }

        // Email
        if (data.email) {
            document.getElementById('email-smtp-server').value = data.email.smtp_server || '';
            document.getElementById('email-smtp-port').value = data.email.smtp_port || 587;
            document.getElementById('email-username').value = data.email.username || '';
            document.getElementById('email-password').value = data.email.password || '';
        }
    }

    /**
     * Attach event listeners to buttons
     */
    attachEventListeners() {
        // Save buttons
        document.getElementById('save-polymarket-btn')?.addEventListener('click', () => this.saveSettings('polymarket'));
        document.getElementById('save-crypto-btn')?.addEventListener('click', () => this.saveSettings('crypto'));
        document.getElementById('save-telegram-btn')?.addEventListener('click', () => this.saveSettings('telegram'));
        document.getElementById('save-email-btn')?.addEventListener('click', () => this.saveSettings('email'));

        // Test connection buttons
        document.getElementById('test-polymarket-btn')?.addEventListener('click', () => this.testConnection('polymarket'));
        document.getElementById('test-crypto-btn')?.addEventListener('click', () => this.testConnection('crypto'));
        document.getElementById('test-telegram-btn')?.addEventListener('click', () => this.testConnection('telegram'));
        document.getElementById('test-email-btn')?.addEventListener('click', () => this.testConnection('email'));
    }

    /**
     * Save settings for a service
     */
    async saveSettings(service) {
        let credentials = {};

        // Gather credentials based on service
        if (service === 'polymarket') {
            credentials = {
                endpoint: document.getElementById('polymarket-endpoint').value,
                api_key: document.getElementById('polymarket-api-key').value
            };
        } else if (service === 'crypto') {
            credentials = {
                provider: document.getElementById('crypto-provider').value,
                endpoint: document.getElementById('crypto-endpoint').value,
                api_key: document.getElementById('crypto-api-key').value
            };
        } else if (service === 'telegram') {
            credentials = {
                bot_token: document.getElementById('telegram-bot-token').value,
                chat_id: document.getElementById('telegram-chat-id').value
            };
        } else if (service === 'email') {
            credentials = {
                smtp_server: document.getElementById('email-smtp-server').value,
                smtp_port: parseInt(document.getElementById('email-smtp-port').value) || 587,
                username: document.getElementById('email-username').value,
                password: document.getElementById('email-password').value
            };
        }

        // Show loading state
        const button = document.getElementById(`save-${service}-btn`);
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Saving...';

        try {
            const response = await fetch(`${this.apiEndpoint}/data-sources`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    service: service,
                    credentials: credentials
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('success', data.message);
                this.updateStatus(service, 'saved');
                
                // Update data mode if changed
                if (data.data_mode) {
                    this.currentMode = data.data_mode;
                    this.updateDataModeIndicator(data.data_mode);
                }
            } else {
                this.showToast('error', data.error || 'Failed to save settings');
                this.updateStatus(service, 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            this.showToast('error', 'Error connecting to server');
            this.updateStatus(service, 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    /**
     * Test connection to a service
     */
    async testConnection(service) {
        // Show loading state
        const button = document.getElementById(`test-${service}-btn`);
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="bi bi-hourglass-split"></i> Testing...';

        // Update status to testing
        this.updateStatus(service, 'testing');

        try {
            const response = await fetch(`${this.apiEndpoint}/test-connection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ service: service })
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('success', data.message);
                this.updateStatus(service, 'connected');
            } else {
                this.showToast('error', data.error || 'Connection test failed');
                this.updateStatus(service, 'error');
            }
        } catch (error) {
            console.error('Error testing connection:', error);
            this.showToast('error', 'Error connecting to server');
            this.updateStatus(service, 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    /**
     * Update data mode indicator
     */
    async updateDataMode() {
        try {
            const response = await fetch(`${this.apiEndpoint}/data-mode`);
            const result = await response.json();
            
            if (result.success) {
                this.currentMode = result.data.mode;
                this.updateDataModeIndicator(result.data.mode);
            }
        } catch (error) {
            console.error('Error fetching data mode:', error);
        }
    }

    /**
     * Update the data mode indicator in the UI
     */
    updateDataModeIndicator(mode) {
        const indicator = document.getElementById('data-mode-indicator');
        if (!indicator) return;

        if (mode === 'live') {
            indicator.innerHTML = '<span class="badge bg-success"><i class="bi bi-circle-fill"></i> LIVE DATA</span>';
        } else {
            indicator.innerHTML = '<span class="badge bg-warning"><i class="bi bi-circle-fill"></i> MOCK DATA</span>';
        }
    }

    /**
     * Update status indicator for a service
     */
    updateStatus(service, status) {
        const statusElement = document.getElementById(`${service}-status`);
        if (!statusElement) return;

        switch (status) {
            case 'connected':
                statusElement.innerHTML = '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Connected</span>';
                break;
            case 'error':
                statusElement.innerHTML = '<span class="badge bg-danger"><i class="bi bi-x-circle"></i> Error</span>';
                break;
            case 'testing':
                statusElement.innerHTML = '<span class="badge bg-info"><i class="bi bi-hourglass-split"></i> Testing...</span>';
                break;
            case 'saved':
                statusElement.innerHTML = '<span class="badge bg-primary"><i class="bi bi-check-circle"></i> Saved</span>';
                break;
            case 'not-configured':
                statusElement.innerHTML = '<span class="badge bg-secondary"><i class="bi bi-exclamation-triangle"></i> Not Configured</span>';
                break;
            default:
                statusElement.innerHTML = '<span class="badge bg-secondary">Unknown</span>';
        }
    }

    /**
     * Show toast notification
     */
    showToast(type, message) {
        // Create toast element if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        const toastId = 'toast-' + Date.now();
        const icon = type === 'success' ? 'check-circle' : 'exclamation-circle';
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';

        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert">
                <div class="toast-header ${bgClass} text-white">
                    <i class="bi bi-${icon} me-2"></i>
                    <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);

        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();

        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.dataSourcesSettings = new DataSourcesSettings();
        window.dataSourcesSettings.init();
    });
} else {
    window.dataSourcesSettings = new DataSourcesSettings();
    window.dataSourcesSettings.init();
}
