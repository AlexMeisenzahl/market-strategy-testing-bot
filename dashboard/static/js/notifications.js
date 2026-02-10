/**
 * Notifications - Toast Notification System
 * 
 * Provides toast notifications for user feedback on actions.
 */

/**
 * Show notification toast
 * @param {string} message - Message to display
 * @param {string} type - Type of notification ('success', 'error', 'warning', 'info')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showNotification(message, type = 'success', duration = 3000) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Icon based on type
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    
    const icon = icons[type] || 'info-circle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    // Add styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 10000;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
        max-width: 400px;
        font-size: 14px;
    `;
    
    // Type-specific styling
    const typeStyles = {
        'success': {
            background: '#10b981',
            color: 'white'
        },
        'error': {
            background: '#ef4444',
            color: 'white'
        },
        'warning': {
            background: '#f59e0b',
            color: 'white'
        },
        'info': {
            background: '#3b82f6',
            color: 'white'
        }
    };
    
    const styles = typeStyles[type] || typeStyles.info;
    toast.style.background = styles.background;
    toast.style.color = styles.color;
    
    // Add to body
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Auto-remove after duration
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

/**
 * Show success notification
 * @param {string} message - Success message
 */
function showSuccess(message) {
    showNotification(message, 'success');
}

/**
 * Show error notification
 * @param {string} message - Error message
 */
function showError(message) {
    showNotification(message, 'error', 4000); // Longer duration for errors
}

/**
 * Show warning notification
 * @param {string} message - Warning message
 */
function showWarning(message) {
    showNotification(message, 'warning');
}

/**
 * Show info notification
 * @param {string} message - Info message
 */
function showInfo(message) {
    showNotification(message, 'info');
}

/**
 * Confirm action with modal
 * @param {string} message - Confirmation message
 * @param {Function} onConfirm - Callback for confirmation
 * @param {Function} onCancel - Callback for cancellation
 */
function confirmAction(message, onConfirm, onCancel) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10001;
    `;
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'confirm-modal';
    modal.style.cssText = `
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        max-width: 400px;
        width: 90%;
    `;
    
    modal.innerHTML = `
        <div style="margin-bottom: 20px; font-size: 16px; color: #333;">${message}</div>
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
            <button id="confirmCancel" style="
                padding: 10px 20px;
                border: 1px solid #ddd;
                background: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            ">Cancel</button>
            <button id="confirmOk" style="
                padding: 10px 20px;
                border: none;
                background: #3b82f6;
                color: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
            ">Confirm</button>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Handle confirm
    document.getElementById('confirmOk').addEventListener('click', () => {
        overlay.remove();
        if (onConfirm) onConfirm();
    });
    
    // Handle cancel
    document.getElementById('confirmCancel').addEventListener('click', () => {
        overlay.remove();
        if (onCancel) onCancel();
    });
    
    // Close on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
            if (onCancel) onCancel();
        }
    });
}

// Export functions for global use
if (typeof window !== 'undefined') {
    window.showNotification = showNotification;
    window.showSuccess = showSuccess;
    window.showError = showError;
    window.showWarning = showWarning;
    window.showInfo = showInfo;
    window.confirmAction = confirmAction;
}
