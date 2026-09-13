import React, { useState, useEffect, useContext, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { CartContext } from '../context/CartContext';
import { authService, chatService } from '../services/apiServices';
import { Search, ShoppingCart, Menu, Heart, MessageSquarePlus, MessageSquare, MapPin, Store, X } from 'lucide-react';
import { NotificationBell } from './NotificationBell';

export const Navbar = () => {
  const { token, logout, activeTenantId, setTenant } = useContext(AuthContext);
  const { cartItemCount, wishlistCount } = useContext(CartContext);
  const [tenants, setTenants] = useState([]);
  const [unreadChatCount, setUnreadChatCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchUnreadChatCount = useCallback(() => {
    if (token) {
      chatService.getUnreadCount()
        .then((res) => setUnreadChatCount(res.data?.unread_count || 0))
        .catch(() => {});
    }
  }, [token]);

  useEffect(() => {
    fetchUnreadChatCount();

    const handleNotif = (e) => {
      const notif = e.detail;
      if (notif?.notification_type === 'CHAT' || notif?.metadata?.room_id) {
        fetchUnreadChatCount();
      }
    };

    const handleUnreadUpdate = (e) => {
      if (typeof e?.detail?.total_unread_count === 'number') {
        setUnreadChatCount(e.detail.total_unread_count);
      } else {
        fetchUnreadChatCount();
      }
    };

    window.addEventListener('notification_received', handleNotif);
    window.addEventListener('chat_unread_updated', handleUnreadUpdate);

    const interval = setInterval(fetchUnreadChatCount, 10000);

    return () => {
      window.removeEventListener('notification_received', handleNotif);
      window.removeEventListener('chat_unread_updated', handleUnreadUpdate);
      clearInterval(interval);
    };
  }, [token, fetchUnreadChatCount]);

  // Close mobile drawer on route/search changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname, location.search]);

  // Lock body scroll and listen for Escape key when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setMobileMenuOpen(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileMenuOpen]);

  const fetchTenants = async () => {
    try {
      const res = await authService.getTenants();
      const rawData = res.data;
      const tenantList = Array.isArray(rawData) ? rawData : (rawData?.results || []);
      setTenants(tenantList);
    } catch (err) {
      console.error(err);
    }
  };

  const currentShopInUrl = new URLSearchParams(location.search).get('shop') || new URLSearchParams(location.search).get('tenant_id') || '';

  const handleTenantChange = (e) => {
    const selectedId = e.target.value;
    setTenant(selectedId);
    const params = new URLSearchParams(location.search);
    if (selectedId) {
      params.set('shop', selectedId);
      params.delete('tenant_id');
    } else {
      params.delete('shop');
      params.delete('tenant_id');
    }
    params.set('page', '1');
    navigate(`/?${params.toString()}`);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const params = new URLSearchParams(location.search);
    if (searchQuery.trim()) {
      params.set('search', searchQuery.trim());
    } else {
      params.delete('search');
    }
    params.set('page', '1');
    navigate(`/?${params.toString()}`);
  };

  return (
    <header className="flex flex-col w-full z-50 sticky top-0 shadow-md">
      {/* Top Bar - Main Nav */}
      <div className="bg-amazon-header-primary text-white px-3 sm:px-4 py-2 flex items-center justify-between gap-2 sm:gap-4">
        {/* Left: Mobile Menu Toggle + Logo */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            className="md:hidden p-1.5 rounded text-white hover:border hover:border-white focus:outline-none"
            aria-label="Open Navigation Menu"
          >
            <Menu className="w-6 h-6" />
          </button>

          <Link to="/" className="flex items-center gap-1 border border-transparent hover:border-white p-1 rounded-sm shrink-0">
            <Store className="w-7 h-7 sm:w-8 sm:h-8 text-white" />
            <span className="text-lg sm:text-xl font-bold tracking-tight text-white mt-0.5">apex</span>
            <span className="text-[#FF9900] self-start text-[10px] sm:text-xs font-bold -ml-1 mt-0.5">store</span>
          </Link>
        </div>

        {/* Deliver To / Location (Desktop) */}
        {token && (
          <Link to="/addresses" className="hidden lg:flex items-center gap-1 border border-transparent hover:border-white p-1 rounded-sm shrink-0">
            <MapPin className="w-4 h-4 text-white self-end mb-1" />
            <div className="flex flex-col">
              <span className="text-[11px] text-gray-300 leading-none">Deliver to</span>
              <span className="text-sm font-bold leading-none">Select your address</span>
            </div>
          </Link>
        )}

        {/* Desktop Search Bar */}
        <form 
          onSubmit={handleSearchSubmit}
          className="flex-1 hidden md:flex h-10 rounded-md overflow-hidden bg-white max-w-4xl focus-within:ring-2 focus-within:ring-amazon-orange"
        >
          <select 
            className="bg-[#F3F3F3] text-black border-r border-[#CDCDCD] px-2 text-xs h-full outline-none hover:bg-[#DADADA] cursor-pointer"
            value={currentShopInUrl}
            onChange={handleTenantChange}
          >
            <option value="">All Shops</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <input 
            type="text" 
            placeholder="Search Amazon-style..."
            className="flex-1 px-3 text-black text-sm outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" className="bg-amazon-cta-secondary hover:bg-amazon-cta-secondaryHover w-12 flex items-center justify-center text-[#333]">
            <Search className="w-5 h-5" />
          </button>
        </form>

        {/* Right Section Links */}
        <div className="flex items-center gap-1 shrink-0">
          {/* Sign In / Account */}
          {token ? (
            <Link to="/profile" className="flex flex-col border border-transparent hover:border-white p-1 rounded-sm text-left">
              <span className="text-[10px] sm:text-[11px] leading-none text-gray-300">Hello, User</span>
              <span className="text-xs sm:text-sm font-bold leading-none hidden xs:inline-block mt-0.5">
                Account & Lists
              </span>
            </Link>
          ) : (
            <Link to="/login" className="flex flex-col border border-transparent hover:border-white p-1 rounded-sm text-left">
              <span className="text-[10px] sm:text-[11px] leading-none text-gray-300">Hello, sign in</span>
              <span className="text-xs sm:text-sm font-bold leading-none hidden xs:inline-block mt-0.5">
                Account & Lists
              </span>
            </Link>
          )}

          {/* Returns & Orders */}
          <Link to="/orders" className="hidden sm:flex flex-col border border-transparent hover:border-white p-1 rounded-sm">
            <span className="text-[11px] leading-none text-gray-300">Returns</span>
            <span className="text-sm font-bold leading-none">& Orders</span>
          </Link>

          {/* Cart */}
          <Link to="/cart" className="flex items-end border border-transparent hover:border-white p-1 rounded-sm relative">
            <div className="relative flex items-center">
              <ShoppingCart className="w-7 h-7 sm:w-8 sm:h-8" />
              <span className="absolute -top-1 left-2.5 sm:left-3 text-amazon-orange font-bold text-xs sm:text-sm w-4 text-center">
                {cartItemCount}
              </span>
            </div>
            <span className="text-sm font-bold hidden md:block ml-1">Cart</span>
          </Link>
        </div>
      </div>

      {/* Mobile Search Bar (Rendered for < md screens) */}
      <div className="md:hidden bg-amazon-header-primary px-3 pb-2.5 pt-0.5">
        <form 
          onSubmit={handleSearchSubmit}
          className="flex h-9 rounded-md overflow-hidden bg-white w-full focus-within:ring-2 focus-within:ring-amazon-orange"
        >
          <select 
            className="bg-[#F3F3F3] text-black border-r border-[#CDCDCD] px-1.5 text-[11px] h-full outline-none max-w-[95px] truncate"
            value={currentShopInUrl}
            onChange={handleTenantChange}
          >
            <option value="">All Shops</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <input 
            type="text" 
            placeholder="Search products..."
            className="flex-1 px-2.5 text-black text-xs outline-none min-w-0"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" className="bg-amazon-cta-secondary hover:bg-amazon-cta-secondaryHover px-3 flex items-center justify-center text-[#333] shrink-0">
            <Search className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Secondary Nav Bar (Scrollable on mobile & desktop) */}
      <div className="bg-amazon-header-secondary text-white px-3 sm:px-4 py-1.5 flex items-center gap-3 sm:gap-4 overflow-x-auto text-xs sm:text-sm custom-scrollbar shrink-0">
        <button 
          type="button"
          onClick={() => setMobileMenuOpen(true)}
          className="hidden md:flex items-center gap-1 font-bold border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap"
        >
          <Menu className="w-5 h-5" /> All
        </button>
        <Link to="/?collection=all" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap">
          All Products
        </Link>
        <Link to="/?collection=deals" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap">
          Today's Deals
        </Link>
        
        {token && (
          <>
            <Link to="/wishlist" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap flex items-center gap-1">
              Wishlist {wishlistCount > 0 && <span className="text-amazon-orange font-bold">({wishlistCount})</span>}
            </Link>
            <Link to="/chat" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap flex items-center gap-1">
              Messages {unreadChatCount > 0 && <span className="bg-amazon-orange text-white text-[10px] px-1 rounded-full">{unreadChatCount}</span>}
            </Link>
            <Link to="/item-requests" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap">
              Requests
            </Link>
            <Link to="/payments" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap">
              Payments
            </Link>
            <Link to="/invoices" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap">
              Invoices
            </Link>
            <div className="ml-auto hidden md:flex items-center gap-2">
              <NotificationBell />
              <button onClick={logout} className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap">
                Sign Out
              </button>
            </div>
          </>
        )}
        {!token && (
          <div className="ml-auto hidden md:block">
            <Link to="/register" className="border border-transparent hover:border-white px-1.5 py-0.5 rounded-sm whitespace-nowrap font-bold text-amazon-orange">
              Start selling
            </Link>
          </div>
        )}
      </div>

      {/* Mobile Navigation Drawer Overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-[100] flex md:hidden">
          <div 
            className="fixed inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
          />
          <aside className="relative w-4/5 max-w-xs bg-white h-full shadow-2xl flex flex-col z-10 overflow-y-auto">
            {/* Drawer Header */}
            <div className="bg-amazon-header-secondary text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Store className="w-6 h-6 text-amazon-orange" />
                <span className="font-bold text-base">Apex Menu</span>
              </div>
              <button 
                onClick={() => setMobileMenuOpen(false)} 
                className="p-1 rounded text-gray-300 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Shop Context Selector */}
            <div className="p-3 bg-gray-100 border-b border-gray-200">
              <label className="block text-[11px] font-bold uppercase text-gray-500 mb-1">Filter Shop</label>
              <select
                className="w-full bg-white border border-gray-300 rounded px-2 py-1.5 text-xs text-black focus:outline-none"
                value={currentShopInUrl}
                onChange={(e) => { handleTenantChange(e); setMobileMenuOpen(false); }}
              >
                <option value="">All Shops</option>
                {tenants.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>

            {/* Nav Links List */}
            <div className="flex-1 p-4 space-y-4 text-sm text-amazon-text-primary">
              <div className="space-y-2">
                <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Navigation</div>
                <Link to="/" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 font-medium hover:text-amazon-orange">
                  Home / Storefront
                </Link>
                <Link to="/?collection=all" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                  All Products
                </Link>
                <Link to="/?collection=deals" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                  Today's Deals
                </Link>
              </div>

              <div className="border-t border-gray-200 pt-3 space-y-2">
                <div className="text-xs font-bold text-gray-400 uppercase tracking-wider">Account & Support</div>
                {token ? (
                  <>
                    <Link to="/profile" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                      Your Account & Profile
                    </Link>
                    <Link to="/orders" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                      Your Orders & Returns
                    </Link>
                    <Link to="/wishlist" onClick={() => setMobileMenuOpen(false)} className="flex items-center justify-between py-1.5 hover:text-amazon-orange">
                      <span>Wishlist</span>
                      {wishlistCount > 0 && <span className="font-bold text-amazon-orange">({wishlistCount})</span>}
                    </Link>
                    <Link to="/chat" onClick={() => setMobileMenuOpen(false)} className="flex items-center justify-between py-1.5 hover:text-amazon-orange">
                      <span>Messages</span>
                      {unreadChatCount > 0 && <span className="bg-amazon-orange text-white text-xs px-2 py-0.5 rounded-full font-bold">{unreadChatCount}</span>}
                    </Link>
                    <Link to="/item-requests" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                      Sourcing Requests
                    </Link>
                    <Link to="/payments" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                      Payments
                    </Link>
                    <Link to="/invoices" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                      Invoices & Statements
                    </Link>
                    <Link to="/addresses" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 hover:text-amazon-orange">
                      Shipping Addresses
                    </Link>
                  </>
                ) : (
                  <>
                    <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 font-bold text-amazon-link-teal">
                      Sign In
                    </Link>
                    <Link to="/register" onClick={() => setMobileMenuOpen(false)} className="block py-1.5 text-amazon-orange font-bold">
                      Create Account / Start Selling
                    </Link>
                  </>
                )}
              </div>
            </div>

            {/* Drawer Footer */}
            {token && (
              <div className="p-4 border-t border-gray-200 bg-gray-50">
                <button
                  onClick={() => { logout(); setMobileMenuOpen(false); }}
                  className="w-full py-2 bg-slate-200 hover:bg-slate-300 text-black font-semibold rounded text-xs transition-colors"
                >
                  Sign Out
                </button>
              </div>
            )}
          </aside>
        </div>
      )}
    </header>
  );
};

