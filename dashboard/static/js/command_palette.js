/**
 * Universal Command Palette (Cmd+K / Ctrl+K)
 * Like VS Code's command palette with fuzzy search
 */

class CommandPalette {
    constructor() {
        this.commands = [];
        this.filteredCommands = [];
        this.selectedIndex = 0;
        this.isOpen = false;
        this.container = null;
        
        this.defineCommands();
        this.createUI();
        this.attachEventListeners();
    }
    
    defineCommands() {
        // Navigation commands
        this.commands.push(
            { id: 'go-dashboard', label: '🏠 Go to Dashboard', action: () => window.location.href = '/', category: 'Navigation' },
            { id: 'go-analytics', label: '📈 Go to Analytics', action: () => window.location.href = '/analytics', category: 'Navigation' },
            { id: 'go-markets', label: '💼 Go to Markets', action: () => window.location.href = '/markets', category: 'Navigation' },
            { id: 'go-settings', label: '⚙️ Go to Settings', action: () => window.location.href = '/settings', category: 'Navigation' },
            { id: 'go-crypto', label: '₿ Go to Crypto Charts', action: () => window.location.href = '/crypto-charts', category: 'Navigation' }
        );
        
        // Action commands
        this.commands.push(
            { id: 'refresh-data', label: '🔄 Refresh Data', action: () => this.refreshData(), category: 'Actions' },
            { id: 'export-data', label: '📥 Export Data as CSV', action: () => this.exportData(), category: 'Actions' },
            { id: 'export-json', label: '📄 Export Data as JSON', action: () => this.exportJSON(), category: 'Actions' },
            { id: 'clear-cache', label: '🗑️ Clear Cache', action: () => this.clearCache(), category: 'Actions' },
            { id: 'new-trade', label: '➕ New Trade', action: () => this.newTrade(), category: 'Actions' }
        );
        
        // View commands
        this.commands.push(
            { id: 'toggle-theme', label: '🌓 Toggle Dark/Light Theme', action: () => this.toggleTheme(), category: 'Views' },
            { id: 'toggle-fullscreen', label: '⛶ Toggle Fullscreen', action: () => this.toggleFullscreen(), category: 'Views' },
            { id: 'zoom-in', label: '🔍 Zoom In', action: () => this.zoomIn(), category: 'Views' },
            { id: 'zoom-out', label: '🔍 Zoom Out', action: () => this.zoomOut(), category: 'Views' },
            { id: 'zoom-reset', label: '↺ Reset Zoom', action: () => this.zoomReset(), category: 'Views' }
        );
        
        // Filter commands
        this.commands.push(
            { id: 'filter-profitable', label: '💰 Show Only Profitable', action: () => this.filterProfitable(), category: 'Filters' },
            { id: 'filter-today', label: '📅 Show Today Only', action: () => this.filterToday(), category: 'Filters' },
            { id: 'filter-this-week', label: '📅 Show This Week', action: () => this.filterThisWeek(), category: 'Filters' },
            { id: 'clear-filters', label: '✖️ Clear All Filters', action: () => this.clearFilters(), category: 'Filters' }
        );
        
        // Notification commands
        this.commands.push(
            { id: 'open-notifications', label: '🔔 Open Notifications', action: () => this.openNotifications(), category: 'Notifications' },
            { id: 'mark-read', label: '✓ Mark All Read', action: () => this.markAllRead(), category: 'Notifications' },
            { id: 'clear-notifications', label: '🗑️ Clear Notifications', action: () => this.clearNotifications(), category: 'Notifications' }
        );
        
        // System commands
        this.commands.push(
            { id: 'debug-panel', label: '🐛 Open Debug Panel', action: () => this.openDebugPanel(), category: 'System' },
            { id: 'view-logs', label: '📋 View System Logs', action: () => this.viewLogs(), category: 'System' },
            { id: 'health-check', label: '❤️ Run Health Check', action: () => this.healthCheck(), category: 'System' },
            { id: 'connection-status', label: '🌐 Check Connection Status', action: () => this.checkConnection(), category: 'System' }
        );
        
        // Help commands
        this.commands.push(
            { id: 'show-shortcuts', label: '⌨️ Show Keyboard Shortcuts', action: () => this.showShortcuts(), category: 'Help' },
            { id: 'show-help', label: '❓ Show Help', action: () => this.showHelp(), category: 'Help' },
            { id: 'show-onboarding', label: '🎓 Start Onboarding Tutorial', action: () => this.startOnboarding(), category: 'Help' },
            { id: 'documentation', label: '📚 Open Documentation', action: () => this.openDocs(), category: 'Help' }
        );
        
        // Strategy commands
        this.commands.push(
            { id: 'enable-all-strategies', label: '✓ Enable All Strategies', action: () => this.enableAllStrategies(), category: 'Strategies' },
            { id: 'disable-all-strategies', label: '✖️ Disable All Strategies', action: () => this.disableAllStrategies(), category: 'Strategies' }
        );
        
        // Trading mode commands
        this.commands.push(
            { id: 'switch-paper', label: '📝 Switch to Paper Trading', action: () => this.switchToPaper(), category: 'Trading' },
            { id: 'switch-live', label: '🔴 Switch to Live Trading', action: () => this.switchToLive(), category: 'Trading' }
        );
        
        // Workspace commands
        this.commands.push(
            { id: 'workspace-1', label: '📊 Switch to Workspace 1', action: () => this.switchWorkspace(1), category: 'Workspaces' },
            { id: 'workspace-2', label: '📈 Switch to Workspace 2', action: () => this.switchWorkspace(2), category: 'Workspaces' },
            { id: 'workspace-3', label: '💼 Switch to Workspace 3', action: () => this.switchWorkspace(3), category: 'Workspaces' },
            { id: 'create-workspace', label: '➕ Create New Workspace', action: () => this.createWorkspace(), category: 'Workspaces' }
        );
        
        // Bookmark commands
        this.commands.push(
            { id: 'show-bookmarks', label: '⭐ Show Bookmarks', action: () => this.showBookmarks(), category: 'Bookmarks' },
            { id: 'bookmark-current', label: '⭐ Bookmark Current Page', action: () => this.bookmarkCurrent(), category: 'Bookmarks' }
        );
        
        console.log('[Command Palette] Loaded', this.commands.length, 'commands');
    }
    
