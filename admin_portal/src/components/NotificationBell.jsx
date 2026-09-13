import React, { useState, useContext, useRef, useEffect } from 'react';
import { Bell, Check, Trash2, Clock, Wifi, WifiOff } from 'lucide-react';
import { NotificationContext } from '../context/NotificationContext';
import { Link } from 'react-router-dom';

export const NotificationBell = () => {
  const { notifications, unreadCount, isConnected, markAsRead, deleteNotification } = useContext(NotificationContext);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 transition-all flex items-center justify-center"
        title={isConnected ? 'Live Notifications Connected' : 'Connecting to Notification Stream...'}
      >
        <Bell className="w-5 h-5 text-indigo-400" />
        
        {/* Unread badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-rose-500 text-white text-[10px] font-black flex items-center justify-center border-2 border-slate-950 animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}

        {/* WebSocket Live Indicator */}
        <span className={`absolute bottom-0 right-0 w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-amber-400'}`} />
      </button>

      {/* Notification Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 md:w-96 glass-panel border border-white/15 shadow-2xl z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div className="p-4 bg-slate-900/90 border-b border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h4 className="font-extrabold text-white text-sm">Notifications</h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300">
                {unreadCount} new
              </span>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              {isConnected ? (
                <span className="text-emerald-400 inline-flex items-center gap-1 font-bold">
                  <Wifi size={12} /> Live
                </span>
              ) : (
                <span className="text-amber-400 inline-flex items-center gap-1">
                  <WifiOff size={12} /> Connecting
                </span>
              )}
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto custom-scrollbar divide-y divide-white/5">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">
                No notifications right now.
              </div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`p-3.5 flex items-start justify-between gap-3 transition-colors ${
                    !notif.is_read ? 'bg-indigo-950/20' : 'opacity-70 hover:opacity-100'
                  }`}
                >
                  <div className="space-y-0.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white truncate">{notif.title}</span>
                      {!notif.is_read && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />}
                    </div>
                    <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">{notif.message}</p>
                    <span className="text-[10px] text-slate-500 block pt-1 font-mono">
                      {new Date(notif.created_at || Date.now()).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {!notif.is_read && (
                      <button
                        onClick={() => markAsRead(notif.id)}
                        className="p-1 rounded bg-indigo-500/20 text-indigo-300 hover:bg-indigo-600 hover:text-white"
                        title="Mark as read"
                      >
                        <Check size={12} />
                      </button>
                    )}
                    <button
                      onClick={() => deleteNotification(notif.id)}
                      className="p-1 rounded text-slate-500 hover:text-rose-400"
                      title="Delete"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-3 bg-slate-900/90 border-t border-white/10 text-center">
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-bold text-cyan-400 hover:underline inline-block"
            >
              View All Notifications Center →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
