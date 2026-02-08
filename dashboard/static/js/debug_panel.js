/**
 * Debug Panel - System Diagnostics
 * Displays logs, performance metrics, network requests, health status
 */

class DebugPanel {
    constructor() {
        this.isOpen = false;
        this.logs = [];
        this.maxLogs = 100;
        this.performanceMetrics = {};
        this.networkRequests = [];
        
        this.init();
    }
    
    init() {
        this.interceptConsole();
        this.collectPerformanceMetrics();
        this.monitorNetworkRequests();
        this.createUI();
        
        document.addEventListener('open-debug-panel', () => this.toggle());
        
        console.log('[Debug Panel] Initialized');
    }
    
    interceptConsole() {
        const originalLog = console.log;
        const originalError = console.error;
        const originalWarn = console.warn;
        const originalInfo = console.info;
        
        console.log = (...args) => {
            this.addLog('log', args);
            originalLog.apply(console, args);
        };
        
        console.error = (...args) => {
            this.addLog('error', args);
            originalError.apply(console, args);
        };
        
        console.warn = (...args) => {
            this.addLog('warn', args);
            originalWarn.apply(console, args);
        };
        
        console.info = (...args) => {
            this.addLog('info', args);
            originalInfo.apply(console, args);
        };
    }
    
    addLog(level, args) {
        const log = {
            level,
            message: args.map(arg => 
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' '),
            timestamp: new Date().toISOString()
        };
        
        this.logs.unshift(log);
        if (this.logs.length > this.maxLogs) {
            this.logs.pop();
        }
        
        if (this.isOpen) {
            this.renderLogs();
        }
    }
    
    collectPerformanceMetrics() {
        // Page load time
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            this.performanceMetrics.pageLoad = timing.loadEventEnd - timing.navigationStart;
            this.performanceMetrics.domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
        }
        
        // Memory usage (if available)
        if (performance.memory) {
            this.performanceMetrics.memory = {
                used: (performance.memory.usedJSHeapSize / 1048576).toFixed(2) + ' MB',
                total: (performance.memory.totalJSHeapSize / 1048576).toFixed(2) + ' MB',
                limit: (performance.memory.jsHeapSizeLimit / 1048576).toFixed(2) + ' MB'
            };
        }
        
