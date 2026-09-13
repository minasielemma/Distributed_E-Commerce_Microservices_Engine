import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../services/api';
import { DollarSign, ShoppingBag, Boxes, Shield, Activity, TrendingUp, Store, ArrowRight, AlertCircle, PackageSearch } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ActivityLogBadge, ActivityLogDetails } from '../components/ActivityLogFormatter';
import { cartService } from '../services/apiServices';
import { ControlPanel, DataTable } from '../components/common/UIComponents';

export const DashboardPage = () => {
  const { activeTenant, isPlatformAdmin } = useContext(AuthContext);
  const [ledger, setLedger] = useState(null);
  const [productsCount, setProductsCount] = useState(0);
  const [tenants, setTenants] = useState([]);
  const [itemRequestsStats, setItemRequestsStats] = useState({ total: 0, pending: 0 });
  const [activityLogs, setActivityLogs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, [activeTenant, isPlatformAdmin]);

  const fetchDashboardData = async () => {
    try {
      if (isPlatformAdmin) {
        const tenantsRes = await api.get('/auth/tenants/').catch(() => null);
        if (tenantsRes) {
          const list = Array.isArray(tenantsRes.data) ? tenantsRes.data : (tenantsRes.data?.results || []);
          setTenants(list);
        }
      }

      const ledgerRes = await api.get('/finance/ledger/').catch(() => null);
      if (ledgerRes) setLedger(ledgerRes.data);

      const prodRes = await api.get('/catalog/products/').catch(() => null);
      if (prodRes) {
        const count = typeof prodRes.data?.count === 'number' 
          ? prodRes.data.count 
          : (Array.isArray(prodRes.data) ? prodRes.data.length : 0);
        setProductsCount(count);
      }

      const reqStatsRes = await cartService.getItemRequestStats({ scope: 'shop' }).catch(() => null);
      if (reqStatsRes) setItemRequestsStats(reqStatsRes.data || { total: 0, pending: 0 });

      const logsRes = await api.get('/auth/activity/').catch(() => null);
      if (logsRes) {
        const logsList = Array.isArray(logsRes.data) ? logsRes.data : (logsRes.data?.results || []);
        setActivityLogs(logsList.slice(0, 5));
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (isPlatformAdmin) {
    return (
      <div className="w-full pb-12">
        <ControlPanel
          title="Platform Governance Dashboard"
          subtitle="SuperAdmin System Scope"
          primaryAction={{
            label: 'Tenants Directory',
            icon: Store,
            onClick: () => navigate('/tenants')
          }}
          secondaryActions={[
            { label: 'Subscription Plans', icon: Shield, onClick: () => navigate('/subscriptions') },
            { label: 'Platform Finance', icon: DollarSign, onClick: () => navigate('/finance') }
          ]}
          onRefresh={fetchDashboardData}
        />

        <div className="p-4 md:p-8 space-y-6">
          {/* Platform Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="app-card p-5 relative overflow-hidden border-purple-500/30">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Registered Tenants</span>
                <div className="p-2 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  <Store size={18} />
                </div>
              </div>
              <div className="text-2xl font-black text-white">{tenants.length || 1}</div>
              <div className="text-xs text-purple-300 mt-2 font-semibold">Active SaaS Tenants & Stores</div>
            </div>

            <div className="app-card p-5 relative overflow-hidden border-emerald-500/30">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Platform GMV Revenue</span>
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  <DollarSign size={18} />
                </div>
              </div>
              <div className="text-2xl font-black text-white">${ledger?.total_sales_revenue || '0.00'}</div>
              <div className="text-xs font-bold text-emerald-400 mt-2 flex items-center gap-1">
                <TrendingUp size={13} /> Platform-wide volume
              </div>
            </div>

            <div className="app-card p-5 relative overflow-hidden border-indigo-500/30">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Common Taxonomies</span>
                <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  <Boxes size={18} />
                </div>
              </div>
              <div className="text-2xl font-black text-white">Global Categories</div>
              <div className="text-xs text-slate-400 mt-2 font-medium">Platform Object Standards</div>
            </div>

            <div className="app-card p-5 relative overflow-hidden border-cyan-500/30">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Security Audit Logs</span>
                <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  <Activity size={18} />
                </div>
              </div>
              <div className="text-2xl font-black text-white">{activityLogs.length}</div>
              <div className="text-xs text-slate-400 mt-2 font-medium">Recent Audit Events</div>
            </div>
          </div>

          {/* Governance Quick Modules */}
          <div className="app-card p-6 space-y-4">
            <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">Governance Modules</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <button
                onClick={() => navigate('/tenants')}
                className="p-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">Multi-Tenant Governance</div>
                <div className="text-sm font-extrabold text-white mt-1 group-hover:text-purple-300">Tenants & Shop Accounts &rarr;</div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">Approve, suspend, or configure tenant shop permissions.</p>
              </button>
              <button
                onClick={() => navigate('/subscriptions')}
                className="p-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Subscription Engine</div>
                <div className="text-sm font-extrabold text-white mt-1 group-hover:text-indigo-300">Tiers & Feature Flags &rarr;</div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">Manage STARTER, GROWTH, and ENTERPRISE tenant tiers.</p>
              </button>
              <button
                onClick={() => navigate('/categories')}
                className="p-4 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-left transition-all group"
              >
                <div className="text-[10px] font-bold text-teal-400 uppercase tracking-wider">Common Platform Objects</div>
                <div className="text-sm font-extrabold text-white mt-1 group-hover:text-teal-300">Global Categories & Taxonomies &rarr;</div>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">Define platform-wide categories, attributes, and taxonomies.</p>
              </button>
            </div>
          </div>

          {/* Audit Trail Table */}
          <div>
            <div className="flex items-center justify-between mb-2 px-1">
              <h3 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                <Activity size={16} className="text-purple-400" /> Recent Security Audit Events
              </h3>
              <button onClick={() => navigate('/activity')} className="text-xs font-semibold text-purple-400 hover:underline">
                View All Activity Logs &rarr;
              </button>
            </div>

            <DataTable headers={['Action', 'Details', 'Timestamp']}>
              {activityLogs.map((log, idx) => (
                <tr key={idx}>
                  <td className="w-48 align-top">
                    <ActivityLogBadge action={log.action} />
                  </td>
                  <td className="align-top">
                    <ActivityLogDetails details={log.details} />
                  </td>
                  <td className="w-44 text-slate-400 font-mono text-[11px] align-top whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))}
            </DataTable>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full pb-12">
      <ControlPanel
        title="Store Operations Dashboard"
        subtitle={activeTenant ? activeTenant.name : 'Merchant Portal'}
        primaryAction={{
          label: 'Products Catalog',
          icon: ShoppingBag,
          onClick: () => navigate('/products')
        }}
        secondaryActions={[
          { label: 'Orders Fulfillments', icon: PackageSearch, onClick: () => navigate('/orders') },
          { label: 'Inventory Stock', icon: Boxes, onClick: () => navigate('/inventory') }
        ]}
        onRefresh={fetchDashboardData}
      />

      <div className="p-4 md:p-8 space-y-6">
        {/* Active Shop Indicator Banner */}
        {!activeTenant ? (
          <div className="app-card p-5 border-amber-500/30 bg-amber-500/10 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 shrink-0">
                <AlertCircle size={22} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">No Active Shop Currently Selected</h3>
                <p className="text-xs text-slate-300">Select a shop context or register a new tenant to manage products, orders, and ledger data.</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/tenants')}
              className="app-btn-primary shrink-0"
            >
              <Store size={14} /> Select / Create Shop <ArrowRight size={13} />
            </button>
          </div>
        ) : (
          <div className="app-card p-5 border-purple-500/30 bg-gradient-to-r from-purple-950/20 to-slate-900 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30 shrink-0">
                <Store size={24} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-extrabold text-purple-400 uppercase tracking-wider">Active Shop Context</span>
                  <span className="px-2 py-0.5 rounded-full text-[9px] font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {activeTenant.status}
                  </span>
                </div>
                <h2 className="text-xl font-black text-white">{activeTenant.name}</h2>
                <p className="text-xs text-slate-400 font-mono">Domain: {activeTenant.domain} | Tier: {activeTenant.subscription_tier}</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/tenants')}
              className="app-btn-secondary shrink-0"
            >
              <Store size={14} /> Switch Active Shop
            </button>
          </div>
        )}

        {/* Metrics Summary Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="app-card p-5 relative overflow-hidden border-emerald-500/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Revenue</span>
              <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <DollarSign size={18} />
              </div>
            </div>
            <div className="text-2xl font-black text-white">${ledger?.total_sales_revenue || '0.00'}</div>
            <div className="text-xs font-bold text-emerald-400 mt-2 flex items-center gap-1">
              <TrendingUp size={13} /> Real-time ledger tracking
            </div>
          </div>

          <div className="app-card p-5 relative overflow-hidden border-purple-500/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Catalog SKUs</span>
              <div className="p-2 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30">
                <ShoppingBag size={18} />
              </div>
            </div>
            <div className="text-2xl font-black text-white">{productsCount}</div>
            <div className="text-xs text-slate-400 mt-2 font-medium">Active Products</div>
          </div>

          <div className="app-card p-5 relative overflow-hidden border-teal-500/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Item Requests</span>
              <div className="p-2 rounded-lg bg-teal-500/20 text-teal-300 border border-teal-500/30">
                <PackageSearch size={18} />
              </div>
            </div>
            <div className="text-2xl font-black text-white">{itemRequestsStats.total}</div>
            <div className="text-xs font-bold text-amber-400 mt-2">{itemRequestsStats.pending} pending review</div>
          </div>

          <div className="app-card p-5 relative overflow-hidden border-cyan-500/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Available Payout</span>
              <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                <DollarSign size={18} />
              </div>
            </div>
            <div className="text-2xl font-black text-white">${ledger?.available_payout_balance || '0.00'}</div>
            <div className="text-xs text-slate-400 mt-2 font-medium">Ready for Payout</div>
          </div>

          <div className="app-card p-5 relative overflow-hidden border-indigo-500/30">
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Subscription Tier</span>
              <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                <Shield size={18} />
              </div>
            </div>
            <div className="text-xl font-black text-white truncate">{activeTenant?.subscription_tier || 'N/A'}</div>
            <div className="text-xs font-bold text-emerald-400 mt-2">Status: {activeTenant?.status || 'Active'}</div>
          </div>
        </div>

        {/* Permissions Grid */}
        <div className="app-card p-5 space-y-3">
          <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider">Enabled Microservice Permissions</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: 'Catalog Service', active: activeTenant?.has_catalog_access },
              { label: 'Inventory Service', active: activeTenant?.has_inventory_access },
              { label: 'Finance Service', active: activeTenant?.has_finance_access },
              { label: 'Payment (Polar)', active: activeTenant?.has_payment_access },
            ].map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex justify-between items-center">
                <span className="text-xs font-semibold text-slate-200">{item.label}</span>
                <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold uppercase ${
                  item.active
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                }`}>
                  {item.active ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity Table */}
        <div>
          <div className="flex items-center justify-between mb-2 px-1">
            <h3 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity size={16} className="text-teal-400" /> Recent Audit Activity Stream
            </h3>
          </div>

          <DataTable 
            headers={['Action', 'Details', 'Timestamp']}
            isEmpty={activityLogs.length === 0}
            emptyStateProps={{ title: 'No activity logs', description: 'No recent store operational activity logged yet.' }}
          >
            {activityLogs.map((log, idx) => (
              <tr key={idx}>
                <td className="w-48 align-top">
                  <ActivityLogBadge action={log.action} />
                </td>
                <td className="align-top">
                  <ActivityLogDetails details={log.details} />
                </td>
                <td className="w-44 text-slate-400 font-mono text-[11px] align-top whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
              </tr>
            ))}
          </DataTable>
        </div>
      </div>
    </div>
  );
};


