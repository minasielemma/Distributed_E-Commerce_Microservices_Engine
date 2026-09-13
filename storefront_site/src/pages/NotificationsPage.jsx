import React, { useState, useEffect } from 'react';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { LoadingSkeleton, Pagination } from '../components/common/UIComponents';
import { usePagination } from '../hooks/usePagination';
import { Link } from 'react-router-dom';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPage: 1, initialPageSize: 10 });

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await authService.getNotifications({
        page: pagination.page,
        page_size: pagination.pageSize,
      });
      const data = res?.data;
      if (Array.isArray(data)) {
        setNotifications(data);
        pagination.updatePaginationState({ count: data.length, total_pages: 1, current_page: 1 });
      } else {
        setNotifications(data?.results || []);
        pagination.updatePaginationState(data);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [pagination.page, pagination.pageSize]);

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
      showSuccess('Notification removed');
      fetchNotifications();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <h1 className="text-3xl font-normal">Message Center</h1>
          <LoadingSkeleton count={3} type="table" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto space-y-6">
        <div>
          <Link to="/profile" className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline mb-2 block">
            Your Account
          </Link>
          <h1 className="text-3xl font-normal">Message Center</h1>
        </div>

        {notifications.length === 0 ? (
          <div className="py-8">
             <p className="text-lg">You have no new messages.</p>
          </div>
        ) : (
          <div className="border border-[#D5D9D9] rounded bg-white">
            <div className="bg-[#F0F2F2] p-4 border-b border-[#D5D9D9]">
              <h2 className="font-bold text-lg text-[#111]">Messages</h2>
            </div>
            
            <div className="divide-y divide-[#D5D9D9]">
              {notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-5 flex items-start justify-between gap-4 ${
                    !notif.is_read ? 'bg-[#F9F9F9]' : ''
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className={`text-base ${!notif.is_read ? 'font-bold' : 'font-medium'}`}>
                        {notif.title || 'Notification'}
                      </h4>
                    </div>
                    <p className="text-sm text-[#111]">{notif.message || notif.body}</p>
                    <div className="text-xs text-[#565959] pt-1">
                      {new Date(notif.created_at || Date.now()).toLocaleDateString(undefined, {
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {!notif.is_read && (
                      <button
                        onClick={() => handleMarkRead(notif.id)}
                        className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline"
                      >
                        Mark as read
                      </button>
                    )}
                    {notif.is_read && <span className="text-[#D5D9D9] hidden sm:inline">|</span>}
                    <button
                      onClick={() => handleDelete(notif.id)}
                      className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {pagination.totalPages > 1 && (
          <div className="pt-4 flex justify-center">
            <Pagination
              currentPage={pagination.page}
              totalPages={pagination.totalPages}
              onPageChange={pagination.handlePageChange}
            />
          </div>
        )}
      </div>
    </div>
  );
}
