/**
 * WebSocket Service for MYC3LIUM Real-time Updates
 * 
 * Manages WebSocket connection to the backend for real-time mesh network events.
 * Auto-reconnects on disconnect with exponential backoff.
 */

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export type WebSocketEventType =
  | 'connected'
  | 'node_added'
  | 'node_updated'
  | 'node_removed'
  | 'thread_added'
  | 'thread_updated'
  | 'thread_removed'
  | 'message_added'
  | 'message_removed'
  | 'stats'
  | 'echo'
  | 'client_disconnected'
  | 'store_cleared'
  | 'store_loaded'
  | 'mesh_update'
  | 'meshtastic_node_added'
  | 'meshtastic_node_updated'
  | 'meshtastic_message'
  | 'reconnected';

export interface WebSocketMessage {
  event: WebSocketEventType;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any;
  timestamp: string;
}

export type EventHandler = (message: WebSocketMessage) => void;

/**
 * WebSocket Client with auto-reconnect and event subscriptions
 */
export class MeshWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 1000; // Start with 1 second
  private reconnectTimer: number | null = null;
  private eventHandlers: Map<WebSocketEventType, Set<EventHandler>> = new Map();
  private globalHandlers: Set<EventHandler> = new Set();
  private isManualClose: boolean = false;

  /**
   * Connection state
   */
  private _isConnected: boolean = false;
  private _connectionId: string | null = null;

  constructor() {
    this.url = `${WS_BASE_URL}/ws`;
  }

  /**
   * Check if connected
   */
  get isConnected(): boolean {
    return this._isConnected;
  }

  /**
   * Get client ID assigned by server
   */
  get connectionId(): string | null {
    return this._connectionId;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WS] Already connected');
      return;
    }

    this.isManualClose = false;

    try {
      console.log('[WS] Connecting to', this.url);
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        const wasReconnect = this.reconnectAttempts > 0;
        console.log('[WS] Connected');
        this._isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        if (wasReconnect) {
          console.log('[WS] Reconnected after disconnect');
          this.handleMessage({
            event: 'reconnected',
            data: {},
            timestamp: new Date().toISOString(),
          });
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[WS] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
      };

      this.ws.onclose = () => {
        console.log('[WS] Disconnected');
        this._isConnected = false;
        this._connectionId = null;

        if (!this.isManualClose) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WS] Connection failed:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isManualClose = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._isConnected = false;
    this._connectionId = null;
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = window.setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Handle incoming WebSocket message
   */
  private handleMessage(msg: WebSocketMessage): void {
    // Handle special 'connected' event to capture client ID
    if (msg.event === 'connected' && msg.data?.client_id) {
      this._connectionId = msg.data.client_id;
      console.log('[WS] Client ID:', this._connectionId);
    }

    // Call event-specific handlers
    const handlers = this.eventHandlers.get(msg.event);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(msg);
        } catch (error) {
          console.error('[WS] Handler error:', error);
        }
      });
    }

    // Call global handlers
    this.globalHandlers.forEach((handler) => {
      try {
        handler(msg);
      } catch (error) {
        console.error('[WS] Global handler error:', error);
      }
    });
  }

  /**
   * Subscribe to a specific event type
   */
  on(event: WebSocketEventType, handler: EventHandler): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.eventHandlers.get(event)?.delete(handler);
    };
  }

  /**
   * Subscribe to all events
   */
  onAll(handler: EventHandler): () => void {
    this.globalHandlers.add(handler);

    // Return unsubscribe function
    return () => {
      this.globalHandlers.delete(handler);
    };
  }

  /**
   * Unsubscribe from an event
   */
  off(event: WebSocketEventType, handler: EventHandler): void {
    this.eventHandlers.get(event)?.delete(handler);
  }

  /**
   * Send a message to the server (for keepalive/echo)
   */
  send(data: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    } else {
      console.warn('[WS] Cannot send message: not connected');
    }
  }

  /**
   * Send keepalive ping
   */
  ping(): void {
    this.send('ping');
  }
}

// Singleton instance
let wsClient: MeshWebSocketClient | null = null;

/**
 * Get the singleton WebSocket client instance
 */
export function getWebSocketClient(): MeshWebSocketClient {
  if (!wsClient) {
    wsClient = new MeshWebSocketClient();
  }
  return wsClient;
}

/**
 * Connect to WebSocket server
 */
export function connectWebSocket(): MeshWebSocketClient {
  const client = getWebSocketClient();
  client.connect();
  return client;
}

/**
 * Disconnect from WebSocket server
 */
export function disconnectWebSocket(): void {
  wsClient?.disconnect();
}
