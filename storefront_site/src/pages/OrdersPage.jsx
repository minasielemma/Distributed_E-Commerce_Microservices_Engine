import React, { useState, useEffect } from 'react';
import { orderService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Modal, LoadingSkeleton, Badge, Pagination } from '../components/common/UIComponents';
import { ShoppingBag, CreditCard, Clock, Eye, CheckCircle, AlertCircle, FileText, Truck, MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';
import { usePagination } from '../hooks/usePagination';

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [payingOrderId, setPayingOrderId] = useState(null);
  const [cancellingOrderId, setCancellingOrderId] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [timeFilter, setTimeFilter] = useState('ALL');
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPage: 1, initialPageSize: 10 });

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await orderService.getOrders({
        page: 1,
        page_size: 100,
      });
      const data = res?.data;
      const list = Array.isArray(data) ? data : (data?.results || data?.orders || []);
      setOrders(Array.isArray(list) ? list : []);
    } catch (err) {
      console.error(err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();

    const handleRealtimeNotification = (e) => {
      const notif = e.detail;
      if (!notif) return;
      const meta = notif.metadata || {};

      if (meta.order_id && meta.status) {
        setOrders((prevOrders) =>
          prevOrders.map((ord) => {
            if (String(ord.id) === String(meta.order_id)) {
              return { ...ord, status: meta.status };
            }
            return ord;
          })
        );
      } else if (notif.notification_type === 'ORDER' || notif.notification_type === 'PAYMENT' || notif.notification_type === 'SHIPMENT') {
        fetchOrders();
      }
    };

    window.addEventListener('notification_received', handleRealtimeNotification);
    return () => window.removeEventListener('notification_received', handleRealtimeNotification);
  }, []);

  const handlePayOrder = async (orderId) => {
    setPayingOrderId(orderId);
    try {
      const res = await orderService.payOrder(orderId);
      showSuccess('Checkout session created! Redirecting to payment...');
      if (res.data?.checkout_url) {
        window.location.href = res.data.checkout_url;
      } else {
        showSuccess('Order payment process initiated.');
        fetchOrders();
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setPayingOrderId(null);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    setCancellingOrderId(orderId);
    try {
      await orderService.cancelOrder(orderId);
      showSuccess('Order cancelled successfully.');
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(null);
      }
      fetchOrders();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setCancellingOrderId(null);
    }
  };

  // Tab Badge Counts
  const allCount = orders.length;
  const notShippedCount = orders.filter(o => ['PENDING', 'UNPAID', 'PAID', 'CONFIRMED', 'PROCESSING'].includes((o.status || '').toUpperCase())).length;
  const paidCount = orders.filter(o => ['PAID', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED'].includes((o.status || '').toUpperCase())).length;
  const shippedCount = orders.filter(o => ['SHIPPED', 'DELIVERED'].includes((o.status || '').toUpperCase())).length;
  const cancelledCount = orders.filter(o => ['CANCELLED', 'FAILED'].includes((o.status || '').toUpperCase())).length;

  // Filter Orders Logic
  const safeOrders = Array.isArray(orders) ? orders : [];
  const getFilteredOrders = () => {
    let result = [...safeOrders];

    // Filter by Time Range
    const now = new Date();
    if (timeFilter === '3months') {
      const cutoff = new Date();
      cutoff.setMonth(now.getMonth() - 3);
      result = result.filter(o => new Date(o.created_at || now) >= cutoff);
    } else if (timeFilter === '6months') {
      const cutoff = new Date();
      cutoff.setMonth(now.getMonth() - 6);
      result = result.filter(o => new Date(o.created_at || now) >= cutoff);
    } else if (timeFilter === 'year') {
      const cutoff = new Date(now.getFullYear(), 0, 1);
      result = result.filter(o => new Date(o.created_at || now) >= cutoff);
    }

    // Filter by Status Tab
    if (statusFilter === 'PENDING') {
      result = result.filter(o => ['PENDING', 'UNPAID', 'PAID', 'CONFIRMED', 'PROCESSING'].includes((o.status || '').toUpperCase()));
    } else if (statusFilter === 'PAID') {
      result = result.filter(o => ['PAID', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED'].includes((o.status || '').toUpperCase()));
    } else if (statusFilter === 'SHIPPED') {
      result = result.filter(o => ['SHIPPED', 'DELIVERED'].includes((o.status || '').toUpperCase()));
    } else if (statusFilter === 'CANCELLED') {
      result = result.filter(o => ['CANCELLED', 'FAILED'].includes((o.status || '').toUpperCase()));
    }

    return result;
  };

  const filteredOrders = getFilteredOrders();

  if (loading) {
    return (
      <div className="w-full bg-white min-h-screen py-6 px-4 md:px-6 text-[#111]">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <h1 className="text-3xl font-normal">Your Orders</h1>
          <LoadingSkeleton count={3} type="table" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white min-h-screen py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-4">
          <h1 className="text-3xl font-normal">Your Orders</h1>
        </div>

        {/* Tabs with exact Counts */}
        <div className="flex flex-wrap gap-6 border-b border-[#D5D9D9] mb-4 text-sm font-normal">
          {[
            { key: 'ALL', label: `Orders (${allCount})` },
            { key: 'PENDING', label: `Not Yet Shipped (${notShippedCount})` },
            { key: 'PAID', label: `PAID (${paidCount})` },
            { key: 'SHIPPED', label: `SHIPPED (${shippedCount})` },
            { key: 'CANCELLED', label: `Cancelled Orders (${cancelledCount})` },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`pb-2 px-1 text-sm ${
                statusFilter === tab.key
                  ? 'border-b-2 border-[#e77600] font-bold text-[#111]'
                  : 'text-amazon-link-teal hover:text-amazon-orange hover:underline'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Time Range Selector */}
        <div className="mb-6 flex items-center gap-2 text-sm text-[#565959]">
          <span className="font-bold text-[#111]">{filteredOrders.length} order(s)</span> placed in
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value)}
            className="font-bold border border-[#D5D9D9] bg-[#F0F2F2] px-3 py-1 rounded cursor-pointer text-xs focus:outline-none text-[#111]"
          >
            <option value="ALL">all time</option>
            <option value="3months">past 3 months</option>
            <option value="6months">past 6 months</option>
            <option value="year">2026</option>
          </select>
        </div>

        {/* Empty States */}
        {filteredOrders.length === 0 ? (
          orders.length > 0 && statusFilter !== 'ALL' ? (
            <div className="py-10 text-center bg-[#F9F9F9] border border-[#D5D9D9] rounded-lg p-6 space-y-3">
              <p className="text-base text-[#111]">
                No {statusFilter === 'CANCELLED' ? 'cancelled' : statusFilter === 'PENDING' ? 'unshipped' : statusFilter.toLowerCase()} orders found in this filter view.
              </p>
              <p className="text-sm text-[#565959]">
                You have <span className="font-bold text-[#111]">{orders.length}</span> total order(s) available in your account.
              </p>
              <button 
                onClick={() => { setStatusFilter('ALL'); setTimeFilter('ALL'); }}
                className="btn-buy-now px-6 py-2 rounded text-sm shadow-sm font-semibold mt-2"
              >
                View All Orders ({orders.length})
              </button>
            </div>
          ) : (
            <div className="py-12 text-center bg-[#F9F9F9] border border-[#D5D9D9] rounded-lg p-8 space-y-4">
              <div className="w-16 h-16 rounded-full bg-[#F0F2F2] border border-[#D5D9D9] mx-auto flex items-center justify-center text-[#565959]">
                <ShoppingBag className="w-8 h-8 opacity-40 text-[#111]" />
              </div>
              <p className="text-lg font-medium text-[#111]">Looks like you haven't placed an order yet.</p>
              <Link to="/" className="btn-buy-now px-6 py-2 inline-block rounded text-sm font-semibold shadow-sm">
                Start Shopping
              </Link>
            </div>
          )
        ) : (
          <div className="space-y-6">
            {filteredOrders.map((order) => {
              const orderDate = new Date(order.created_at || Date.now()).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
              const totalAmount = Number(order.total_amount || order.total || 0).toFixed(2);
              
              return (
                <div key={order.id} className="border border-[#D5D9D9] rounded-lg overflow-hidden bg-white">
                  {/* Order Header */}
                  <div className="bg-[#F0F2F2] border-b border-[#D5D9D9] p-4 flex flex-wrap justify-between gap-4 text-sm text-[#565959]">
                    <div className="flex flex-wrap gap-4 sm:gap-8">
                      <div>
                        <div className="font-bold text-[#565959] uppercase text-xs mb-1">Order Placed</div>
                        <div>{orderDate}</div>
                      </div>
                      <div>
                        <div className="font-bold text-[#565959] uppercase text-xs mb-1">Total</div>
                        <div className="font-bold text-[#111]">${totalAmount}</div>
                      </div>
                      <div>
                        <div className="font-bold text-[#565959] uppercase text-xs mb-1">Ship To</div>
                        <div className="text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
                          {typeof order.shipping_address === 'string' ? order.shipping_address : (order.shipping_address?.full_name || 'Customer')} <span>▾</span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right flex flex-col items-end">
                      <div className="font-bold text-[#565959] uppercase text-xs mb-1">Order # {order.id}</div>
                      <div className="flex gap-2 text-amazon-link-teal text-xs">
                        <button onClick={() => setSelectedOrder(order)} className="hover:text-amazon-orange hover:underline font-semibold">View order details</button>
                      </div>
                    </div>
                  </div>

                  {/* Order Body */}
                  <div className="p-4 bg-white flex flex-col md:flex-row gap-6">
                    <div className="flex-1 space-y-4">
                      <div className="flex items-center gap-3">
                        <h3 className="font-bold text-lg text-[#111]">
                          {order.status === 'DELIVERED' ? 'Delivered' : 
                           order.status === 'SHIPPED' ? 'Shipped' : 
                           order.status === 'CANCELLED' ? 'Cancelled' : 
                           'Arriving soon / Processing'}
                        </h3>
                        <Badge status={order.status || 'PENDING'} />
                      </div>
                      
                      {(order.items || []).map((item, idx) => (
                        <div key={idx} className="flex gap-4">
                          <div className="w-20 h-20 bg-[#F0F2F2] border border-[#D5D9D9] shrink-0 flex items-center justify-center rounded">
                             {item.image_url ? (
                               <img src={item.image_url} alt={item.product_name} className="max-w-full max-h-full object-contain mix-blend-multiply" />
                             ) : (
                               <ShoppingBag className="w-8 h-8 opacity-20 text-[#111]" />
                             )}
                          </div>
                          <div>
                            <Link to={`/products/${item.product_id}`} className="text-amazon-link-teal hover:text-amazon-orange hover:underline font-bold block mb-1">
                              {item.product_name || `Product #${item.product_id}`}
                            </Link>
                            <div className="text-xs text-[#565959] mb-1">Quantity: {item.quantity}</div>
                            <div className="text-sm flex gap-2">
                               <Link to={`/products/${item.product_id}`} className="btn-secondary py-1 px-3 text-xs">View item details</Link>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="w-full md:w-64 space-y-2 shrink-0 flex flex-col">
                      <Link to={`/orders/${order.id}/tracking`} className="btn-secondary py-1.5 w-full text-center text-sm mb-1 shadow-sm font-normal">Track package</Link>
                      
                      {['PENDING', 'UNPAID', 'CREATED'].includes((order.status || '').toUpperCase()) && (
                        <button onClick={() => handlePayOrder(order.id)} disabled={payingOrderId === order.id} className="btn-buy-now py-1.5 w-full text-sm shadow-sm">
                          {payingOrderId === order.id ? 'Processing...' : 'Pay Now'}
                        </button>
                      )}

                      {!['CANCELLED', 'FAILED', 'DELIVERED'].includes((order.status || '').toUpperCase()) && (
                        <button onClick={() => handleCancelOrder(order.id)} disabled={cancellingOrderId === order.id} className="btn-secondary py-1.5 w-full text-sm shadow-sm text-[#111]">
                          {cancellingOrderId === order.id ? 'Cancelling...' : 'Cancel Order'}
                        </button>
                      )}
                      
                      <Link to={`/chat?orderId=${order.id}`} className="btn-secondary py-1.5 w-full text-center text-sm shadow-sm font-normal">Get product support</Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Order Detail Modal */}
        {selectedOrder && (
          <Modal
            isOpen={!!selectedOrder}
            onClose={() => setSelectedOrder(null)}
            title={`Order Details`}
            maxWidth="max-w-3xl"
          >
            <div className="space-y-4 text-[#111]">
              <div className="flex justify-between items-center border-b border-[#D5D9D9] pb-3">
                 <div className="font-bold text-lg">Order# {selectedOrder.id}</div>
                 <div className="font-bold text-lg text-[#c40000]">${Number(selectedOrder.total_amount || selectedOrder.total || 0).toFixed(2)}</div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm pt-2">
                <div className="border border-[#D5D9D9] p-4 rounded bg-[#F0F2F2]">
                  <div className="font-bold mb-2">Shipping Address</div>
                  <div>
                    {typeof selectedOrder.shipping_address === 'string'
                      ? selectedOrder.shipping_address
                      : selectedOrder.shipping_address
                      ? `${selectedOrder.shipping_address.street || ''}, ${selectedOrder.shipping_address.city || ''}, ${selectedOrder.shipping_address.country || ''}`
                      : 'N/A'}
                  </div>
                </div>
                <div className="border border-[#D5D9D9] p-4 rounded bg-[#F0F2F2]">
                  <div className="font-bold mb-2">Payment Method</div>
                  <div>Visa ending in ****</div>
                </div>
              </div>

              <div className="mt-4 border border-[#D5D9D9] rounded">
                <div className="bg-[#F0F2F2] p-3 border-b border-[#D5D9D9] font-bold text-sm">Order Summary</div>
                <div className="p-3 overflow-x-auto">
                  <table className="w-full text-left text-sm min-w-[400px]">
                    <thead>
                      <tr className="border-b border-[#D5D9D9] text-[#565959]">
                        <th className="pb-2">Items</th>
                        <th className="pb-2 text-right">Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedOrder.items || []).map((item, idx) => (
                        <tr key={idx} className="border-b border-[#D5D9D9] last:border-0">
                          <td className="py-3">
                            <span className="font-bold text-amazon-link-teal">{item.product_name || `Product #${item.product_id}`}</span> <br/>
                            <span className="text-xs text-[#565959]">Qty: {item.quantity}</span>
                          </td>
                          <td className="py-3 text-right font-bold text-[#c40000]">
                            ${(Number(item.quantity || 1) * Number(item.unit_price || item.price || 0)).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button onClick={() => setSelectedOrder(null)} className="btn-secondary py-1.5 px-4 text-sm shadow-sm">
                  Close window
                </button>
              </div>
            </div>
          </Modal>
        )}
      </div>
    </div>
  );
}
