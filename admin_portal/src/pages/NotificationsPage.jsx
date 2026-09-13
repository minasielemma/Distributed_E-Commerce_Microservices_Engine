import React, { useState, useEffect, useCallback } from 'react';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, EmptyState, LoadingSkeleton } from '../components/common/UIComponents';
import { Bell, Check, Trash2, Clock } from 'lucide-react';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange } = pagination;

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authService.getNotifications({ page, page_size: pageSize });
      const resData = res?.data;
      const list = Array.isArray(resData) ? resData : (resData?.results || []);
      setNotifications(list);
      updatePaginationState(resData);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, updatePaginationState, showError]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkRead = async (id) => {
    try {
      await authService.markNotificationRead(id);
      showSuccess('Notification marked as read');
      fetchNotifications();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async (id) => {
    try {
      await authService.deleteNotification(id);
      showSuccess('Notification deleted');
      fetchNotifications();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Notifications Center"
        subtitle="Tenant subscription events, out-of-stock alerts, and system notifications"
        breadcrumbs={['System', 'Notifications']}
        pagination={pagination}
      />

      <div className="px-4 md:px-6">
        {loading ? (
          <LoadingSkeleton count={3} type="table" />
        ) : notifications.length === 0 ? (
          <EmptyState
            icon={Bell}
            title="No notifications found"
            description="System notifications and operational alerts will appear here."
          />
        ) : (
          <div className="space-y-3">
            {notifications.map((notif) => (
              <div
                key={notif.id}
                className={`app-card p-4 flex items-start justify-between gap-4 transition-all ${
                  !notif.is_read ? 'border-l-4 border-l-[#7c7bad] bg-[#7c7bad]/5' : 'opacity-85'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-bold text-white text-sm">{notif.title || 'Notification'}</h4>
                    {!notif.is_read && (
                      <span className="w-2 h-2 rounded-full bg-[#7c7bad]"></span>
                    )}
                  </div>
                  <p className="text-slate-300 text-xs">{notif.message || notif.body}</p>
                  <div className="flex items-center gap-1 text-[11px] text-[#94a3b8] font-mono pt-1">
                    <Clock className="w-3.5 h-3.5 text-[#7c7bad]" />
                    <span>{new Date(notif.created_at || Date.now()).toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {!notif.is_read && (
                    <button
                      onClick={() => handleMarkRead(notif.id)}
                      className="p-1.5 rounded bg-[#7c7bad]/20 text-[#7c7bad] hover:bg-[#7c7bad] hover:text-white transition-colors"
                      title="Mark as read"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(notif.id)}
                    className="p-1.5 rounded bg-white/5 text-[#94a3b8] hover:text-rose-400 hover:bg-white/10 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
