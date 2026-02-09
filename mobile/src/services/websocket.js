/**
 * WebSocket Service
 * 
 * Manages WebSocket connection for real-time updates.
 * 
 * Configuration:
 * - For production, set WS_URL via window.WS_URL before loading
 * - For development, uses localhost:8000
 */

// Configure WebSocket URL
// You can override this by setting window.WS_URL before loading this script
const WS_URL = window.WS_URL || (
  window.location.origin.includes('localhost')
    ? 'ws://localhost:8000/ws/stream'
    : `wss://${window.location.host}/ws/stream`
);

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.listeners = new Map();
    this.isConnected = false;
  }

  connect() {
    if (this.ws) {
      return;
    }

    console.log('WebSocket: Connecting...');
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('WebSocket: Connected');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.emit('connected', {});
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.emit(message.type, message.data);
      } catch (error) {
        console.error('WebSocket: Message parse error:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket: Error:', error);
      this.emit('error', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket: Disconnected');
      this.isConnected = false;
      this.ws = null;
      this.stopHeartbeat();
      this.emit('disconnected', {});
      this.attemptReconnect();
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.stopHeartbeat();
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('WebSocket: Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`WebSocket: Reconnecting (attempt ${this.reconnectAttempts})...`);

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send('ping');
      }
    }, 30000); // 30 seconds
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  send(message) {
    if (this.ws && this.isConnected) {
      this.ws.send(typeof message === 'string' ? message : JSON.stringify(message));
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`WebSocket: Event handler error (${event}):`, error);
        }
      });
    }
  }
}

export default new WebSocketService();
