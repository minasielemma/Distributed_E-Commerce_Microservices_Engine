import React, { useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { NotificationProvider } from './context/NotificationContext';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { TenantSelectPage } from './pages/TenantSelectPage';
import { DashboardPage } from './pages/DashboardPage';
import { SuperAdminSubscriptionsPage } from './pages/SuperAdminSubscriptionsPage';
import { ProductsPage } from './pages/ProductsPage';
import { InventoryPage } from './pages/InventoryPage';
import { FinancePage } from './pages/FinancePage';
import { ActivityLogsPage } from './pages/ActivityLogsPage';
import CategoriesPage from './pages/CategoriesPage';
import CouponsPage from './pages/CouponsPage';
import DiscountsPage from './pages/DiscountsPage';
import OrdersPage from './pages/OrdersPage';
import PaymentsPage from './pages/PaymentsPage';
import MediaPage from './pages/MediaPage';
import InvoicesPage from './pages/InvoicesPage';
import NotificationsPage from './pages/NotificationsPage';
import ItemRequestsPage from './pages/ItemRequestsPage';
import { ChatPage } from './pages/ChatPage';

const RoleRoute = ({ allowedRole, children }) => {
  const { isPlatformAdmin } = useContext(AuthContext);

  if (allowedRole === 'platform' && !isPlatformAdmin) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="max-w-md w-full bg-[#131b2e] border border-red-500/20 rounded-2xl p-6 text-center shadow-2xl">
          <h2 className="text-lg font-bold text-red-400">Platform Governance Area</h2>
          <p className="mt-2 text-xs text-slate-400">This page requires Platform Administrator credentials.</p>
        </div>
      </div>
    );
  }

  if (allowedRole === 'store' && isPlatformAdmin) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="max-w-md w-full bg-[#131b2e] border border-purple-500/20 rounded-2xl p-6 text-center shadow-2xl">
          <div className="w-12 h-12 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center mx-auto mb-4 font-bold text-base">
            PA
          </div>
          <h2 className="text-lg font-bold text-white">Platform Governance Mode Active</h2>
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">
            As a Platform Administrator, your portal is focused on common platform objects, tenant subscriptions, global categories, and system governance. Store operational tools belong to tenant store owners.
          </p>
        </div>
      </div>
    );
  }

  return children;
};

const ProtectedLayout = ({ allowedRole, children }) => {
  const { token, loading } = useContext(AuthContext);
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);

  if (loading) return (
    <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center text-slate-400 text-sm font-medium gap-3">
      <div className="w-10 h-10 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
      <span>Loading Enterprise Admin Portal...</span>
    </div>
  );
  if (!token) return <Navigate to="/login" replace />;

  return (
    <div className="flex min-h-screen bg-[#090d16] text-slate-100">
      <Sidebar 
        collapsed={collapsed} 
        setCollapsed={setCollapsed} 
        mobileOpen={mobileOpen} 
        setMobileOpen={setMobileOpen} 
      />
      <div className="flex-1 flex flex-col min-w-0 min-h-screen overflow-x-hidden">
        <Navbar onMobileMenuToggle={() => setMobileOpen(!mobileOpen)} />
        <main className="flex-1 bg-[#090d16] overflow-y-auto">
          <RoleRoute allowedRole={allowedRole}>
            {children}
          </RoleRoute>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <NotificationProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/tenants" element={<ProtectedLayout allowedRole="platform"><TenantSelectPage /></ProtectedLayout>} />
              <Route path="/" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
              <Route path="/categories" element={<ProtectedLayout><CategoriesPage /></ProtectedLayout>} />
              <Route path="/products" element={<ProtectedLayout allowedRole="store"><ProductsPage /></ProtectedLayout>} />
              <Route path="/coupons" element={<ProtectedLayout allowedRole="store"><CouponsPage /></ProtectedLayout>} />
              <Route path="/discounts" element={<ProtectedLayout allowedRole="store"><DiscountsPage /></ProtectedLayout>} />
              <Route path="/orders" element={<ProtectedLayout allowedRole="store"><OrdersPage /></ProtectedLayout>} />
              <Route path="/item-requests" element={<ProtectedLayout allowedRole="store"><ItemRequestsPage /></ProtectedLayout>} />
              <Route path="/chat" element={<ProtectedLayout allowedRole="store"><ChatPage /></ProtectedLayout>} />
              <Route path="/inventory" element={<ProtectedLayout allowedRole="store"><InventoryPage /></ProtectedLayout>} />
              <Route path="/payments" element={<ProtectedLayout allowedRole="platform"><PaymentsPage /></ProtectedLayout>} />
              <Route path="/finance" element={<ProtectedLayout><FinancePage /></ProtectedLayout>} />
              <Route path="/invoices" element={<ProtectedLayout allowedRole="platform"><InvoicesPage /></ProtectedLayout>} />
              <Route path="/media" element={<ProtectedLayout allowedRole="store"><MediaPage /></ProtectedLayout>} />
              <Route path="/notifications" element={<ProtectedLayout><NotificationsPage /></ProtectedLayout>} />
              <Route path="/activity" element={<ProtectedLayout allowedRole="platform"><ActivityLogsPage /></ProtectedLayout>} />
              <Route path="/subscriptions" element={<ProtectedLayout allowedRole="platform"><SuperAdminSubscriptionsPage /></ProtectedLayout>} />
            </Routes>
          </BrowserRouter>
        </NotificationProvider>
      </AuthProvider>
    </ToastProvider>
  );
}

