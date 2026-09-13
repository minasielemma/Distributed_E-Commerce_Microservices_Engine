import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

const ROUTE_NAME_MAP = {
  '': 'Dashboard',
  'products': 'Products Catalog',
  'categories': 'Categories',
  'inventory': 'Inventory & Stock',
  'orders': 'Orders & Fulfillments',
  'coupons': 'Coupons & Promos',
  'discounts': 'Price Discounts',
  'item-requests': 'Item Requests',
  'chat': 'Customer Chat',
  'media': 'Media Library',
  'finance': 'Finance & Ledger',
  'payments': 'Payments & Audits',
  'invoices': 'Billing & Invoices',
  'notifications': 'Notifications Center',
  'activity': 'Activity Audit Logs',
  'tenants': 'Tenants Governance',
  'subscriptions': 'Subscription Plans'
};

export const Breadcrumbs = ({ customCrumbs, activeTitle }) => {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);

  if (customCrumbs) {
    return (
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400">
        <Link to="/" className="hover:text-purple-400 transition-colors flex items-center gap-1 font-medium">
          <Home size={13} className="text-purple-400" />
          <span>Home</span>
        </Link>
        {customCrumbs.map((crumb, idx) => (
          <React.Fragment key={idx}>
            <ChevronRight size={12} className="text-slate-600 shrink-0" />
            {crumb.path ? (
              <Link to={crumb.path} className="hover:text-purple-400 transition-colors font-medium">
                {crumb.label}
              </Link>
            ) : (
              <span className="font-semibold text-slate-200 truncate">{crumb.label}</span>
            )}
          </React.Fragment>
        ))}
      </nav>
    );
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400">
      <Link to="/" className="hover:text-purple-400 transition-colors flex items-center gap-1 font-medium">
        <Home size={13} className="text-purple-400" />
        <span>Home</span>
      </Link>
      
      {pathSegments.map((segment, index) => {
        const isLast = index === pathSegments.length - 1;
        const routePath = '/' + pathSegments.slice(0, index + 1).join('/');
        const label = activeTitle && isLast ? activeTitle : (ROUTE_NAME_MAP[segment] || segment.replace(/-/g, ' '));

        return (
          <React.Fragment key={routePath}>
            <ChevronRight size={12} className="text-slate-600 shrink-0" />
            {isLast ? (
              <span className="font-bold text-slate-100 capitalize truncate max-w-[200px]">
                {label}
              </span>
            ) : (
              <Link to={routePath} className="hover:text-purple-400 transition-colors font-medium capitalize">
                {label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
