import React, { useState } from 'react';
import { Store, User, ShieldCheck, Settings, ChevronDown, ChevronUp } from 'lucide-react';

export const parseLogDetails = (details) => {
  if (!details) return {};
  if (typeof details === 'object') return details;
  if (typeof details === 'string') {
    try {
      return JSON.parse(details);
    } catch (e) {
      return { raw: details };
    }
  }
  return {};
};

export const getActionMetadata = (action = '') => {
  const normAction = action.toLowerCase();
  if (normAction.includes('tenant') || normAction.includes('shop')) {
    return {
      label: 'Shop Action',
      icon: Store,
      colorClass: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
    };
  }
  if (normAction.includes('user') || normAction.includes('register') || normAction.includes('profile')) {
    return {
      label: 'User Action',
      icon: User,
      colorClass: 'bg-blue-500/15 text-blue-300 border-blue-500/30'
    };
  }
  if (normAction.includes('subscription') || normAction.includes('admin')) {
    return {
      label: 'Admin Config',
      icon: ShieldCheck,
      colorClass: 'bg-purple-500/15 text-purple-300 border-purple-500/30'
    };
  }
  return {
    label: action.replace(/[._]/g, ' ').toUpperCase(),
    icon: Settings,
    colorClass: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30'
  };
};

export const ActivityLogBadge = ({ action }) => {
  const meta = getActionMetadata(action);
  const IconComponent = meta.icon;
  const formattedAction = action
    ? action
        .split(/[._]/)
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ')
    : 'System Activity';

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${meta.colorClass}`}>
      <IconComponent className="w-3.5 h-3.5" />
      <span>{formattedAction}</span>
    </span>
  );
};

export const ActivityLogDetails = ({ details, compact = false }) => {
  const [showRaw, setShowRaw] = useState(false);
  const parsed = parseLogDetails(details);

  if (!parsed || Object.keys(parsed).length === 0) {
    return <span className="text-slate-400 text-xs italic">No additional details</span>;
  }

  if (parsed.raw) {
    return <span className="text-slate-300 text-xs font-mono">{parsed.raw}</span>;
  }

  // Format known keys into human friendly chips
  const keyLabels = {
    shop_name: 'Shop Name',
    domain: 'Domain',
    tenant_id: 'Tenant ID',
    email: 'Email',
    username: 'Username',
    subscription_tier: 'Tier',
    status: 'Status',
    phone_number: 'Phone',
    address: 'Address',
    has_catalog_access: 'Catalog Access',
    has_inventory_access: 'Inventory Access',
    has_finance_access: 'Finance Access',
    has_payment_access: 'Payment Access',
  };

  const formattedPairs = Object.entries(parsed).map(([key, value]) => {
    const label = keyLabels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
    let formattedVal = value;
    if (typeof value === 'boolean') {
      formattedVal = value ? 'Yes' : 'No';
    } else if (typeof value === 'object' && value !== null) {
      formattedVal = JSON.stringify(value);
    }
    return { key, label, value: String(formattedVal) };
  });

  // Construct primary human sentence if key fields exist
  let primaryText = null;
  if (parsed.shop_name) {
    primaryText = (
      <span>
        Created shop <strong className="text-white font-semibold">{parsed.shop_name}</strong>
        {parsed.domain && <span className="text-cyan-400 ml-1">({parsed.domain})</span>}
      </span>
    );
  } else if (parsed.email || parsed.username) {
    primaryText = (
      <span>
        User <strong className="text-white font-semibold">{parsed.username || parsed.email}</strong> registered
      </span>
    );
  } else if (parsed.subscription_tier) {
    primaryText = (
      <span>
        Configured plan <strong className="text-purple-300 font-semibold">{parsed.subscription_tier}</strong> ({parsed.status || 'Active'})
      </span>
    );
  }

  return (
    <div className="space-y-1.5 py-0.5">
      {primaryText && <div className="text-xs text-slate-200 font-medium">{primaryText}</div>}

      <div className="flex flex-wrap items-center gap-1.5">
        {formattedPairs.map(({ key, label, value }) => (
          <span
            key={key}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] bg-slate-800/80 border border-white/10 text-slate-300"
          >
            <span className="text-slate-400 font-medium">{label}:</span>
            <span className="font-semibold text-slate-100 font-mono text-[11px]">
              {key === 'tenant_id' && value.length > 12 ? `${value.slice(0, 8)}...` : value}
            </span>
          </span>
        ))}

        {!compact && (
          <button
            onClick={() => setShowRaw(!showRaw)}
            className="text-[10px] text-slate-400 hover:text-cyan-400 flex items-center gap-0.5 ml-1 transition-colors"
            title="Toggle raw JSON view"
          >
            {showRaw ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            <span>{showRaw ? 'Hide JSON' : 'JSON'}</span>
          </button>
        )}
      </div>

      {showRaw && (
        <pre className="mt-2 font-mono text-[11px] bg-slate-950/80 p-2 rounded-lg border border-white/10 text-cyan-300 overflow-x-auto">
          {JSON.stringify(parsed, null, 2)}
        </pre>
      )}
    </div>
  );
};
