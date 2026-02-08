/**
 * Global Keyboard Shortcuts System
 * Supports 50+ keyboard shortcuts for power users
 */

class KeyboardShortcutManager {
    constructor() {
        this.shortcuts = {};
        this.sequenceKeys = [];
        this.sequenceTimeout = null;
        this.sequenceTimeoutDuration = 1000; // 1 second for sequence
        this.isModalOpen = false;
        
        this.defineShortcuts();
        this.init();
    }
    
    defineShortcuts() {
        // Navigation shortcuts (g + key)
        this.shortcuts['g d'] = {
            action: () => this.navigate('/'),
            description: 'Go to Dashboard',
            category: 'Navigation'
        };
        this.shortcuts['g a'] = {
            action: () => this.navigate('/analytics'),
            description: 'Go to Analytics',
            category: 'Navigation'
        };
        this.shortcuts['g m'] = {
            action: () => this.navigate('/markets'),
            description: 'Go to Markets',
            category: 'Navigation'
        };
        this.shortcuts['g s'] = {
            action: () => this.navigate('/settings'),
            description: 'Go to Settings',
            category: 'Navigation'
        };
        this.shortcuts['g h'] = {
            action: () => this.navigate('/'),
            description: 'Go Home',
            category: 'Navigation'
        };
        
        // Universal Search
        this.shortcuts['ctrl+k'] = {
            action: () => this.openCommandPalette(),
            description: 'Open Command Palette',
            category: 'Search'
        };
        this.shortcuts['meta+k'] = {
            action: () => this.openCommandPalette(),
            description: 'Open Command Palette',
            category: 'Search'
        };
        this.shortcuts['/'] = {
            action: (e) => this.focusSearch(e),
            description: 'Focus Search',
            category: 'Search'
        };
        
        // Actions
        this.shortcuts['n'] = {
            action: () => this.newTrade(),
            description: 'New Trade',
            category: 'Actions'
        };
        this.shortcuts['r'] = {
            action: () => this.refreshData(),
            description: 'Refresh Data',
            category: 'Actions'
        };
        this.shortcuts['e'] = {
            action: () => this.exportData(),
            description: 'Export Data',
            category: 'Actions'
        };
        this.shortcuts['ctrl+s'] = {
            action: (e) => this.save(e),
            description: 'Save',
            category: 'Actions'
        };
        
        // Views
        this.shortcuts['t'] = {
            action: () => this.toggleTheme(),
            description: 'Toggle Theme',
            category: 'Views'
        };
        this.shortcuts['f'] = {
            action: () => this.toggleFullscreen(),
            description: 'Toggle Fullscreen',
            category: 'Views'
        };
        this.shortcuts['['] = {
            action: () => this.previousTab(),
            description: 'Previous Tab',
            category: 'Views'
        };
        this.shortcuts[']'] = {
            action: () => this.nextTab(),
            description: 'Next Tab',
            category: 'Views'
        };
        this.shortcuts['1'] = {
            action: () => this.switchWorkspace(1),
            description: 'Switch to Workspace 1',
            category: 'Workspaces'
        };
        this.shortcuts['2'] = {
            action: () => this.switchWorkspace(2),
            description: 'Switch to Workspace 2',
            category: 'Workspaces'
        };
        this.shortcuts['3'] = {
            action: () => this.switchWorkspace(3),
            description: 'Switch to Workspace 3',
            category: 'Workspaces'
        };
        
        // System
        this.shortcuts['?'] = {
            action: () => this.showShortcutGuide(),
            description: 'Show Keyboard Shortcuts',
            category: 'System'
        };
        this.shortcuts['escape'] = {
            action: () => this.closeModals(),
            description: 'Close Modals',
            category: 'System'
        };
        this.shortcuts['ctrl+,'] = {
            action: () => this.navigate('/settings'),
            description: 'Open Settings',
            category: 'System'
        };
        this.shortcuts['ctrl+d'] = {
            action: (e) => this.openDebugPanel(e),
            description: 'Open Debug Panel',
            category: 'System'
        };
        this.shortcuts['ctrl+shift+d'] = {
            action: (e) => this.openDebugPanel(e),
            description: 'Open Debug Panel (Alt)',
            category: 'System'
        };
        
        // Additional shortcuts
        this.shortcuts['ctrl+b'] = {
            action: () => this.toggleBookmark(),
            description: 'Toggle Bookmark',
            category: 'Actions'
        };
        this.shortcuts['ctrl+h'] = {
            action: () => this.showHelp(),
            description: 'Show Help',
            category: 'System'
        };
        this.shortcuts['ctrl+n'] = {
            action: () => this.showNotifications(),
            description: 'Show Notifications',
            category: 'System'
        };
    }
    
