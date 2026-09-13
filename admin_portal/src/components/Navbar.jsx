import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { authService } from '../services/apiServices';
import { LogOut, Store, Menu, Building2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { NotificationBell } from './NotificationBell';

export const Navbar = ({ onMobileMenuToggle }) => {
  const { user, logout, activeTenant, selectTenant, isPlatformAdmin } = useContext(AuthContext);
  const [tenants, setTenants] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      fetchTenants();
    }
  }, [user]);

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

  const handleTenantSelectChange = (e) => {
    const selectedId = e.target.value;
    if (!selectedId) {
      selectTenant(null);
    } else {
      const tenantObj = tenants.find((t) => String(t.id) === String(selectedId));
      selectTenant(tenantObj || null);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800/90 px-3 sm:px-4 md:px-6 flex items-center justify-between bg-[#0f172a]/95 backdrop-blur-xl sticky top-0 z-30 shadow-sm gap-2">
      <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
        {/* Mobile Hamburger Toggle Button */}
        <button
          onClick={onMobileMenuToggle}
          className="lg:hidden p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors shrink-0 touch-target"
          title="Toggle Navigation Menu"
        >
          <Menu size={18} />
        </button>

        {/* Active Shop Context Dropdown */}
        <div className="flex items-center gap-1.5 sm:gap-2 bg-slate-900/90 border border-slate-800 rounded-lg px-2 sm:px-3 py-1.5 text-xs text-white shadow-inner min-w-0 max-w-[170px] xs:max-w-[210px] sm:max-w-[280px]">
          <Building2 size={15} className="text-purple-400 shrink-0" />
          <span className="font-semibold text-slate-400 hidden sm:inline shrink-0">Active Context:</span>
          <select
            className="bg-transparent font-extrabold text-teal-300 focus:outline-none cursor-pointer w-full truncate text-[11px] sm:text-xs"
            value={activeTenant?.id || ''}
            onChange={handleTenantSelectChange}
          >
            <option value="" className="bg-slate-900 text-purple-300">All Shops (Global View)</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id} className="bg-slate-900 text-white">
                {t.name} ({t.domain})
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => navigate('/tenants')}
          className="hidden sm:flex px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-all items-center gap-1.5 shrink-0"
        >
          <Store size={14} className="text-purple-400" />
          <span>{isPlatformAdmin ? 'Tenants Directory' : 'Manage Shops'}</span>
        </button>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <NotificationBell />

        {user && (
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800/80 rounded-lg px-2 sm:px-2.5 py-1">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
              isPlatformAdmin ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50' : 'bg-teal-500/20 text-teal-300 border border-teal-500/40'
            }`}>
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div className="hidden md:block text-left min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-slate-100 truncate">{user.username}</span>
                {isPlatformAdmin && (
                  <span className="px-1.5 py-0.2 rounded text-[8px] font-black bg-purple-500/30 text-purple-300 border border-purple-500/40 shrink-0">
                    SUPERADMIN
                  </span>
                )}
              </div>
              <div className="text-[10px] text-slate-400 font-mono truncate max-w-[130px]">{user.email}</div>
            </div>
          </div>
        )}

        <button
          onClick={logout}
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-rose-500/20 hover:text-rose-400 border border-slate-700 text-slate-300 transition-colors shrink-0"
          title="Logout"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
};


