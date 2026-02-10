/**
 * Utility Functions for Dashboard
 * 
 * Provides debouncing, formatting, API client, and chart helpers
 */

/**
 * Debounce function to limit how often a function can be called
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function to ensure a function is called at most once in a specified time period
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format currency value with thousands separators
 * @param {number} value - Value to format
 * @param {boolean} showSign - Whether to show +/- sign
 * @returns {string} Formatted currency string (e.g., "$1,787.00" or "+$1,787.00")
 */
function formatCurrency(value, showSign = true) {
    if (value === null || value === undefined || isNaN(value)) {
        return '$0.00';
    }
    
    const formatted = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(Math.abs(value));
    
    if (showSign && value >= 0) {
        return '+' + formatted;
    } else if (value < 0) {
        return '-' + formatted.replace('$', '$');
    }
    return formatted;
}

/**
 * Format percentage value
 * @param {number} value - Value to format
 * @param {boolean} showSign - Whether to show +/- sign
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, showSign = true) {
    const sign = showSign && value >= 0 ? '+' : '';
    return sign + value.toFixed(2) + '%';
}

/**
 * Format date for display
 * @param {string|Date} date - Date to format
 * @param {boolean} includeTime - Whether to include time
 * @returns {string} Formatted date string
 */
function formatDate(date, includeTime = true) {
    const d = typeof date === 'string' ? new Date(date) : date;
    if (includeTime) {
        return d.toLocaleString();
    }
    return d.toLocaleDateString();
}

/**
 * API Client with retry logic
 */
class APIClient {
    constructor(baseURL, retries = 3) {
        this.baseURL = baseURL;
        this.retries = retries;
    }

    /**
     * Make a GET request with retry logic
     * @param {string} endpoint - API endpoint
     * @param {object} params - Query parameters
     * @param {number} attempt - Current attempt number
     * @returns {Promise} Response data
     */
    async get(endpoint, params = {}, attempt = 1) {
        try {
            // Build query string
            const queryString = Object.keys(params).length > 0
                ? '?' + new URLSearchParams(params).toString()
                : '';
            
            const url = `${this.baseURL}${endpoint}${queryString}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (attempt < this.retries) {
                // Exponential backoff
                const delay = Math.pow(2, attempt) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
                return this.get(endpoint, params, attempt + 1);
            }
            throw error;
        }
    }

    /**
     * Make a POST request
     * @param {string} endpoint - API endpoint
     * @param {object} data - Request body data
     * @returns {Promise} Response data
     */
    async post(endpoint, data = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    /**
     * Make a PUT request
     * @param {string} endpoint - API endpoint
     * @param {object} data - Request body data
     * @returns {Promise} Response data
     */
    async put(endpoint, data = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            throw error;
        }
    }
}

/**
 * Chart helper to safely destroy and recreate charts
 * @param {Chart} chart - Chart instance to destroy
 * @returns {null}
 */
function destroyChart(chart) {
    if (chart && typeof chart.destroy === 'function') {
        chart.destroy();
    }
    return null;
}

/**
 * Chart helper to create chart with common options
 * @param {HTMLCanvasElement} ctx - Canvas context
 * @param {string} type - Chart type
 * @param {object} data - Chart data
 * @param {object} customOptions - Custom options to merge
 * @returns {Chart} New chart instance
 */
function createChart(ctx, type, data, customOptions = {}) {
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 0  // Disable animations during updates
        },
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(30, 41, 59, 0.9)',
                titleColor: '#f1f5f9',
                bodyColor: '#cbd5e1',
                borderColor: '#475569',
                borderWidth: 1
            }
        },
        scales: {
            y: {
                grid: {
                    color: '#334155'
                },
                ticks: {
                    color: '#94a3b8'
                }
            },
            x: {
                grid: {
                    color: '#334155'
                },
                ticks: {
                    color: '#94a3b8',
                    maxRotation: 45,
                    minRotation: 45
                }
            }
        }
    };

    // Deep merge options
    const options = mergeDeep(defaultOptions, customOptions);

    return new Chart(ctx, {
        type: type,
        data: data,
        options: options
    });
}

/**
 * Deep merge utility for objects
 * @param {object} target - Target object
 * @param {object} source - Source object
 * @returns {object} Merged object
 */
function mergeDeep(target, source) {
    const output = Object.assign({}, target);
    if (isObject(target) && isObject(source)) {
        Object.keys(source).forEach(key => {
            if (isObject(source[key])) {
                if (!(key in target))
                    Object.assign(output, { [key]: source[key] });
                else
                    output[key] = mergeDeep(target[key], source[key]);
            } else {
                Object.assign(output, { [key]: source[key] });
            }
        });
    }
    return output;
}

/**
 * Check if value is an object
 * @param {any} item - Item to check
 * @returns {boolean} True if object
 */
function isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item);
}

/**
 * Show loading state on element
 * @param {HTMLElement} element - Element to show loading on
 */
function showLoading(element) {
    if (element) {
        element.classList.add('loading');
        element.disabled = true;
    }
}

/**
 * Hide loading state on element
 * @param {HTMLElement} element - Element to hide loading from
 */
function hideLoading(element) {
    if (element) {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

/**
 * Safe JSON parse with fallback
 * @param {string} str - String to parse
 * @param {any} fallback - Fallback value
 * @returns {any} Parsed value or fallback
 */
function safeJSONParse(str, fallback = null) {
    try {
        return JSON.parse(str);
    } catch (e) {
        return fallback;
    }
}

/**
 * Local storage helper with error handling
 */
const storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Error saving to localStorage:', e);
            return false;
        }
    },
    get: (key, fallback = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : fallback;
        } catch (e) {
            console.error('Error reading from localStorage:', e);
            return fallback;
        }
    },
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removing from localStorage:', e);
            return false;
        }
    }
};

/**
 * Connection status checker
 * @param {string} healthEndpoint - Health check endpoint URL
 * @returns {Promise<boolean>} Connection status
 */
async function checkConnection(healthEndpoint) {
    try {
        const response = await fetch(healthEndpoint, {
            method: 'GET',
            cache: 'no-cache'
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        debounce,
        throttle,
        formatCurrency,
        formatPercentage,
        formatDate,
        APIClient,
        destroyChart,
        createChart,
        showLoading,
        hideLoading,
        safeJSONParse,
        storage,
        checkConnection
    };
}