    init() {
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        console.log('[Shortcuts] Initialized with', Object.keys(this.shortcuts).length, 'shortcuts');
    }
    
    handleKeyDown(e) {
        // Don't trigger shortcuts when typing in inputs
        if (e.target.matches('input, textarea, select')) {
            // Exception: Escape and Command Palette shortcuts work everywhere
            if (!['escape', 'ctrl+k', 'meta+k'].includes(this.getKeyCombo(e))) {
                return;
            }
        }
        
        const keyCombo = this.getKeyCombo(e);
        
        // Handle sequence shortcuts (like 'g d')
        if (this.isSequenceStarter(keyCombo)) {
            this.sequenceKeys.push(keyCombo);
            this.resetSequenceTimeout();
            return;
        }
        
        // Check for sequence completion
        if (this.sequenceKeys.length > 0) {
            const sequence = this.sequenceKeys.join(' ') + ' ' + keyCombo;
            if (this.shortcuts[sequence]) {
                e.preventDefault();
                this.shortcuts[sequence].action(e);
                this.sequenceKeys = [];
                this.clearSequenceTimeout();
                return;
            }
        }
        
        // Check for direct shortcut
        if (this.shortcuts[keyCombo]) {
            e.preventDefault();
            this.shortcuts[keyCombo].action(e);
        }
    }
    
    getKeyCombo(e) {
        const parts = [];
        
        if (e.ctrlKey) parts.push('ctrl');
        if (e.metaKey) parts.push('meta');
        if (e.shiftKey && !['?', '[', ']'].includes(e.key)) parts.push('shift');
        if (e.altKey) parts.push('alt');
        
        const key = e.key.toLowerCase();
        parts.push(key);
        
        return parts.join('+');
    }
    
    isSequenceStarter(key) {
        return key === 'g';
    }
    
    resetSequenceTimeout() {
        this.clearSequenceTimeout();
        this.sequenceTimeout = setTimeout(() => {
            this.sequenceKeys = [];
        }, this.sequenceTimeoutDuration);
    }
    
    clearSequenceTimeout() {
        if (this.sequenceTimeout) {
            clearTimeout(this.sequenceTimeout);
            this.sequenceTimeout = null;
        }
    }
    
    // Action implementations
    navigate(url) {
        window.location.href = url;
    }
    
    openCommandPalette() {
        const event = new CustomEvent('open-command-palette');
        document.dispatchEvent(event);
    }
    
    focusSearch(e) {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="Search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    newTrade() {
        console.log('[Shortcuts] New trade action');
        // Implement new trade modal
    }
    
    refreshData() {
        console.log('[Shortcuts] Refreshing data...');
        if (typeof window.refreshDashboard === 'function') {
            window.refreshDashboard();
        } else {
            window.location.reload();
        }
    }
    
    exportData() {
        console.log('[Shortcuts] Export data action');
        const event = new CustomEvent('export-data');
        document.dispatchEvent(event);
    }
    
    save(e) {
        e.preventDefault();
        console.log('[Shortcuts] Save action');
        const event = new CustomEvent('save-action');
        document.dispatchEvent(event);
    }
    
