import React, { useState, useEffect, useContext } from 'react';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { Store, Plus, ArrowRight, CheckCircle2, Building2 } from 'lucide-react';

export const TenantSelectPage = () => {
  const [tenants, setTenants] = useState([]);
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [tier, setTier] = useState('STARTER');
  const [showCreate, setShowCreate] = useState(false);
  const { selectTenant, activeTenant } = useContext(AuthContext);
  const { showSuccess, showError } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      const res = await authService.getTenants();
      const rawData = res.data;
      const tenantList = Array.isArray(rawData) ? rawData : (rawData?.results || []);
      setTenants(tenantList);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    try {
      const res = await authService.createTenant({
        name,
        domain,
        subscription_tier: tier,
      });
      showSuccess(`Shop "${name}" created successfully!`);
      selectTenant(res.data);
      setName('');
      setDomain('');
      setShowCreate(false);
      fetchTenants();
      navigate('/');
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleSelect = (tenant) => {
    selectTenant(tenant);
    showSuccess(`Switched to active shop: ${tenant.name}`);
    navigate('/');
  };

  return (
    <div className="w-full space-y-4">
      {/* Top Control Bar */}
      <div className="bg-[#1e293b] border-b border-[#334155] px-4 md:px-6 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <Breadcrumbs items={['Multi-Company', 'Shop Selector']} />
          <h1 className="text-xl font-bold text-white flex items-center gap-2 mt-1">
            <Building2 className="text-[#7c7bad] w-6 h-6" />
            <span>Manage Shop Tenants</span>
          </h1>
          <p className="text-xs text-[#94a3b8] mt-0.5">Select an active store context or register a new multi-tenant shop</p>
        </div>

        <button
          onClick={() => setShowCreate(!showCreate)}
          className="app-btn-primary inline-flex items-center gap-1.5 text-xs shrink-0 self-start sm:self-auto"
        >
          <Plus size={14} /> {showCreate ? 'Close Register Form' : 'Create New Shop'}
        </button>
      </div>

      <div className="px-4 md:px-6 space-y-4">
        {showCreate && (
          <div className="app-card p-5 border-[#7c7bad]">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Register New E-Commerce Shop</h3>
            <form onSubmit={handleCreateTenant} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1.5">Shop Name</label>
                <input
                  type="text"
                  className="app-input"
                  placeholder="e.g. Apex Tech Store"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1.5">Subdomain</label>
                <input
                  type="text"
                  className="app-input font-mono"
                  placeholder="apextech.saas.com"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1.5">Subscription Tier</label>
                <select
                  className="app-input"
                  value={tier}
                  onChange={(e) => setTier(e.target.value)}
                >
                  <option value="STARTER">Starter Tier</option>
                  <option value="GROWTH">Growth Tier</option>
                  <option value="ENTERPRISE">Enterprise Tier</option>
                </select>
              </div>
              <button
                type="submit"
                className="app-btn-teal text-xs py-2"
              >
                Launch Shop
              </button>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tenants.map((tenant) => {
            const isSelected = activeTenant?.id === tenant.id;
            return (
              <div
                key={tenant.id}
                className={`app-card p-5 relative transition-all ${
                  isSelected ? 'border-2 border-[#7c7bad] bg-[#7c7bad]/10' : 'hover:border-[#7c7bad]/50'
                }`}
              >
                {isSelected && (
                  <div className="absolute top-4 right-4 text-[#7c7bad]">
                    <CheckCircle2 size={20} />
                  </div>
                )}
                <div className="w-10 h-10 rounded bg-[#7c7bad]/20 border border-[#7c7bad]/30 flex items-center justify-center text-[#7c7bad] mb-3">
                  <Store size={20} />
                </div>
                <h3 className="text-base font-bold text-white">{tenant.name}</h3>
                <p className="text-xs text-[#94a3b8] mt-0.5 font-mono">{tenant.domain}</p>

                <div className="flex gap-2 my-4">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#00a09d]/20 text-[#00a09d] border border-[#00a09d]/30 font-mono uppercase">
                    {tenant.subscription_tier}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#48bb78]/20 text-[#48bb78] border border-[#48bb78]/30 font-mono uppercase">
                    {tenant.status}
                  </span>
                </div>

                <button
                  onClick={() => handleSelect(tenant)}
                  className={`w-full py-2 px-3 rounded font-bold text-xs flex items-center justify-center gap-1.5 transition-all ${
                    isSelected
                      ? 'bg-white/10 text-white border border-white/20'
                      : 'app-btn-primary'
                  }`}
                >
                  {isSelected ? 'Active Shop' : 'Select Shop'} <ArrowRight size={14} />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

