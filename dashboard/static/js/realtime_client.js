/**
 * Real-Time WebSocket Client
 * 
 * Provides instant push updates from server replacing 30-second polling.
 * Handles connection management, reconnection, and event routing.
 */

class RealtimeClient {
    constructor(serverUrl = null) {
        this.serverUrl = serverUrl || window.location.origin;
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.subscriptions = new Set();
        
        // Event handlers registry
        this.handlers = {
            'price_update': [],
            'trade_executed': [],
            'signal_detected': [],
            'opportunity_found': [],
            'portfolio_updated': [],
            'system_message': []
        };
        
        // Statistics
        this.stats = {
            messagesReceived: 0,
            lastMessageTime: null,
            connectionTime: null,
            disconnections: 0
        };
    }
    
    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.connected) {
            console.log('[RealtimeClient] Already connected');
            return;
        }
        
        console.log(`[RealtimeClient] Connecting to ${this.serverUrl}...`);
        
        // Initialize Socket.IO connection
        this.socket = io(this.serverUrl, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: this.reconnectDelay,
            reconnectionAttempts: this.maxReconnectAttempts
        });
        
        // Register connection handlers
        this.socket.on('connect', () => this._onConnect());
        this.socket.on('disconnect', (reason) => this._onDisconnect(reason));
        this.socket.on('connect_error', (error) => this._onError(error));
        
        // Register event handlers
        this.socket.on('connected', (data) => this._onWelcome(data));
        this.socket.on('price_update', (data) => this._handleEvent('price_update', data));
        this.socket.on('trade_executed', (data) => this._handleEvent('trade_executed', data));
        this.socket.on('signal_detected', (data) => this._handleEvent('signal_detected', data));
        this.socket.on('opportunity_found', (data) => this._handleEvent('opportunity_found', data));
        this.socket.on('portfolio_updated', (data) => this._handleEvent('portfolio_updated', data));
        this.socket.on('system_message', (data) => this._handleEvent('system_message', data));
        
        // Ping/pong for keepalive
        this.socket.on('pong', (data) => this._onPong(data));
        
        // Start ping interval
        this.startPingInterval();
    }
    
    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.socket) {
            console.log('[RealtimeClient] Disconnecting...');
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
        }
    }
    
    /**
     * Subscribe to a specific event room
     */
    subscribe(room) {
        if (!this.connected) {
            console.warn(`[RealtimeClient] Cannot subscribe to ${room}: not connected`);
            return;
        }
        
        if (this.subscriptions.has(room)) {
            console.log(`[RealtimeClient] Already subscribed to ${room}`);
            return;
        }
        
        console.log(`[RealtimeClient] Subscribing to ${room}...`);
        this.socket.emit('subscribe', { room: room });
        this.subscriptions.add(room);
    }
    
    /**
     * Unsubscribe from a specific event room
     */
    unsubscribe(room) {
        if (!this.connected || !this.subscriptions.has(room)) {
            return;
        }
        
        console.log(`[RealtimeClient] Unsubscribing from ${room}...`);
        this.socket.emit('unsubscribe', { room: room });
        this.subscriptions.delete(room);
    }
    
    /**
     * Register event handler
     */
    on(eventType, handler) {
        if (this.handlers[eventType]) {
            this.handlers[eventType].push(handler);
        } else {
            console.warn(`[RealtimeClient] Unknown event type: ${eventType}`);
        }
    }
    
    /**
     * Remove event handler
     */
    off(eventType, handler) {
        if (this.handlers[eventType]) {
            const index = this.handlers[eventType].indexOf(handler);
            if (index > -1) {
                this.handlers[eventType].splice(index, 1);
            }
        }
    }
    
    /**
     * Get connection statistics
     */
    getStats() {
        return {
            ...this.stats,
            connected: this.connected,
            subscriptions: Array.from(this.subscriptions)
        };
    }
    
    // Private methods
    
    _onConnect() {
        console.log('[RealtimeClient] Connected to server');
        this.connected = true;
        this.reconnectAttempts = 0;
        this.stats.connectionTime = new Date();
        
        // Resubscribe to previously subscribed rooms
        this.subscriptions.forEach(room => {
            this.socket.emit('subscribe', { room: room });
        });
        
        // Notify connection
        this._notifyConnectionChange(true);
    }
    
    _onDisconnect(reason) {
        console.log(`[RealtimeClient] Disconnected: ${reason}`);
        this.connected = false;
        this.stats.disconnections++;
        
        // Notify disconnection
        this._notifyConnectionChange(false);
        
        // Attempt reconnection
        if (reason === 'io server disconnect') {
            // Server initiated disconnect, try to reconnect
            this._attemptReconnect();
        }
    }
    
    _onError(error) {
        console.error('[RealtimeClient] Connection error:', error);
    }
    
    _onWelcome(data) {
        console.log('[RealtimeClient] Welcome message received:', data);
        
        // Subscribe to default rooms
        this.subscribe('prices');
        this.subscribe('trades');
        this.subscribe('opportunities');
        this.subscribe('portfolio');
        this.subscribe('system');
    }
    
    _onPong(data) {
        // Connection is alive
        const latency = Date.now() - (data.server_time * 1000);
        console.log(`[RealtimeClient] Pong received, latency: ${latency}ms`);
    }
    
    _handleEvent(eventType, data) {
        console.log(`[RealtimeClient] Event received: ${eventType}`, data);
        
        this.stats.messagesReceived++;
        this.stats.lastMessageTime = new Date();
        
        // Call all registered handlers for this event type
        if (this.handlers[eventType]) {
            this.handlers[eventType].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`[RealtimeClient] Error in ${eventType} handler:`, error);
                }
            });
        }
    }
    
    _attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[RealtimeClient] Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`[RealtimeClient] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    _notifyConnectionChange(connected) {
        // Trigger custom event for connection status change
        const event = new CustomEvent('realtime_connection_change', {
            detail: { connected: connected }
        });
        window.dispatchEvent(event);
    }
    
    startPingInterval() {
        // Send ping every 30 seconds to keep connection alive
        this.pingInterval = setInterval(() => {
            if (this.connected) {
                this.socket.emit('ping');
            }
        }, 30000);
    }
}

// Global instance
let realtimeClient = null;

/**
 * Initialize the realtime client
 */
function initRealtimeClient() {
    if (!realtimeClient) {
        realtimeClient = new RealtimeClient();
        realtimeClient.connect();
        
        // Make it globally accessible
        window.realtimeClient = realtimeClient;
    }
    return realtimeClient;
}

/**
 * Get the realtime client instance
 */
function getRealtimeClient() {
    if (!realtimeClient) {
        return initRealtimeClient();
    }
    return realtimeClient;
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('[RealtimeClient] DOM ready, initializing...');
        initRealtimeClient();
    });
} else {
    console.log('[RealtimeClient] DOM already ready, initializing...');
    initRealtimeClient();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RealtimeClient, initRealtimeClient, getRealtimeClient };
}
