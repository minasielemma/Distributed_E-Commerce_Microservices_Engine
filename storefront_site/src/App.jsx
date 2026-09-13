import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { ToastProvider } from './context/ToastContext';
import { NotificationProvider } from './context/NotificationContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { StorefrontHome } from './pages/StorefrontHome';
import { ProductDetailPage } from './pages/ProductDetailPage';
import { CartPage } from './pages/CartPage';
import { WishlistPage } from './pages/WishlistPage';
import { ItemRequestsPage } from './pages/ItemRequestsPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { UserProfilePage } from './pages/UserProfilePage';
import OrdersPage from './pages/OrdersPage';
import AddressesPage from './pages/AddressesPage';
import NotificationsPage from './pages/NotificationsPage';
import PaymentsPage from './pages/PaymentsPage';
import InvoicesPage from './pages/InvoicesPage';
import { OrderTrackingPage } from './pages/OrderTrackingPage';
import { ChatPage } from './pages/ChatPage';
import CheckoutSuccessPage from './pages/CheckoutSuccessPage';

function ScrollToTop() {
  const { pathname, search } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname, search]);

  return null;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <NotificationProvider>
          <CartProvider>
            <BrowserRouter>
              <ScrollToTop />
              <div className="flex flex-col min-h-screen">
                <Navbar />
                <main className="flex-1">
                  <Routes>
                    <Route path="/" element={<StorefrontHome />} />
                    <Route path="/products/:id" element={<ProductDetailPage />} />
                    <Route path="/product/:id" element={<ProductDetailPage />} />
                    <Route path="/cart" element={<CartPage />} />
                    <Route path="/checkout/success" element={<CheckoutSuccessPage />} />
                    <Route path="/wishlist" element={<WishlistPage />} />
                    <Route path="/item-requests" element={<ItemRequestsPage />} />
                    <Route path="/chat" element={<ChatPage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/profile" element={<UserProfilePage />} />
                    <Route path="/orders" element={<OrdersPage />} />
                    <Route path="/orders/:id/tracking" element={<OrderTrackingPage />} />
                    <Route path="/orders/track/:trackingCode" element={<OrderTrackingPage />} />
                    <Route path="/addresses" element={<AddressesPage />} />
                    <Route path="/notifications" element={<NotificationsPage />} />
                    <Route path="/payments" element={<PaymentsPage />} />
                    <Route path="/invoices" element={<InvoicesPage />} />
                  </Routes>
                </main>
                <Footer />
              </div>
            </BrowserRouter>
          </CartProvider>
        </NotificationProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