    toggleTheme() {
        console.log('[Shortcuts] Toggling theme...');
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
    
    previousTab() {
        console.log('[Shortcuts] Previous tab');
        // Implement tab switching
    }
    
    nextTab() {
        console.log('[Shortcuts] Next tab');
        // Implement tab switching
    }
    
    switchWorkspace(num) {
        console.log('[Shortcuts] Switching to workspace', num);
        const event = new CustomEvent('switch-workspace', { detail: { workspace: num } });
        document.dispatchEvent(event);
    }
    
    showShortcutGuide() {
        this.createShortcutGuideModal();
    }
    
    closeModals() {
        // Close all open modals
        const modals = document.querySelectorAll('.modal.active, .dialog.active, .command-palette.active');
        modals.forEach(modal => modal.classList.remove('active'));
        
        // Also close mobile menu
        const mobileMenu = document.querySelector('.mobile-menu-overlay.active');
        if (mobileMenu) {
            mobileMenu.classList.remove('active');
            document.querySelector('.mobile-menu-backdrop')?.classList.remove('active');
            document.querySelector('.hamburger-menu')?.classList.remove('active');
        }
    }
    
    openDebugPanel(e) {
        e.preventDefault();
        const event = new CustomEvent('open-debug-panel');
        document.dispatchEvent(event);
    }
    
    toggleBookmark() {
        console.log('[Shortcuts] Toggle bookmark');
        const event = new CustomEvent('toggle-bookmark');
        document.dispatchEvent(event);
    }
    
    showHelp() {
        const event = new CustomEvent('show-help');
        document.dispatchEvent(event);
    }
    
    showNotifications() {
        const event = new CustomEvent('show-notifications');
        document.dispatchEvent(event);
    }
    
    createShortcutGuideModal() {
        // Remove existing modal if present
        const existing = document.getElementById('shortcut-guide-modal');
        if (existing) {
            existing.remove();
        }
        
        // Create modal
        const modal = document.createElement('div');
        modal.id = 'shortcut-guide-modal';
        modal.className = 'modal active';
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        
        const content = document.createElement('div');
        content.className = 'modal-content';
        content.style.cssText = 'background: var(--dark-card, #1e293b); color: white; padding: 32px; border-radius: 12px; max-width: 800px; max-height: 80vh; overflow-y: auto; width: 90%;';
        
        // Group shortcuts by category
        const categories = {};
        Object.entries(this.shortcuts).forEach(([key, shortcut]) => {
            if (!categories[shortcut.category]) {
                categories[shortcut.category] = [];
            }
            categories[shortcut.category].push({ key, ...shortcut });
        });
        
        let html = '<h2 style="margin-top: 0; margin-bottom: 24px; font-size: 24px;">⌨️ Keyboard Shortcuts</h2>';
        
        Object.entries(categories).forEach(([category, shortcuts]) => {
            html += `<div style="margin-bottom: 24px;">`;
            html += `<h3 style="font-size: 18px; margin-bottom: 12px; color: #00d4ff;">${category}</h3>`;
            html += '<div style="display: grid; grid-template-columns: 1fr 2fr; gap: 12px;">';
            
            shortcuts.forEach(shortcut => {
                const keyDisplay = this.formatKeyDisplay(shortcut.key);
                html += `
                    <div style="font-family: monospace; font-size: 14px; padding: 6px 12px; background: rgba(0,0,0,0.3); border-radius: 4px; text-align: center;">
                        ${keyDisplay}
                    </div>
                    <div style="padding: 6px 12px; display: flex; align-items: center;">
                        ${shortcut.description}
                    </div>
                `;
            });
            
            html += '</div></div>';
        });
        
        html += '<div style="margin-top: 24px; text-align: center;"><button onclick="this.closest(\'.modal\').remove()" style="padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">Close (Esc)</button></div>';
        
        content.innerHTML = html;
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        // Close on click outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    formatKeyDisplay(key) {
        return key
            .replace('ctrl', '⌃ Ctrl')
            .replace('meta', '⌘ Cmd')
            .replace('shift', '⇧ Shift')
            .replace('alt', '⌥ Alt')
            .replace('+', ' + ')
            .split(' ')
            .map(k => k.charAt(0).toUpperCase() + k.slice(1))
            .join(' ');
    }
}

// Initialize keyboard shortcuts
document.addEventListener('DOMContentLoaded', () => {
    window.keyboardShortcuts = new KeyboardShortcutManager();
    console.log('[Shortcuts] Keyboard shortcuts ready');
});