        // FPS monitoring
        this.startFPSMonitoring();
    }
    
    startFPSMonitoring() {
        let lastTime = performance.now();
        let frames = 0;
        
        const measureFPS = () => {
            frames++;
            const currentTime = performance.now();
            if (currentTime >= lastTime + 1000) {
                this.performanceMetrics.fps = Math.round(frames * 1000 / (currentTime - lastTime));
                frames = 0;
                lastTime = currentTime;
            }
            requestAnimationFrame(measureFPS);
        };
        
        requestAnimationFrame(measureFPS);
    }
    
    monitorNetworkRequests() {
        // Intercept fetch
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const startTime = performance.now();
            const url = args[0];
            
            try {
                const response = await originalFetch(...args);
                const duration = performance.now() - startTime;
                
                this.networkRequests.unshift({
                    url,
                    method: args[1]?.method || 'GET',
                    status: response.status,
                    duration: Math.round(duration),
                    timestamp: new Date().toISOString()
                });
                
                if (this.networkRequests.length > 50) {
                    this.networkRequests.pop();
                }
                
                return response;
            } catch (error) {
                const duration = performance.now() - startTime;
                this.networkRequests.unshift({
                    url,
                    method: args[1]?.method || 'GET',
                    status: 'ERROR',
                    duration: Math.round(duration),
                    timestamp: new Date().toISOString(),
                    error: error.message
                });
                throw error;
            }
        };
    }
    
    async runHealthChecks() {
        const checks = {
            api: 'Checking...',
            database: 'Checking...',
            websocket: 'Checking...'
        };
        
        try {
            const response = await fetch('/api/health');
            if (response.ok) {
                const data = await response.json();
                return data;
            }
        } catch (e) {
            checks.api = '❌ Failed: ' + e.message;
        }
        
        return checks;
    }
    
    createUI() {
        const html = `
            <div id="debug-panel" class="debug-panel" style="display: none;">
                <div class="debug-header">
                    <h3>🐛 Debug Panel</h3>
                    <button class="debug-close" onclick="window.debugPanel.toggle()">✕</button>
                </div>
                <div class="debug-tabs">
                    <button class="debug-tab active" data-tab="logs">Logs</button>
                    <button class="debug-tab" data-tab="performance">Performance</button>
                    <button class="debug-tab" data-tab="network">Network</button>
                    <button class="debug-tab" data-tab="health">Health</button>
                    <button class="debug-tab" data-tab="storage">Storage</button>
                </div>
                <div class="debug-content">
                    <div class="debug-tab-content active" id="debug-logs"></div>
                    <div class="debug-tab-content" id="debug-performance"></div>
                    <div class="debug-tab-content" id="debug-network"></div>
                    <div class="debug-tab-content" id="debug-health"></div>
                    <div class="debug-tab-content" id="debug-storage"></div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', html);
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .debug-panel {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                height: 50vh;
                background: #1a1a1a;
                color: #fff;
                border-top: 2px solid #3b82f6;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                font-family: 'Courier New', monospace;
            }
            
            .debug-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 20px;
                background: #0a0a0a;
                border-bottom: 1px solid #333;
            }
            
            .debug-header h3 {
                margin: 0;
                font-size: 16px;
            }
            
            .debug-close {
                background: #ef4444;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            
            .debug-tabs {
                display: flex;
                gap: 4px;
                padding: 8px 20px;
                background: #0f0f0f;
                border-bottom: 1px solid #333;
            }
            
            .debug-tab {
                padding: 8px 16px;
                background: transparent;
                color: #999;
                border: none;
                cursor: pointer;
                border-radius: 4px 4px 0 0;
                transition: all 0.2s;
            }
            
            .debug-tab:hover {
                background: rgba(59, 130, 246, 0.1);
                color: #fff;
            }
            
            .debug-tab.active {
                background: #1a1a1a;
                color: #3b82f6;
            }
            
            .debug-content {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }
            
            .debug-tab-content {
                display: none;
            }
            
            .debug-tab-content.active {
                display: block;
            }
            
            .debug-log-entry {
                padding: 8px;
                margin-bottom: 4px;
                border-left: 3px solid #666;
                font-size: 12px;
                white-space: pre-wrap;
                word-break: break-all;
            }
            
            .debug-log-entry.log {
                border-left-color: #3b82f6;
            }
            
            .debug-log-entry.error {
                border-left-color: #ef4444;
                background: rgba(239, 68, 68, 0.1);
            }
            
            .debug-log-entry.warn {
                border-left-color: #f59e0b;
                background: rgba(245, 158, 11, 0.1);
            }
            
            .debug-log-entry.info {
                border-left-color: #10b981;
            }
            
            .debug-metric {
                margin-bottom: 16px;
            }
            
            .debug-metric-label {
                font-weight: bold;
                color: #3b82f6;
                margin-bottom: 4px;
            }
            
            .debug-metric-value {
                font-size: 14px;
            }
        `;
        document.head.appendChild(style);
        
        // Tab switching
        document.querySelectorAll('.debug-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.debug-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.debug-tab-content').forEach(c => c.classList.remove('active'));
                
                tab.classList.add('active');
                const contentId = 'debug-' + tab.dataset.tab;
                document.getElementById(contentId).classList.add('active');
                
                this.renderTab(tab.dataset.tab);
            });
        });
    }
    
    toggle() {
        const panel = document.getElementById('debug-panel');
        this.isOpen = !this.isOpen;
        panel.style.display = this.isOpen ? 'flex' : 'none';
        
        if (this.isOpen) {
            this.renderTab('logs');
        }
    }
    
    renderTab(tab) {
        switch (tab) {
            case 'logs':
                this.renderLogs();
                break;
            case 'performance':
                this.renderPerformance();
                break;
            case 'network':
                this.renderNetwork();
                break;
            case 'health':
                this.renderHealth();
                break;
            case 'storage':
                this.renderStorage();
                break;
        }
    }
    
    renderLogs() {
        const container = document.getElementById('debug-logs');
        if (this.logs.length === 0) {
            container.innerHTML = '<p style="color: #666;">No logs yet</p>';
            return;
        }
        
        container.innerHTML = this.logs.map(log => `
            <div class="debug-log-entry ${log.level}">
                <span style="color: #666;">${log.timestamp}</span> 
                <span style="color: ${this.getLogColor(log.level)};">[${log.level.toUpperCase()}]</span> 
                ${log.message}
            </div>
        `).join('');
    }
    
    getLogColor(level) {
        const colors = {
            log: '#3b82f6',
            error: '#ef4444',
            warn: '#f59e0b',
            info: '#10b981'
        };
        return colors[level] || '#999';
    }
    
    renderPerformance() {
        const container = document.getElementById('debug-performance');
        container.innerHTML = `
            <div class="debug-metric">
                <div class="debug-metric-label">Page Load Time</div>
                <div class="debug-metric-value">${this.performanceMetrics.pageLoad || 'N/A'} ms</div>
            </div>
            <div class="debug-metric">
                <div class="debug-metric-label">DOM Ready</div>
                <div class="debug-metric-value">${this.performanceMetrics.domReady || 'N/A'} ms</div>
            </div>
            <div class="debug-metric">
                <div class="debug-metric-label">Current FPS</div>
                <div class="debug-metric-value">${this.performanceMetrics.fps || 'Calculating...'}</div>
            </div>
            ${this.performanceMetrics.memory ? `
                <div class="debug-metric">
                    <div class="debug-metric-label">Memory Usage</div>
                    <div class="debug-metric-value">
                        Used: ${this.performanceMetrics.memory.used}<br>
                        Total: ${this.performanceMetrics.memory.total}<br>
                        Limit: ${this.performanceMetrics.memory.limit}
                    </div>
                </div>
            ` : ''}
        `;
    }
    
    renderNetwork() {
        const container = document.getElementById('debug-network');
        if (this.networkRequests.length === 0) {
            container.innerHTML = '<p style="color: #666;">No network requests yet</p>';
            return;
        }
        
        container.innerHTML = this.networkRequests.map(req => `
            <div style="padding: 12px; background: rgba(255,255,255,0.05); margin-bottom: 8px; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: ${req.status === 200 ? '#10b981' : '#ef4444'};">${req.method} ${req.status}</span>
                    <span style="color: #666;">${req.duration}ms</span>
                </div>
                <div style="font-size: 12px; color: #999; word-break: break-all;">${req.url}</div>
                ${req.error ? `<div style="color: #ef4444; font-size: 12px; margin-top: 4px;">${req.error}</div>` : ''}
            </div>
        `).join('');
    }
    
    async renderHealth() {
        const container = document.getElementById('debug-health');
        container.innerHTML = '<p style="color: #666;">Running health checks...</p>';
        
        const health = await this.runHealthChecks();
        
        container.innerHTML = Object.entries(health).map(([key, value]) => `
            <div class="debug-metric">
                <div class="debug-metric-label">${key}</div>
                <div class="debug-metric-value">${JSON.stringify(value, null, 2)}</div>
            </div>
        `).join('');
    }
    
    renderStorage() {
        const container = document.getElementById('debug-storage');
        
        // LocalStorage
        let localStorageSize = 0;
        for (let key in localStorage) {
            if (localStorage.hasOwnProperty(key)) {
                localStorageSize += localStorage[key].length;
            }
        }
        
        container.innerHTML = `
            <div class="debug-metric">
                <div class="debug-metric-label">LocalStorage</div>
                <div class="debug-metric-value">
                    Size: ${(localStorageSize / 1024).toFixed(2)} KB<br>
                    Items: ${localStorage.length}
                </div>
            </div>
            <div class="debug-metric">
                <div class="debug-metric-label">SessionStorage</div>
                <div class="debug-metric-value">Items: ${sessionStorage.length}</div>
            </div>
            <div class="debug-metric">
                <div class="debug-metric-label">Cookies</div>
                <div class="debug-metric-value">${document.cookie ? document.cookie.split(';').length : 0} cookies</div>
            </div>
        `;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.debugPanel = new DebugPanel();
});
