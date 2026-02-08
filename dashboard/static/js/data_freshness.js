/**
 * Data Freshness Indicators
 * 
 * Shows how old data is with visual indicators:
 * - Green dot: <1 min (fresh)
 * - Yellow dot: 1-5 min (recent)
 * - Orange dot: 5-60 min (stale)
 * - Red dot: >1 hour (very stale)
 * 
 * Usage:
 * <span class="freshness-indicator" data-freshness-timestamp="2026-02-08T10:30:00Z">
 *     <span class="dot"></span> <span class="time-text"></span>
 * </span>
 */

class DataFreshnessIndicator {
    constructor() {
        this.updateInterval = 10000; // Update every 10 seconds
        this.indicators = [];
        this.init();
    }

    init() {
        // Find all freshness indicators on page
        this.updateIndicators();
        
        // Set up auto-refresh
        setInterval(() => this.updateIndicators(), this.updateInterval);
    }

    updateIndicators() {
        const elements = document.querySelectorAll('.freshness-indicator[data-freshness-timestamp]');
        
        elements.forEach(element => {
            const timestamp = element.getAttribute('data-freshness-timestamp');
            if (!timestamp) return;
            
            const age = this.calculateAge(timestamp);
            const { color, text } = this.getAgeFormat(age);
            
            // Update dot color
            const dot = element.querySelector('.dot') || this.createDot(element);
            dot.className = `dot ${color}`;
            
            // Update time text
            const timeText = element.querySelector('.time-text') || this.createTimeText(element);
            timeText.textContent = text;
            
            // Add tooltip
            element.title = `Last updated: ${this.formatFullTimestamp(timestamp)}`;
        });
    }

    createDot(parent) {
        const dot = document.createElement('span');
        dot.className = 'dot';
        parent.insertBefore(dot, parent.firstChild);
        return dot;
    }

    createTimeText(parent) {
        const timeText = document.createElement('span');
        timeText.className = 'time-text';
        parent.appendChild(timeText);
        return timeText;
    }

    calculateAge(timestamp) {
        const now = new Date();
        const then = new Date(timestamp);
        return Math.floor((now - then) / 1000); // Age in seconds
    }

    getAgeFormat(ageSeconds) {
        const minutes = Math.floor(ageSeconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (ageSeconds < 60) {
            // Less than 1 minute - green
            return {
                color: 'green',
                text: `${ageSeconds}s ago`
            };
        } else if (minutes < 5) {
            // 1-5 minutes - yellow
            return {
                color: 'yellow',
                text: `${minutes}m ago`
            };
        } else if (minutes < 60) {
            // 5-60 minutes - orange
            return {
                color: 'orange',
                text: `${minutes}m ago`
            };
        } else if (hours < 24) {
            // 1-24 hours - red
            return {
                color: 'red',
                text: `${hours}h ago`
            };
        } else {
            // More than 1 day - red
            return {
                color: 'red',
                text: `${days}d ago`
            };
        }
    }

    formatFullTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZoneName: 'short'
        });
    }

    // Method to manually update a specific indicator
    updateIndicator(element, timestamp) {
        element.setAttribute('data-freshness-timestamp', timestamp);
        this.updateIndicators();
    }

    // Method to add a new indicator dynamically
    addIndicator(element, timestamp) {
        element.classList.add('freshness-indicator');
        element.setAttribute('data-freshness-timestamp', timestamp);
        
        if (!element.querySelector('.dot')) {
            this.createDot(element);
        }
        if (!element.querySelector('.time-text')) {
            this.createTimeText(element);
        }
        
        this.updateIndicators();
    }
}

// Initialize when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.dataFreshnessIndicator = new DataFreshnessIndicator();
        });
    } else {
        window.dataFreshnessIndicator = new DataFreshnessIndicator();
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataFreshnessIndicator;
}
