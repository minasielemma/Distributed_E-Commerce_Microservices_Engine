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
      colorClass: 'bg-[#E8F5E9] text-[#2E7D32] border-[#2E7D32]'
    };
  }
  if (normAction.includes('user') || normAction.includes('register') || normAction.includes('profile')) {
    return {
      label: 'User Action',
      icon: User,
      colorClass: 'bg-[#F3E5F5] text-[#7B1FA2] border-[#7B1FA2]'
    };
  }
  if (normAction.includes('subscription') || normAction.includes('admin')) {
    return {
      label: 'Admin Config',
      icon: ShieldCheck,
      colorClass: 'bg-[#E8EAF6] text-[#303F9F] border-[#303F9F]'
    };
  }
  return {
    label: action.replace(/[._]/g, ' ').toUpperCase(),
    icon: Settings,
    colorClass: 'bg-[#E3F2FD] text-[#1976D2] border-[#1976D2]'
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
    return <span className="text-amazon-text-secondary text-xs italic">System event / activity</span>;
  }

  if (parsed.raw) {
    return <span className="text-[#111] text-xs font-mono">{parsed.raw}</span>;
  }

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

  let primaryText = null;
  if (parsed.shop_name) {
    primaryText = (
      <span>
        Created shop <strong className="text-[#111] font-bold">{parsed.shop_name}</strong>
        {parsed.domain && <span className="text-amazon-link-teal ml-1">({parsed.domain})</span>}
      </span>
    );
  } else if (parsed.email || parsed.username) {
    primaryText = (
      <span>
        User <strong className="text-[#111] font-bold">{parsed.username || parsed.email}</strong> registered
      </span>
    );
  }

  return (
    <div className="space-y-1.5 py-0.5">
      {primaryText && <div className="text-xs text-[#111] font-medium">{primaryText}</div>}

      <div className="flex flex-wrap items-center gap-1.5">
        {formattedPairs.map(({ key, label, value }) => (
          <span
            key={key}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] bg-[#F0F2F2] border border-[#D5D9D9] text-[#111]"
          >
            <span className="text-amazon-text-secondary font-medium">{label}:</span>
            <span className="font-bold text-[#111] font-mono text-[11px]">
              {key === 'tenant_id' && value.length > 12 ? `${value.slice(0, 8)}...` : value}
            </span>
          </span>
        ))}

        {!compact && (
          <button
            onClick={() => setShowRaw(!showRaw)}
            className="text-[10px] text-amazon-text-secondary hover:text-amazon-orange flex items-center gap-0.5 ml-1 transition-colors"
            title="Toggle raw JSON view"
          >
            {showRaw ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            <span>{showRaw ? 'Hide JSON' : 'JSON'}</span>
          </button>
        )}
      </div>

      {showRaw && (
        <pre className="mt-2 font-mono text-[11px] bg-[#F0F2F2] p-2 rounded-lg border border-[#D5D9D9] text-[#111] overflow-x-auto">
          {JSON.stringify(parsed, null, 2)}
        </pre>
      )}
    </div>
  );
};
