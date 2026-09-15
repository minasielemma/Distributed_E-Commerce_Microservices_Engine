import { useState, useCallback, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';

export const usePresence = () => {
  const [presenceMap, setPresenceMap] = useState({});

  const handleMessage = useCallback((evt) => {
    if (evt.type === 'presence_update' && evt.data) {
      const { user_id, status, last_seen } = evt.data;
      setPresenceMap((prev) => ({
        ...prev,
        [user_id]: { status, last_seen },
      }));
    } else if (evt.type === 'connection_established' && evt.data && typeof evt.data.total_unread_count === 'number') {
      window.dispatchEvent(new CustomEvent('chat_unread_updated', { detail: evt.data }));
    } else if (evt.type === 'room_created' && evt.data) {
      window.dispatchEvent(new CustomEvent('chat_room_created', { detail: evt.data }));
      window.dispatchEvent(new CustomEvent('chat_unread_updated', { detail: evt.data }));
    } else if (evt.type === 'room_updated' && evt.data) {
      window.dispatchEvent(new CustomEvent('chat_room_updated', { detail: evt.data }));
      window.dispatchEvent(new CustomEvent('chat_unread_updated', { detail: evt.data }));
    } else if (evt.type === 'unread_count_update' && evt.data) {
      window.dispatchEvent(new CustomEvent('chat_unread_updated', { detail: evt.data }));
    }
  }, []);

  const { isConnected, sendMessage } = useWebSocket('/ws/chat/updates/', {
    onMessage: handleMessage,
  });

  useEffect(() => {
    if (!isConnected) return;
    const timer = setInterval(() => {
      sendMessage({ action: 'heartbeat', payload: {} });
    }, 120000);
    return () => clearInterval(timer);
  }, [isConnected, sendMessage]);

  const queryPresence = useCallback((userId) => {
    if (!userId) return;
    if (isConnected) {
      sendMessage({ action: 'get_presence', payload: { user_id: userId } });
    }
  }, [isConnected, sendMessage]);

  return { presenceMap, isConnected, queryPresence };
};
