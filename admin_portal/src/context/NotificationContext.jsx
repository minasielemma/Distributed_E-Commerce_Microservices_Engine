import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import { authService } from '../services/apiServices';
import { useWebSocket } from '../hooks/useWebSocket';
import { useToast } from './ToastContext';
import { AuthContext } from './AuthContext';

export const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const { token } = useContext(AuthContext);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const { showSuccess } = useToast();

  const fetchNotifications = useCallback(async () => {
    if (!token) return;
    try {
      const res = await authService.getNotifications();
      const list = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setNotifications(list);
      setUnreadCount(list.filter(n => !n.is_read).length);
    } catch (e) {
      // Quiet fail if unauthorized
    }
  }, [token]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleWebSocketMessage = useCallback((msg) => {
    const data = msg.data || (msg.type === 'notification.message' ? msg : null);
    if ((msg.type === 'notification' || msg.type === 'notification.message') && data) {
      const newNotif = {
        id: data.id || data.metadata?.notification_id || Math.random().toString(),
        title: data.title || 'Notification',
        message: data.message || '',
        notification_type: data.notification_type || 'SYSTEM',
        is_read: false,
        metadata: data.metadata || {},
        created_at: data.created_at || data.timestamp || new Date().toISOString(),
      };

      setNotifications(prev => [newNotif, ...prev]);
      setUnreadCount(prev => prev + 1);

      showSuccess(`[${newNotif.notification_type}] ${newNotif.title}`);
      window.dispatchEvent(new CustomEvent('notification_received', { detail: newNotif }));
    }
  }, [showSuccess]);

  const { isConnected } = useWebSocket('/ws/notifications/', {
    enabled: !!token,
    onMessage: handleWebSocketMessage,
  });

  const markAsRead = async (id) => {
    try {
      await authService.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (e) {
      // Ignore
    }
  };

  const deleteNotification = async (id) => {
    try {
      await authService.deleteNotification(id);
      setNotifications(prev => {
        const item = prev.find(n => n.id === id);
        if (item && !item.is_read) {
          setUnreadCount(count => Math.max(0, count - 1));
        }
        return prev.filter(n => n.id !== id);
      });
    } catch (e) {
      // Ignore
    }
  };

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, isConnected, fetchNotifications, markAsRead, deleteNotification }}>
      {children}
    </NotificationContext.Provider>
  );
};
