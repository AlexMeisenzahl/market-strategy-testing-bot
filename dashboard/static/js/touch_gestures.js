/**
 * Touch Gesture Handler
 * Handles swipe gestures for mobile navigation
 */

class TouchGestureHandler {
    constructor() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.minSwipeDistance = 50;
        this.maxVerticalDistance = 100;
        this.isSwiping = false;
        
        this.init();
    }
    
    init() {
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    }
    
    handleTouchStart(e) {
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
        this.isSwiping = true;
    }
    
    handleTouchMove(e) {
        if (!this.isSwiping) return;
        
        this.touchEndX = e.touches[0].clientX;
        this.touchEndY = e.touches[0].clientY;
        
        // Prevent vertical scrolling during horizontal swipe
        const xDiff = Math.abs(this.touchEndX - this.touchStartX);
        const yDiff = Math.abs(this.touchEndY - this.touchStartY);
        
        if (xDiff > yDiff && xDiff > this.minSwipeDistance / 2) {
            e.preventDefault();
        }
    }
    
    handleTouchEnd(e) {
        if (!this.isSwiping) return;
        
        this.isSwiping = false;
        
        const xDiff = this.touchEndX - this.touchStartX;
        const yDiff = Math.abs(this.touchEndY - this.touchStartY);
        
        // Ignore if too much vertical movement
        if (yDiff > this.maxVerticalDistance) {
            return;
        }
        
        // Swipe right (open menu)
        if (xDiff > this.minSwipeDistance && this.touchStartX < 50) {
            this.openMobileMenu();
        }
        
        // Swipe left (close menu)
        if (xDiff < -this.minSwipeDistance) {
            this.closeMobileMenu();
        }
    }
    
    openMobileMenu() {
        const menu = document.querySelector('.mobile-menu-overlay');
        const backdrop = document.querySelector('.mobile-menu-backdrop');
        const hamburger = document.querySelector('.hamburger-menu');
        
        if (menu) {
            menu.classList.add('active');
            if (backdrop) backdrop.classList.add('active');
            if (hamburger) hamburger.classList.add('active');
        }
    }
    
    closeMobileMenu() {
        const menu = document.querySelector('.mobile-menu-overlay');
        const backdrop = document.querySelector('.mobile-menu-backdrop');
        const hamburger = document.querySelector('.hamburger-menu');
        
        if (menu) {
            menu.classList.remove('active');
            if (backdrop) backdrop.classList.remove('active');
            if (hamburger) hamburger.classList.remove('active');
        }
    }
}

// Initialize touch gestures on mobile
if ('ontouchstart' in window) {
    document.addEventListener('DOMContentLoaded', () => {
        new TouchGestureHandler();
    });
}

// Mobile menu toggle functionality
document.addEventListener('DOMContentLoaded', () => {
    const hamburger = document.querySelector('.hamburger-menu');
    const menu = document.querySelector('.mobile-menu-overlay');
    const backdrop = document.querySelector('.mobile-menu-backdrop');
    
    if (hamburger && menu) {
        hamburger.addEventListener('click', () => {
            const isActive = menu.classList.contains('active');
            
            if (isActive) {
                menu.classList.remove('active');
                if (backdrop) backdrop.classList.remove('active');
                hamburger.classList.remove('active');
            } else {
                menu.classList.add('active');
                if (backdrop) backdrop.classList.add('active');
                hamburger.classList.add('active');
            }
        });
    }
    
    // Close menu when clicking backdrop
    if (backdrop) {
        backdrop.addEventListener('click', () => {
            menu.classList.remove('active');
            backdrop.classList.remove('active');
            hamburger.classList.remove('active');
        });
    }
    
    // Close menu when clicking a link
    if (menu) {
        const links = menu.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.remove('active');
                if (backdrop) backdrop.classList.remove('active');
                if (hamburger) hamburger.classList.remove('active');
            });
        });
    }
});
