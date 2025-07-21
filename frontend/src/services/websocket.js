/**
 * WebSocket service for real-time communication.
 * Handles WebSocket connection and message handling for live updates.
 */

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.callbacks = {
      onMessage: null,
      onConnect: null,
      onDisconnect: null,
      onError: null
    };
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.heartbeatInterval = null;
  }

  connect(callbacks = {}) {
    // Set callbacks
    this.callbacks = { ...this.callbacks, ...callbacks };

    // Clean up existing connection
    if (this.ws) {
      this.disconnect();
    }

    try {
      console.log('Connecting to WebSocket:', `${WS_BASE_URL}/api/v1/ws`);
      this.ws = new WebSocket(`${WS_BASE_URL}/api/v1/ws`);

      this.ws.onopen = (event) => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000; // Reset delay
        
        // Start heartbeat
        this.startHeartbeat();
        
        if (this.callbacks.onConnect) {
          this.callbacks.onConnect(event);
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data.type);
          
          if (this.callbacks.onMessage) {
            this.callbacks.onMessage(data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error, event.data);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        
        if (this.callbacks.onDisconnect) {
          this.callbacks.onDisconnect(event);
        }

        // Attempt to reconnect if not closed intentionally
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.attemptReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnected = false;
        
        if (this.callbacks.onError) {
          this.callbacks.onError(error);
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      if (this.callbacks.onError) {
        this.callbacks.onError(error);
      }
    }
  }

  disconnect() {
    console.log('Disconnecting WebSocket');
    this.isConnected = false;
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  send(message) {
    if (this.ws && this.isConnected) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
        this.ws.send(messageStr);
        console.log('WebSocket message sent:', messageStr);
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }
  }

  // Send ping to keep connection alive
  ping() {
    return this.send({
      type: 'ping',
      timestamp: Date.now()
    });
  }

  // Subscribe to specific update types
  subscribe(subscriptions) {
    return this.send({
      type: 'subscribe_updates',
      subscriptions: subscriptions
    });
  }

  // Request current status
  requestStatus() {
    return this.send({
      type: 'request_status',
      timestamp: Date.now()
    });
  }

  startHeartbeat() {
    // Send ping every 30 seconds to keep connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.ping();
      }
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  attemptReconnect() {
    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
    
    setTimeout(() => {
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        this.connect(this.callbacks);
      }
    }, this.reconnectDelay);

    // Exponential backoff for reconnection delay
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000); // Max 30 seconds
  }

  getConnectionState() {
    return {
      isConnected: this.isConnected,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Create and export singleton instance
export const websocketService = new WebSocketService();
export default websocketService;