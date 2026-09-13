import React, { useState, useEffect, useContext } from 'react';
import { NavLink } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { chatService } from '../services/apiServices';
import { 
  LayoutDashboard, Store, Package, Layers, Tag, Percent, 
  ShoppingBag, CreditCard, Boxes, Wallet, FileText, Image as ImageIcon, 
  Bell, ShieldAlert, History, PackageSearch, MessageSquare, ChevronLeft, ChevronRight, X
} from 'lucide-react';

export const Sidebar = ({ collapsed = false, setCollapsed, mobileOpen = false, setMobileOpen }) => {
  const { activeTenant, isPlatformAdmin } = useContext(AuthContext);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!isPlatformAdmin) {
      const fetchUnread = () => {
        chatService.getUnreadCount()
          .then((res) => setUnreadCount(res.data?.unread_count || 0))
          .catch(() => {});
      };
      fetchUnread();

      const handleNotif = (e) => {
        const notif = e.detail;
        if (notif?.notification_type === 'CHAT' || notif?.metadata?.room_id) {
          fetchUnread();
        }
      };

      const handleUnreadUpdate = (e) => {
        if (typeof e?.detail?.total_unread_count === 'number') {
          setUnreadCount(e.detail.total_unread_count);
        } else {
          fetchUnread();
        }
      };

      window.addEventListener('notification_received', handleNotif);
      window.addEventListener('chat_unread_updated', handleUnreadUpdate);

      const interval = setInterval(fetchUnread, 10000);
      return () => {
        window.removeEventListener('notification_received', handleNotif);
        window.removeEventListener('chat_unread_updated', handleUnreadUpdate);
        clearInterval(interval);
      };
    }
  }, [isPlatformAdmin]);

  const platformAdminSections = [
    {
      title: 'Governance & Apps',
      items: [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Tenants Governance', path: '/tenants', icon: Store },
        { name: 'Subscription Plans', path: '/subscriptions', icon: ShieldAlert },
        { name: 'Global Categories', path: '/categories', icon: Layers },
      ]
    },
    {
      title: 'Finance & Invoicing',
      items: [
        { name: 'Platform Finance', path: '/finance', icon: Wallet },
        { name: 'Payments & Audits', path: '/payments', icon: CreditCard },
        { name: 'Billing & Invoices', path: '/invoices', icon: FileText },
      ]
    },
    {
      title: 'System Administration',
      items: [
        { name: 'Notifications', path: '/notifications', icon: Bell },
        { name: 'Activity Audit Logs', path: '/activity', icon: History },
      ]
    }
  ];

  const storeOwnerSections = [
    {
      title: 'Overview & Analytics',
      items: [
        { name: 'Store Dashboard', path: '/', icon: LayoutDashboard },
      ]
    },
    {
      title: 'Sales & Catalog',
      items: [
        { name: 'Products Catalog', path: '/products', icon: Package },
        { name: 'Inventory & Stock', path: '/inventory', icon: Boxes },
        { name: 'Orders Fulfillments', path: '/orders', icon: ShoppingBag },
        { name: 'Item Requests', path: '/item-requests', icon: PackageSearch },
      ]
    },
    {
      title: 'Marketing & Promos',
      items: [
        { name: 'Coupons & Promos', path: '/coupons', icon: Tag },
        { name: 'Price Discounts', path: '/discounts', icon: Percent },
      ]
    },
    {
      title: 'Finance & Workspace',
      items: [
        { name: 'Finance & Ledger', path: '/finance', icon: Wallet },
        { name: 'Customer Chat', path: '/chat', icon: MessageSquare },
        { name: 'Media Library', path: '/media', icon: ImageIcon },
        { name: 'Notifications', path: '/notifications', icon: Bell },
      ]
    }
  ];

  const sections = isPlatformAdmin ? platformAdminSections : storeOwnerSections;

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className={`
        fixed lg:sticky top-0 z-40 h-screen bg-[#0f172a] border-r border-slate-800/90 
        flex flex-col justify-between transition-all duration-300 select-none shrink-0 shadow-2xl
        ${collapsed ? 'w-20' : 'w-64'}
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full overflow-hidden">
          {/* Header Branding */}
          <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-700 via-purple-600 to-indigo-600 flex items-center justify-center font-black text-white text-base shadow-lg shadow-purple-900/30 shrink-0">
                {isPlatformAdmin ? 'O' : 'ERP'}
              </div>
              {!collapsed && (
                <div className="min-w-0">
                  <h3 className="font-extrabold text-slate-100 text-sm leading-tight tracking-wide truncate">
                    {isPlatformAdmin ? 'Platform Admin' : 'Store ERP Portal'}
                  </h3>
                  <span className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase block truncate">
                    {isPlatformAdmin ? 'SuperAdmin Scope' : 'Merchant Portal'}
                  </span>
                </div>
              )}
            </div>

            {/* Mobile Close Button */}
            <button 
              onClick={() => setMobileOpen(false)}
              className="lg:hidden p-1 rounded-lg text-slate-400 hover:text-white"
            >
              <X size={18} />
            </button>

            {/* Desktop Collapse Toggle Button */}
            {setCollapsed && (
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
              >
                {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
              </button>
            )}
          </div>

          {/* Role Status Tag */}
          {!collapsed && (
            <div className="px-4 py-2 bg-slate-950/40 border-b border-slate-800/60">
              <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                isPlatformAdmin 
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                  : 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${isPlatformAdmin ? 'bg-purple-400 animate-pulse' : 'bg-teal-400'}`}></span>
                {isPlatformAdmin ? 'Platform Admin' : 'Store Merchant'}
              </span>
            </div>
          )}

          {/* Active Tenant Widget */}
          {!isPlatformAdmin && activeTenant && !collapsed && (
            <div className="mx-3 mt-3 bg-slate-900/90 border border-slate-800 rounded-xl p-3 shadow-inner">
              <div className="text-[9px] text-slate-400 uppercase font-extrabold tracking-wider">Active Shop</div>
              <div className="text-xs font-extrabold text-teal-300 truncate mt-0.5">{activeTenant.name}</div>
              <span className="mt-1 inline-block px-2 py-0.5 rounded text-[9px] font-black bg-purple-500/20 text-purple-300 border border-purple-500/30">
                {activeTenant.subscription_tier || 'PRO'} TIER
              </span>
            </div>
          )}

          {/* Navigation Items grouped into Sections */}
          <nav className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-5">
            {sections.map((section, sIdx) => (
              <div key={sIdx} className="space-y-1">
                {!collapsed && (
                  <div className="px-2 text-[10px] font-extrabold uppercase text-slate-500 tracking-wider">
                    {section.title}
                  </div>
                )}
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isChat = item.path === '/chat';
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileOpen(false)}
                      title={collapsed ? item.name : undefined}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                          isActive
                            ? 'bg-purple-700/30 text-white border-l-4 border-purple-500 shadow-md font-bold'
                            : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                        } ${collapsed ? 'justify-center px-0' : ''}`
                      }
                    >
                      <Icon size={16} className="shrink-0" />
                      {!collapsed && <span className="flex-1 truncate">{item.name}</span>}
                      {isChat && unreadCount > 0 && (
                        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-black bg-purple-600 text-white shadow-sm shrink-0 ${collapsed ? 'absolute top-1 right-1 px-1 text-[8px]' : ''}`}>
                          {unreadCount}
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </nav>

          {/* Footer Version Info */}
          {!collapsed && (
            <div className="p-3 border-t border-slate-800/80 text-[10px] text-slate-500 text-center font-mono">
              Admin Portal v2.4 • Enterprise Edition
            </div>
          )}
        </div>
      </aside>
    </>
  );
};