    createUI() {
        const html = `
            <div class="command-palette" id="command-palette" style="display: none;">
                <div class="command-palette-backdrop"></div>
                <div class="command-palette-container">
                    <input 
                        type="text" 
                        id="command-palette-input" 
                        placeholder="Type a command or search..."
                        autocomplete="off"
                    >
                    <div class="command-palette-results" id="command-palette-results"></div>
                    <div class="command-palette-footer">
                        <span>↑↓ Navigate</span>
                        <span>↵ Execute</span>
                        <span>Esc Close</span>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', html);
        this.container = document.getElementById('command-palette');
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .command-palette {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 10000;
            }
            
            .command-palette-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
            }
            
            .command-palette-container {
                position: absolute;
                top: 20%;
                left: 50%;
                transform: translateX(-50%);
                width: 90%;
                max-width: 600px;
                background: var(--dark-card, #1e293b);
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                overflow: hidden;
            }
            
            .command-palette-container input {
                width: 100%;
                padding: 20px 24px;
                border: none;
                background: transparent;
                color: white;
                font-size: 18px;
                outline: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .command-palette-container input::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
            
            .command-palette-results {
                max-height: 400px;
                overflow-y: auto;
                padding: 8px 0;
            }
            
            .command-item {
                padding: 12px 24px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 12px;
                color: white;
                transition: background 0.2s;
            }
            
            .command-item:hover,
            .command-item.selected {
                background: rgba(59, 130, 246, 0.3);
            }
            
            .command-item .command-category {
                margin-left: auto;
                font-size: 12px;
                color: rgba(255, 255, 255, 0.5);
                text-transform: uppercase;
            }
            
            .command-palette-footer {
                padding: 12px 24px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                gap: 24px;
                font-size: 12px;
                color: rgba(255, 255, 255, 0.5);
            }
            
            @media (max-width: 767px) {
                .command-palette-container {
                    top: 10%;
                    width: 95%;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    attachEventListeners() {
        // Open command palette
        document.addEventListener('open-command-palette', () => this.open());
        
        // Input handling
        const input = document.getElementById('command-palette-input');
        input.addEventListener('input', (e) => this.handleInput(e.target.value));
        input.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Close on backdrop click
        this.container.querySelector('.command-palette-backdrop').addEventListener('click', () => this.close());
    }
    
    open() {
        this.isOpen = true;
        this.container.style.display = 'block';
        document.getElementById('command-palette-input').value = '';
        document.getElementById('command-palette-input').focus();
        this.filteredCommands = [...this.commands];
        this.selectedIndex = 0;
        this.render();
    }
    
    close() {
        this.isOpen = false;
        this.container.style.display = 'none';
    }
    
    handleInput(query) {
        if (!query.trim()) {
            this.filteredCommands = [...this.commands];
        } else {
            this.filteredCommands = this.fuzzySearch(query);
        }
        this.selectedIndex = 0;
        this.render();
    }
    
    fuzzySearch(query) {
        const lowerQuery = query.toLowerCase();
        return this.commands.filter(cmd => {
            const label = cmd.label.toLowerCase();
            const category = cmd.category.toLowerCase();
            return label.includes(lowerQuery) || category.includes(lowerQuery);
        }).sort((a, b) => {
            const aIndex = a.label.toLowerCase().indexOf(lowerQuery);
            const bIndex = b.label.toLowerCase().indexOf(lowerQuery);
            return aIndex - bIndex;
        });
    }
    
    handleKeyDown(e) {
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredCommands.length - 1);
                this.render();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.render();
                break;
            case 'Enter':
                e.preventDefault();
                this.executeCommand(this.selectedIndex);
                break;
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
        }
    }
    
    render() {
        const resultsContainer = document.getElementById('command-palette-results');
        
        if (this.filteredCommands.length === 0) {
            resultsContainer.innerHTML = '<div style="padding: 24px; text-align: center; color: rgba(255,255,255,0.5);">No commands found</div>';
            return;
        }
        
        resultsContainer.innerHTML = this.filteredCommands.map((cmd, index) => `
            <div class="command-item ${index === this.selectedIndex ? 'selected' : ''}" 
                 data-index="${index}"
                 onclick="window.commandPalette.executeCommand(${index})">
                <span>${cmd.label}</span>
                <span class="command-category">${cmd.category}</span>
            </div>
        `).join('');
        
        // Scroll selected item into view
        const selected = resultsContainer.querySelector('.command-item.selected');
        if (selected) {
            selected.scrollIntoView({ block: 'nearest' });
        }
    }
    
    executeCommand(index) {
        if (index >= 0 && index < this.filteredCommands.length) {
            const cmd = this.filteredCommands[index];
            console.log('[Command Palette] Executing:', cmd.label);
            this.close();
            cmd.action();
        }
    }
    
    // Command action implementations
    refreshData() {
        if (typeof window.refreshDashboard === 'function') {
            window.refreshDashboard();
        } else {
            window.location.reload();
        }
    }
    
    exportData() {
        const event = new CustomEvent('export-data', { detail: { format: 'csv' } });
        document.dispatchEvent(event);
    }
    
    exportJSON() {
        const event = new CustomEvent('export-data', { detail: { format: 'json' } });
        document.dispatchEvent(event);
    }
    
    clearCache() {
        localStorage.clear();
        sessionStorage.clear();
        alert('Cache cleared!');
    }
    
    newTrade() {
        alert('New trade modal would open here');
    }
    
    toggleTheme() {
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
    
    zoomIn() {
        document.body.style.zoom = (parseFloat(document.body.style.zoom || 1) + 0.1);
    }
    
    zoomOut() {
        document.body.style.zoom = (parseFloat(document.body.style.zoom || 1) - 0.1);
    }
    
    zoomReset() {
        document.body.style.zoom = 1;
    }
    
    filterProfitable() {
        const event = new CustomEvent('apply-filter', { detail: { type: 'profitable' } });
        document.dispatchEvent(event);
    }
    
    filterToday() {
        const event = new CustomEvent('apply-filter', { detail: { type: 'today' } });
        document.dispatchEvent(event);
    }
    
    filterThisWeek() {
        const event = new CustomEvent('apply-filter', { detail: { type: 'week' } });
        document.dispatchEvent(event);
    }
    
    clearFilters() {
        const event = new CustomEvent('clear-filters');
        document.dispatchEvent(event);
    }
    
    openNotifications() {
        const event = new CustomEvent('show-notifications');
        document.dispatchEvent(event);
    }
    
    markAllRead() {
        const event = new CustomEvent('mark-all-read');
        document.dispatchEvent(event);
    }
    
    clearNotifications() {
        const event = new CustomEvent('clear-notifications');
        document.dispatchEvent(event);
    }
    
    openDebugPanel() {
        const event = new CustomEvent('open-debug-panel');
        document.dispatchEvent(event);
    }
    
    viewLogs() {
        window.open('/api/logs', '_blank');
    }
    
    healthCheck() {
        fetch('/api/health')
            .then(r => r.json())
            .then(data => alert('Health Check: ' + JSON.stringify(data, null, 2)))
            .catch(e => alert('Health check failed: ' + e));
    }
    
    checkConnection() {
        const event = new CustomEvent('check-connection');
        document.dispatchEvent(event);
    }
    
    showShortcuts() {
        if (window.keyboardShortcuts) {
            window.keyboardShortcuts.showShortcutGuide();
        }
    }
    
    showHelp() {
        const event = new CustomEvent('show-help');
        document.dispatchEvent(event);
    }
    
    startOnboarding() {
        const event = new CustomEvent('start-onboarding');
        document.dispatchEvent(event);
    }
    
    openDocs() {
        window.open('https://github.com/AlexMeisenzahl/market-strategy-testing-bot', '_blank');
    }
    
    enableAllStrategies() {
        alert('Enable all strategies action');
    }
    
    disableAllStrategies() {
        alert('Disable all strategies action');
    }
    
    switchToPaper() {
        alert('Switch to paper trading mode');
    }
    
    switchToLive() {
        if (confirm('Switch to LIVE trading? This will use real funds!')) {
            alert('Switching to live trading...');
        }
    }
    
    switchWorkspace(num) {
        const event = new CustomEvent('switch-workspace', { detail: { workspace: num } });
        document.dispatchEvent(event);
    }
    
    createWorkspace() {
        const name = prompt('Enter workspace name:');
        if (name) {
            const event = new CustomEvent('create-workspace', { detail: { name } });
            document.dispatchEvent(event);
        }
    }
    
    showBookmarks() {
        const event = new CustomEvent('show-bookmarks');
        document.dispatchEvent(event);
    }
    
    bookmarkCurrent() {
        const event = new CustomEvent('bookmark-page', { detail: { url: window.location.href } });
        document.dispatchEvent(event);
        alert('Page bookmarked!');
    }
}

// Initialize command palette
document.addEventListener('DOMContentLoaded', () => {
    window.commandPalette = new CommandPalette();
    console.log('[Command Palette] Ready');
});
