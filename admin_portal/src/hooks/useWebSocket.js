import { useEffect, useRef, useState, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  // Keep onMessage in a ref so the socket callback always accesses the current handler
  const onMessageRef = useRef(null);
  useEffect(() => {
    onMessageRef.current = options.onMessage;
  });

  const { enabled = true, autoReconnect = true, maxReconnectAttempts = 10 } = options;

  useEffect(() => {
    if (!url || !enabled) {
      setIsConnected(false);
      setIsAuthenticated(false);
      return;
    }

    let ws = null;
    let isDisposed = false;

    // Reset connection state on room switch
    setIsConnected(false);
    setIsAuthenticated(false);
    reconnectAttemptsRef.current = 0;

    const connectSocket = () => {
      if (isDisposed) return;

      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const token =
          localStorage.getItem('access_token') ||
          localStorage.getItem('token') ||
          sessionStorage.getItem('access_token') ||
          sessionStorage.getItem('token');

        const host = window.location.host;

        const wsUrl =
          url.startsWith('ws://') || url.startsWith('wss://')
            ? url
            : `${protocol}//${host}${url}`;

        const instance = new WebSocket(wsUrl);
        ws = instance;
        socketRef.current = instance;

        instance.onopen = () => {
          if (isDisposed) return;
          setIsConnected(true);
          reconnectAttemptsRef.current = 0;

          if (token) {
            instance.send(
              JSON.stringify({
                action: 'authenticate',
                payload: { token },
              })
            );
          }
        };

        instance.onmessage = (event) => {
          if (isDisposed) return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'connection_established' || data.status === 'authenticated') {
              setIsAuthenticated(true);
            }
            setLastMessage(data);
            if (onMessageRef.current) onMessageRef.current(data);
          } catch (e) {
            setLastMessage(event.data);
            if (onMessageRef.current) onMessageRef.current(event.data);
          }
        };

        instance.onclose = () => {
          if (isDisposed) return;
          setIsConnected(false);
          setIsAuthenticated(false);
          if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
            const timeout = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
            reconnectAttemptsRef.current += 1;
            reconnectTimeoutRef.current = setTimeout(connectSocket, timeout);
          }
        };

        instance.onerror = () => {
          if (isDisposed) return;
          instance.close();
        };
      } catch (e) {
        console.warn('[useWebSocket] Connection attempt error:', e);
      }
    };

    connectSocket();

    return () => {
      isDisposed = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onclose = null;
        ws.onerror = null;
        ws.close();
      }
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
    };
  }, [url, enabled, autoReconnect, maxReconnectAttempts]);

  const sendMessage = useCallback((data) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  return { isConnected, isAuthenticated, lastMessage, sendMessage };
};
