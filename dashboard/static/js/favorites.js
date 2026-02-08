/**
 * Favorites/Bookmarks System
 * Allows users to bookmark pages, markets, and strategies
 */

class FavoritesManager {
    constructor() {
        this.storageKey = 'trading-bot-favorites';
        this.favorites = this.load();
        this.init();
    }
    
    init() {
        // Listen for bookmark events
        document.addEventListener('bookmark-page', (e) => {
            const url = e.detail?.url || window.location.href;
            this.addFavorite({
                type: 'page',
                url: url,
                title: document.title,
                timestamp: Date.now()
            });
        });
        
        document.addEventListener('show-bookmarks', () => {
            this.showBookmarksModal();
        });
        
        document.addEventListener('toggle-bookmark', () => {
            this.toggleCurrentPage();
        });
        
        console.log('[Favorites] Initialized with', this.favorites.length, 'bookmarks');
    }
    
    load() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('[Favorites] Error loading:', e);
            return [];
        }
    }
    
    save() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.favorites));
        } catch (e) {
            console.error('[Favorites] Error saving:', e);
        }
    }
    
    addFavorite(item) {
        // Check if already bookmarked
        const exists = this.favorites.find(f => f.url === item.url);
        if (exists) {
            console.log('[Favorites] Already bookmarked:', item.url);
            return false;
        }
        
        this.favorites.unshift(item);
        this.save();
        this.showNotification('✓ Bookmarked!');
        return true;
    }
    
    removeFavorite(url) {
        this.favorites = this.favorites.filter(f => f.url !== url);
        this.save();
        this.showNotification('✓ Bookmark removed');
    }
    
    toggleCurrentPage() {
        const url = window.location.href;
        const exists = this.favorites.find(f => f.url === url);
        
        if (exists) {
            this.removeFavorite(url);
        } else {
            this.addFavorite({
                type: 'page',
                url: url,
                title: document.title,
                timestamp: Date.now()
            });
        }
    }
    
    isBookmarked(url) {
        return this.favorites.some(f => f.url === url);
    }
    
    showBookmarksModal() {
        const existing = document.getElementById('bookmarks-modal');
        if (existing) existing.remove();
        
        const modal = document.createElement('div');
        modal.id = 'bookmarks-modal';
        modal.className = 'modal active';
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        
        const content = document.createElement('div');
        content.style.cssText = 'background: var(--dark-card, #1e293b); color: white; padding: 24px; border-radius: 12px; max-width: 600px; max-height: 80vh; overflow-y: auto; width: 90%;';
        
        let html = '<h2 style="margin-top: 0;">⭐ Bookmarks</h2>';
        
        if (this.favorites.length === 0) {
            html += '<p style="color: rgba(255,255,255,0.6);">No bookmarks yet. Press Ctrl+B to bookmark this page.</p>';
        } else {
            html += '<div style="display: flex; flex-direction: column; gap: 12px;">';
            this.favorites.forEach(fav => {
                const date = new Date(fav.timestamp).toLocaleDateString();
                html += `
                    <div style="padding: 12px; background: rgba(0,0,0,0.3); border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <a href="${fav.url}" style="color: #3b82f6; text-decoration: none; font-size: 16px;">${fav.title}</a>
                            <div style="font-size: 12px; color: rgba(255,255,255,0.5); margin-top: 4px;">${date}</div>
                        </div>
                        <button onclick="window.favoritesManager.removeFavorite('${fav.url}'); this.closest('.modal').remove(); window.favoritesManager.showBookmarksModal();" style="background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">Remove</button>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        html += '<button onclick="this.closest(\'.modal\').remove()" style="margin-top: 20px; padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; width: 100%;">Close</button>';
        
        content.innerHTML = html;
        modal.appendChild(content);
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }
    
    showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 12px 20px; border-radius: 8px; z-index: 10001; animation: slideIn 0.3s ease;';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.favoritesManager = new FavoritesManager();
});

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
