import React, { useState, useEffect } from 'react';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { ShieldCheck, Sliders, Save, Store } from 'lucide-react';

export const SuperAdminSubscriptionsPage = () => {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [tier, setTier] = useState('STARTER');
  const [status, setStatus] = useState('ACTIVE');
  const [hasCatalog, setHasCatalog] = useState(true);
  const [hasInventory, setHasInventory] = useState(true);
  const [hasFinance, setHasFinance] = useState(true);
  const [hasPayment, setHasPayment] = useState(true);
  const { showSuccess, showError } = useToast();

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      const res = await authService.getTenants();
      const rawData = res.data;
      const tenantList = Array.isArray(rawData) ? rawData : (rawData?.results || []);
      setTenants(tenantList);
      if (tenantList.length > 0 && !selectedTenant) {
        populateForm(tenantList[0]);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const populateForm = (tenant) => {
    setSelectedTenant(tenant);
    setTier(tenant.subscription_tier || 'STARTER');
    setStatus(tenant.status || 'ACTIVE');
    setHasCatalog(tenant.has_catalog_access ?? true);
    setHasInventory(tenant.has_inventory_access ?? true);
    setHasFinance(tenant.has_finance_access ?? true);
    setHasPayment(tenant.has_payment_access ?? true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!selectedTenant) return;
    try {
      await authService.configureTenantSubscription(selectedTenant.id, {
        subscription_tier: tier,
        status: status,
        has_catalog_access: hasCatalog,
        has_inventory_access: hasInventory,
        has_finance_access: hasFinance,
        has_payment_access: hasPayment,
      });
      showSuccess(`Subscription updated for ${selectedTenant.name}`);
      fetchTenants();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Top Header */}
      <div className="bg-[#1e293b] border-b border-[#334155] px-4 md:px-6 py-3">
        <Breadcrumbs items={['System Admin', 'Subscriptions & Feature Flags']} />
        <h1 className="text-xl font-bold text-white flex items-center gap-2 mt-1">
          <ShieldCheck className="text-[#7c7bad] w-6 h-6" />
          <span>SuperAdmin Subscription & Feature Flags</span>
        </h1>
        <p className="text-xs text-[#94a3b8] mt-0.5">
          Configure multi-tenant shop subscription tiers and toggle microservice feature access
        </p>
      </div>

      <div className="px-4 md:px-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tenant Selection List */}
        <div className="app-card p-4">
          <h3 className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider mb-3 flex items-center gap-2">
            <Store size={14} className="text-[#7c7bad]" /> Select Shop Tenant
          </h3>
          <div className="space-y-2">
            {tenants.map((t) => (
              <div
                key={t.id}
                onClick={() => populateForm(t)}
                className={`p-3 rounded cursor-pointer border transition-all ${
                  selectedTenant?.id === t.id
                    ? 'bg-[#7c7bad]/20 border-[#7c7bad] text-white shadow'
                    : 'bg-[#0f172a] border-[#2d3748] hover:bg-[#1e293b] text-slate-300'
                }`}
              >
                <div className="font-bold text-xs text-white">{t.name}</div>
                <div className="text-[11px] text-[#94a3b8] mt-0.5 font-mono">{t.domain}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration Form */}
        {selectedTenant && (
          <div className="app-card p-6 lg:col-span-2 space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white">
                Configure {selectedTenant.name}
              </h3>
              <p className="text-xs text-[#94a3b8] font-mono mt-0.5">
                Tenant ID: {selectedTenant.id}
              </p>
            </div>

            <form onSubmit={handleSave} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1.5">Subscription Tier</label>
                  <select
                    className="app-input"
                    value={tier}
                    onChange={(e) => setTier(e.target.value)}
                  >
                    <option value="STARTER">STARTER TIER ($29/mo)</option>
                    <option value="GROWTH">GROWTH TIER ($99/mo)</option>
                    <option value="ENTERPRISE">ENTERPRISE TIER ($299/mo)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1.5">Shop Status</label>
                  <select
                    className="app-input"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="SUSPENDED">SUSPENDED</option>
                    <option value="CANCELLED">CANCELLED</option>
                  </select>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Sliders size={14} className="text-[#00a09d]" /> Microservice Feature Access Flags
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { label: 'Catalog Service', desc: 'Product catalog & customer likes', state: hasCatalog, set: setHasCatalog },
                    { label: 'Inventory Service', desc: 'Warehouse & stock movements', state: hasInventory, set: setHasInventory },
                    { label: 'Finance Service', desc: 'Accounting ledgers & billing', state: hasFinance, set: setHasFinance },
                    { label: 'Payment Integration', desc: 'Polar.sh checkout gateway', state: hasPayment, set: setHasPayment },
                  ].map((flag, idx) => (
                    <label key={idx} className="flex items-start gap-3 p-3 rounded bg-[#0f172a] border border-[#2d3748] cursor-pointer hover:border-[#7c7bad]">
                      <input
                        type="checkbox"
                        checked={flag.state}
                        onChange={(e) => flag.set(e.target.checked)}
                        className="mt-0.5 w-4 h-4 rounded text-[#7c7bad] focus:ring-[#7c7bad] bg-[#1e293b] border-white/20"
                      />
                      <div>
                        <div className="font-bold text-xs text-white">{flag.label}</div>
                        <div className="text-[11px] text-[#94a3b8] mt-0.5">{flag.desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="app-btn-primary flex items-center gap-2 text-xs"
                >
                  <Save size={14} /> Save Subscription Settings
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

