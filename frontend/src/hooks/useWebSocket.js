import { useCallback, useEffect, useRef, useState } from 'react';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

/**
 * WebSocket connection states
 */
export const ConnectionState = {
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error',
};

/**
 * Message types from the server
 */
export const MessageType = {
  EVENT_NEW: 'event:new',
  EVENT_UPDATE: 'event:update',
  ALERT_TRIGGERED: 'alert:triggered',
  REPORT_GENERATED: 'report:generated',
  CONNECTION_ACK: 'connection:ack',
  HEARTBEAT: 'heartbeat',
  ERROR: 'error',
};

/**
 * Custom hook for WebSocket connection with auto-reconnect
 */
export function useWebSocket(options = {}) {
  const {
    onEvent,
    onAlert,
    onReport,
    onConnectionChange,
    autoConnect = true,
    subscription = null,
  } = options;

  const [connectionState, setConnectionState] = useState(ConnectionState.DISCONNECTED);
  const [clientId, setClientId] = useState(null);
  const [lastHeartbeat, setLastHeartbeat] = useState(null);
  
  const wsRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);
  const mountedRef = useRef(true);

  // Update connection state and notify
  const updateConnectionState = useCallback((state) => {
    setConnectionState(state);
    onConnectionChange?.(state);
  }, [onConnectionChange]);

  // Send a message to the server
  const sendMessage = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  // Subscribe to specific events
  const subscribe = useCallback((subscriptionData) => {
    return sendMessage({
      type: 'subscribe',
      data: subscriptionData,
    });
  }, [sendMessage]);

  // Unsubscribe from filtered events
  const unsubscribe = useCallback(() => {
    return sendMessage({ type: 'unsubscribe' });
  }, [sendMessage]);

  // Send ping to keep connection alive
  const ping = useCallback(() => {
    return sendMessage({ type: 'ping' });
  }, [sendMessage]);

  // Handle incoming messages
  const handleMessage = useCallback((event) => {
    try {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case MessageType.CONNECTION_ACK:
          setClientId(message.client_id);
          reconnectAttemptsRef.current = 0;
          // Apply initial subscription if provided
          if (subscription) {
            subscribe(subscription);
          }
          break;
          
        case MessageType.EVENT_NEW:
        case MessageType.EVENT_UPDATE:
          onEvent?.(message.data, message.type);
          break;
          
        case MessageType.ALERT_TRIGGERED:
          onAlert?.(message.data);
          break;
          
        case MessageType.REPORT_GENERATED:
          onReport?.(message.data);
          break;
          
        case MessageType.HEARTBEAT:
          setLastHeartbeat(new Date(message.timestamp));
          break;
          
        case MessageType.ERROR:
          console.error('WebSocket error from server:', message.message);
          break;
          
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
    }
  }, [onEvent, onAlert, onReport, subscription, subscribe]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    updateConnectionState(ConnectionState.CONNECTING);

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        if (mountedRef.current) {
          updateConnectionState(ConnectionState.CONNECTED);
        }
      };

      ws.onmessage = handleMessage;

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (mountedRef.current) {
          updateConnectionState(ConnectionState.ERROR);
        }
      };

      ws.onclose = () => {
        if (mountedRef.current) {
          updateConnectionState(ConnectionState.DISCONNECTED);
          
          // Attempt reconnection
          if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttemptsRef.current += 1;
            updateConnectionState(ConnectionState.RECONNECTING);
            
            reconnectTimeoutRef.current = setTimeout(() => {
              if (mountedRef.current) {
                connect();
              }
            }, RECONNECT_DELAY * Math.min(reconnectAttemptsRef.current, 5));
          }
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      updateConnectionState(ConnectionState.ERROR);
    }
  }, [handleMessage, updateConnectionState]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    updateConnectionState(ConnectionState.DISCONNECTED);
    reconnectAttemptsRef.current = MAX_RECONNECT_ATTEMPTS; // Prevent auto-reconnect
  }, [updateConnectionState]);

  // Auto-connect on mount
  useEffect(() => {
    mountedRef.current = true;
    
    if (autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [autoConnect, connect]);

  // Update subscription when it changes
  useEffect(() => {
    if (connectionState === ConnectionState.CONNECTED && subscription) {
      subscribe(subscription);
    }
  }, [connectionState, subscription, subscribe]);

  return {
    connectionState,
    clientId,
    lastHeartbeat,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    ping,
    sendMessage,
    isConnected: connectionState === ConnectionState.CONNECTED,
  };
}

export default useWebSocket;
