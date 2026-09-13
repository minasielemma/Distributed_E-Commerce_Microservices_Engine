import React, { useState, useContext, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Bell, Wifi, WifiOff } from 'lucide-react';
import { NotificationContext } from '../context/NotificationContext';
import { Link } from 'react-router-dom';

export const NotificationBell = () => {
  const { notifications, unreadCount, isConnected, markAsRead, deleteNotification } = useContext(NotificationContext);
  const [isOpen, setIsOpen] = useState(false);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, right: 0 });
  const bellRef = useRef(null);

  // Reposition dropdown whenever it opens
  useEffect(() => {
    if (isOpen && bellRef.current) {
      const rect = bellRef.current.getBoundingClientRect();
      setDropdownPos({
        top: rect.bottom + 6,
        right: window.innerWidth - rect.right,
      });
    }
  }, [isOpen]);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handleClick = (e) => {
      if (bellRef.current && !bellRef.current.contains(e.target)) {
        // Check if click is inside the portal dropdown
        const portal = document.getElementById('notif-dropdown-portal');
        if (!portal || !portal.contains(e.target)) {
          setIsOpen(false);
        }
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [isOpen]);

  // Close on scroll/resize (ignoring scroll events inside the notification list itself)
  useEffect(() => {
    if (!isOpen) return;
    const handleScroll = (e) => {
      const portal = document.getElementById('notif-dropdown-portal');
      if (portal && portal.contains(e.target)) {
        return; // Ignore scroll events originating from inside the notification list
      }
      setIsOpen(false);
    };
    const handleResize = () => setIsOpen(false);

    window.addEventListener('scroll', handleScroll, true);
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleResize);
    };
  }, [isOpen]);

  const dropdown = isOpen ? (
    <div
      id="notif-dropdown-portal"
      style={{
        position: 'fixed',
        top: dropdownPos.top,
        right: dropdownPos.right,
        zIndex: 9999,
        width: '22rem',
      }}
      className="bg-white border border-[#D5D9D9] shadow-xl rounded-md overflow-hidden text-[#0F1111]"
    >
      {/* Header */}
      <div className="px-4 py-3 bg-[#F0F2F2] border-b border-[#D5D9D9] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h4 className="font-bold text-sm">Notifications</h4>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amazon-orange text-white">
              {unreadCount} new
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 text-[11px]">
          {isConnected ? (
            <span className="text-green-600 inline-flex items-center gap-1 font-semibold">
              <Wifi size={11} /> Live
            </span>
          ) : (
            <span className="text-[#FF9900] inline-flex items-center gap-1">
              <WifiOff size={11} /> Connecting
            </span>
          )}
        </div>
      </div>

      {/* Notification list - Scrollable container */}
      <div className="max-h-[360px] overflow-y-auto overscroll-contain divide-y divide-[#F0F2F2] scrollbar-thin">
        {notifications.length === 0 ? (
          <div className="p-8 text-center text-xs text-[#565959]">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-20" />
            No notifications yet.
          </div>
        ) : (
          notifications.map((notif) => (
            <div
              key={notif.id}
              className={`px-4 py-3 flex items-start justify-between gap-3 transition-colors ${
                !notif.is_read ? 'bg-[#FFFBE6]' : 'hover:bg-[#F7F8F8]'
              }`}
            >
              <div className="space-y-0.5 flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  {!notif.is_read && (
                    <span className="w-2 h-2 rounded-full bg-amazon-orange shrink-0" />
                  )}
                  <span className={`text-xs font-bold truncate ${notif.is_read ? 'text-[#565959]' : 'text-[#0F1111]'}`}>
                    {notif.title || 'Notification'}
                  </span>
                </div>
                <p className="text-xs text-[#565959] line-clamp-2 leading-relaxed pl-4">
                  {notif.message || notif.body}
                </p>
                <span className="text-[10px] text-[#999] block pl-4">
                  {new Date(notif.created_at || Date.now()).toLocaleString(undefined, {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                  })}
                </span>
              </div>

              <div className="flex flex-col items-end gap-1 shrink-0">
                {!notif.is_read && (
                  <button
                    onClick={() => markAsRead(notif.id)}
                    className="text-[10px] text-[#007185] hover:underline hover:text-[#C7511F] whitespace-nowrap"
                  >
                    Mark read
                  </button>
                )}
                <button
                  onClick={() => deleteNotification(notif.id)}
                  className="text-[10px] text-[#007185] hover:underline hover:text-[#C7511F]"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 bg-[#F0F2F2] border-t border-[#D5D9D9] text-center">
        <Link
          to="/notifications"
          onClick={() => setIsOpen(false)}
          className="text-xs font-semibold text-[#007185] hover:underline hover:text-[#C7511F]"
        >
          See all notifications →
        </Link>
      </div>
    </div>
  ) : null;

  return (
    <>
      <button
        ref={bellRef}
        onClick={() => setIsOpen((o) => !o)}
        className="relative p-2 rounded-lg text-white hover:bg-white/10 transition-all flex items-center justify-center"
        title={isConnected ? 'Live notifications' : 'Connecting...'}
      >
        <Bell className="w-5 h-5" />

        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amazon-orange text-white text-[9px] font-black flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}

        {/* Live indicator dot */}
        <span
          className={`absolute bottom-1 right-1 w-1.5 h-1.5 rounded-full ${
            isConnected ? 'bg-green-400' : 'bg-[#FF9900]'
          }`}
        />
      </button>

      {/* Render dropdown via portal to escape overflow:auto clipping */}
      {createPortal(dropdown, document.body)}
    </>
  );
};
