/**
 * Device Detection and Classification
 * Detects device type, OS, and PWA installation status
 */

class DeviceDetector {
    /**
     * Check if the device is mobile (phone)
     */
    static isMobile() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        const mobileRegex = /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i;
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const screenWidth = window.innerWidth || document.documentElement.clientWidth;
        
        return mobileRegex.test(userAgent) || (hasTouch && screenWidth < 768);
    }
    
    /**
     * Check if the device is a tablet
     */
    static isTablet() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        const tabletRegex = /iPad|Android/i;
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const screenWidth = window.innerWidth || document.documentElement.clientWidth;
        
        // iPad detection
        if (/iPad/.test(userAgent)) {
            return true;
        }
        
        // MacOS with touch (iPad in desktop mode)
        if (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) {
            return true;
        }
        
        // Android tablet detection (larger screens with touch)
        if (/Android/i.test(userAgent) && hasTouch && screenWidth >= 768 && screenWidth <= 1024) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if the device is desktop
     */
    static isDesktop() {
        return !this.isMobile() && !this.isTablet();
    }
    
    /**
     * Check if the device is running iOS
     */
    static isIOS() {
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        
        // iPhone, iPad, iPod detection
        if (/iPad|iPhone|iPod/.test(userAgent)) {
            return true;
        }
        
        // iPad in desktop mode (iOS 13+)
        if (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if the app is running in standalone mode (installed as PWA)
     */
    static isStandalone() {
        // iOS standalone
        if (window.navigator.standalone === true) {
            return true;
        }
        
        // Android/Chrome standalone
        if (window.matchMedia('(display-mode: standalone)').matches) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if the device supports touch
     */
    static hasTouch() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
    
    /**
     * Get device type as string
     */
    static getDeviceType() {
        if (this.isMobile()) return 'mobile';
        if (this.isTablet()) return 'tablet';
        return 'desktop';
    }
    
    /**
     * Get screen orientation
     */
    static getOrientation() {
        if (window.innerWidth > window.innerHeight) {
            return 'landscape';
        }
        return 'portrait';
    }
    
    /**
     * Check if device is in safe area (iPhone X and newer)
     */
    static hasSafeArea() {
        return this.isIOS() && window.innerHeight >= 812;
    }
    
    /**
     * Apply device classes to body element
     */
    static applyDeviceClasses() {
        const body = document.body;
        
        // Remove existing device classes
        body.classList.remove('device-mobile', 'device-tablet', 'device-desktop', 
                             'ios-device', 'android-device', 'standalone-app',
                             'has-touch', 'has-safe-area', 'orientation-portrait', 
                             'orientation-landscape');
        
        // Add device type class
        const deviceType = this.getDeviceType();
        body.classList.add(`device-${deviceType}`);
        
        // Add OS class
        if (this.isIOS()) {
            body.classList.add('ios-device');
        } else if (/Android/i.test(navigator.userAgent)) {
            body.classList.add('android-device');
        }
        
        // Add standalone mode class
        if (this.isStandalone()) {
            body.classList.add('standalone-app');
        }
        
        // Add touch support class
        if (this.hasTouch()) {
            body.classList.add('has-touch');
        }
        
        // Add safe area class
        if (this.hasSafeArea()) {
            body.classList.add('has-safe-area');
        }
        
        // Add orientation class
        body.classList.add(`orientation-${this.getOrientation()}`);
    }
    
    /**
     * Initialize device detection
     */
    static init() {
        // Apply classes on load
        this.applyDeviceClasses();
        
        // Update on resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.applyDeviceClasses();
            }, 250);
        });
        
        // Update on orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.applyDeviceClasses();
            }, 100);
        });
        
        // Log device info for debugging
        console.log('Device Detection:', {
            type: this.getDeviceType(),
            isIOS: this.isIOS(),
            isStandalone: this.isStandalone(),
            hasTouch: this.hasTouch(),
            hasSafeArea: this.hasSafeArea(),
            orientation: this.getOrientation()
        });
    }
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        DeviceDetector.init();
    });
} else {
    DeviceDetector.init();
}

// Export for use in other scripts
window.DeviceDetector = DeviceDetector;
