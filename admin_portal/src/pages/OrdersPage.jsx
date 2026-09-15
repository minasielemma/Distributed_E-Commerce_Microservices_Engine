import React, { useState, useEffect, useCallback, useContext } from 'react';
import { orderService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { AuthContext } from '../context/AuthContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, Modal, EmptyState, LoadingSkeleton, Badge, Pagination } from '../components/common/UIComponents';
import { ShipmentCard, ShipmentStatusModal } from '../components/ShipmentComponents';
import { ShoppingBag, Eye, CreditCard, Activity, RefreshCw, ArrowRight, Truck, CheckCircle2, PackageCheck, Edit } from 'lucide-react';

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [outboxEvents, setOutboxEvents] = useState([]);
  const [activeTab, setActiveTab] = useState('orders');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderShipments, setOrderShipments] = useState([]);
  const [editingShipment, setEditingShipment] = useState(null);
  const [dispatchModalOrder, setDispatchModalOrder] = useState(null);
  const [carrier, setCarrier] = useState('Standard Delivery');
  const [availableCarriers, setAvailableCarriers] = useState(['Standard Delivery', 'FedEx', 'UPS', 'USPS', 'DHL']);
  const [trackingCode, setTrackingCode] = useState('');

  useEffect(() => {
    orderService.getAvailableCarriers()
      .then(res => {
        const names = res?.data?.names || (Array.isArray(res?.data?.carriers) ? res.data.carriers.map(c => c.name) : null);
        if (names && names.length > 0) {
          setAvailableCarriers(names);
        }
      })
      .catch(err => {
        console.warn('Could not fetch available carriers dynamically:', err);
      });
  }, []);
  const [dispatchingId, setDispatchingId] = useState(null);
  const [updatingShipment, setUpdatingShipment] = useState(false);
  const { showSuccess, showError } = useToast();
  const { activeTenant } = useContext(AuthContext);

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange, resetPage } = pagination;

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const tenantId = activeTenant?.id;
      const params = {
        page,
        page_size: pageSize,
      };

      if (tenantId) {
        params.tenant_id = tenantId;
      }

      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }

      const res = await orderService.getOrders(params);
      const data = res?.data;
      const list = Array.isArray(data) ? data : (data?.results || data?.orders || []);
      setOrders(Array.isArray(list) ? list : []);

      if (data?.count !== undefined) {
        updatePaginationState(data.count, page);
      } else {
        updatePaginationState(list.length, page);
      }
    } catch (err) {
      console.error(err);
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, activeTenant, showError, updatePaginationState]);

  const fetchOutbox = async () => {
    setOutboxLoading(true);
    try {
      const res = await orderService.getOutboxEvents();
      const list = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setOutboxEvents(list);
    } catch (err) {
      console.error(err);
      showError(getErrorMessage(err));
    } finally {
      setOutboxLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'orders') {
      fetchOrders();
    }

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
        if (activeTab === 'orders') fetchOrders();
      }
    };

    window.addEventListener('notification_received', handleRealtimeNotification);
    return () => window.removeEventListener('notification_received', handleRealtimeNotification);
  }, [fetchOrders, activeTab]);

  useEffect(() => {
    if (activeTab === 'outbox') {
      fetchOutbox();
    }
  }, [activeTab]);

  const openDispatchModal = (order) => {
    setDispatchModalOrder(order);
    setCarrier('Standard Delivery');
    setTrackingCode(`TRK-${Math.random().toString(36).substring(2, 10).toUpperCase()}`);
  };

  const handleDispatchOrder = async (e) => {
    if (e) e.preventDefault();
    if (!dispatchModalOrder) return;
    const orderId = dispatchModalOrder.id;
    setDispatchingId(orderId);

    try {
      await orderService.dispatchOrder(orderId, { carrier, tracking_code: trackingCode });
      showSuccess(`Order #${orderId.slice(0, 8)} dispatched successfully via ${carrier}! Stock committed.`);
      
      setOrders(prev => prev.map(o => o.id === orderId ? {
        ...o,
        status: 'SHIPPED',
        shipping_detail: { ...(o.shipping_detail || {}), carrier, tracking_code: trackingCode, shipped_at: new Date().toISOString() }
      } : o));

      if (selectedOrder && selectedOrder.id === orderId) {
        setSelectedOrder(prev => prev ? {
          ...prev,
          status: 'SHIPPED',
          shipping_detail: { ...(prev.shipping_detail || {}), carrier, tracking_code: trackingCode, shipped_at: new Date().toISOString() }
        } : null);
      }
      setDispatchModalOrder(null);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDispatchingId(null);
    }
  };

  const openOrderDetails = async (order) => {
    setSelectedOrder(order);
    try {
      const res = await orderService.getShipments(order.id);
      const list = Array.isArray(res.data) ? res.data : (res.data ? [res.data] : []);
      setOrderShipments(list);
    } catch (err) {
      setOrderShipments(order.shipping_detail ? [order.shipping_detail] : []);
    }
  };

  const handleUpdateShipmentStatus = async (shipmentId, payload) => {
    setUpdatingShipment(true);
    try {
      await orderService.updateShipmentStatus(
        shipmentId,
        payload.status,
        payload.notes,
        payload.carrier,
        payload.tracking_code,
        payload.estimated_delivery_date
      );
      showSuccess(`Shipment status updated to ${payload.status}`);
      setEditingShipment(null);
      fetchOrders();
      if (selectedOrder) {
        openOrderDetails(selectedOrder);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setUpdatingShipment(false);
    }
  };

  const safeOrders = Array.isArray(orders) ? orders : [];
  const filteredOrders = safeOrders.filter(o => {
    if (statusFilter === 'ALL') return true;
    return (o.status || '').toUpperCase() === statusFilter;
  });

  if (loading && activeTab === 'orders') {
    return (
      <div className="w-full p-6 md:p-8 space-y-6">
        <h1 className="text-3xl font-extrabold text-white">Orders Management</h1>
        <LoadingSkeleton count={3} type="table" />
      </div>
    );
  }

  return (
    <div className="w-full pb-12">
      <ControlPanel
        title="Orders & Fulfillments"
        subtitle={`${orders.length} Total Orders`}
        secondaryActions={[
          {
            label: activeTab === 'orders' ? 'View Outbox Events' : 'View Orders List',
            icon: Activity,
            onClick: () => setActiveTab(activeTab === 'orders' ? 'outbox' : 'orders')
          }
        ]}
        filterOptions={[
          { label: 'All Statuses', value: 'ALL' },
          { label: 'Pending Payment', value: 'PENDING' },
          { label: 'Paid Orders', value: 'PAID' },
          { label: 'Shipped Orders', value: 'SHIPPED' },
          { label: 'Cancelled Orders', value: 'CANCELLED' },
        ]}
        activeFilter={statusFilter}
        onFilterChange={(st) => {
          setStatusFilter(st);
          resetPage();
        }}
        pagination={{
          currentPage: page,
          totalPages: pagination.totalPages,
          totalItems: pagination.totalItems,
          pageSize: pageSize,
          onPageChange: handlePageChange
        }}
        onRefresh={fetchOrders}
      />

      <div className="p-4 md:p-8 space-y-6">
        {/* Status Pipeline Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar pb-2">
          {['ALL', 'PENDING', 'PAID', 'SHIPPED', 'CANCELLED'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                resetPage();
              }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-all ${
                statusFilter === st
                  ? 'bg-purple-600 text-white shadow'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {st === 'ALL' ? 'All Statuses' : st}
            </button>
          ))}
        </div>

        {activeTab === 'orders' ? (
          <div className="space-y-6">
            {safeOrders.length === 0 ? (
              <EmptyState
                icon={ShoppingBag}
                title={`No ${statusFilter === 'ALL' ? '' : statusFilter.toLowerCase()} orders found`}
                description="Orders placed by customers will appear here for store merchants to process and fulfill."
              />
            ) : (
              <>
                <DataTable
                headers={['Order ID', 'Items', 'Total Amount', 'Status', 'Shipping Info', 'Created Date', { label: 'Actions', className: 'text-right' }]}
              >
                  {filteredOrders.map((o) => (
                    <tr key={o.id} className="hover:bg-slate-800/40">
                        <td className="p-4 font-bold text-white font-mono">#{o.id.slice(0, 8)}...</td>
                        <td className="p-4 text-xs text-slate-300">
                          {o.items?.length ? `${o.items.length} item(s)` : `${o.quantity || 1} item(s)`}
                        </td>
                        <td className="p-4 font-extrabold text-indigo-300">${Number(o.total_amount || o.subtotal || 0).toFixed(2)}</td>
                        <td className="p-4"><Badge status={o.status} /></td>
                        <td className="p-4 text-xs text-slate-400">
                          {o.shipping_detail?.tracking_code ? (
                            <div className="font-mono text-emerald-400 flex items-center gap-1">
                              <Truck className="w-3 h-3" /> {o.shipping_detail.carrier}: {o.shipping_detail.tracking_code}
                            </div>
                          ) : (
                            <span>{o.shipping_address?.city ? `${o.shipping_address.city}, ${o.shipping_address.country || ''}` : 'Standard Shipping'}</span>
                          )}
                        </td>
                        <td className="p-4 text-xs text-slate-400">{new Date(o.created_at || Date.now()).toLocaleDateString()}</td>
                        <td className="p-4 text-right space-x-2">
                          <button onClick={() => openOrderDetails(o)} className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white hover:bg-white/10" title="View details">
                            <Eye className="w-4 h-4" />
                          </button>
                          {['PAID', 'PROCESSING'].includes((o.status || '').toUpperCase()) && (
                            <button
                              onClick={() => openDispatchModal(o)}
                              className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all inline-flex items-center gap-1.5 shadow-md shadow-emerald-900/30"
                              title="Start Shipment & Dispatch Order"
                            >
                              <Truck className="w-3.5 h-3.5" />
                              Start Shipment
                            </button>
                          )}
                        </td>

                      </tr>
                    ))}
              </DataTable>

              <Pagination
                currentPage={page}
                totalPages={pagination.totalPages}
                totalItems={pagination.totalItems}
                pageSize={pageSize}
                onPageChange={handlePageChange}
                onPageSizeChange={handlePageSizeChange}
              />
            </>
          )}
        </div>
      ) : (
        <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" /> Outbox Event Stream Log
            </h3>
            <button onClick={fetchOutbox} className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {outboxEvents.length === 0 ? (
            <p className="text-slate-500 text-xs text-center py-6">No outbox events logged.</p>
          ) : (
            <div className="space-y-2">
              {outboxEvents.map((evt) => (
                <div key={evt.id} className="p-3 rounded-xl bg-white/5 border border-white/10 font-mono text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <span className="font-bold text-indigo-300">{evt.event_type || 'ORDER_EVENT'}</span>
                    <span className="text-slate-400 ml-2">Aggregate ID: #{evt.aggregate_id || evt.order_id || evt.id}</span>
                  </div>
                  <div className="flex items-center gap-3 text-slate-500 text-[11px]">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${evt.status === 'PROCESSED' || evt.processed ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}`}>
                      {evt.status || (evt.processed ? 'PROCESSED' : 'PENDING')}
                    </span>
                    <span>{new Date(evt.created_at || Date.now()).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      </div>

      {/* Start Shipment / Dispatch Modal */}
      {dispatchModalOrder && (
        <Modal
          isOpen={!!dispatchModalOrder}
          onClose={() => setDispatchModalOrder(null)}
          title={`Dispatch Shipment - Order #${dispatchModalOrder.id.slice(0, 8)}`}
          maxWidth="max-w-md"
        >
          <form onSubmit={handleDispatchOrder} className="space-y-4">
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
              <PackageCheck className="w-5 h-5 flex-shrink-0" />
              <span>Marking this order as dispatched will commit reserved inventory stock and issue shipment tracking notification.</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Tracking Carrier</label>
              <select
                value={carrier}
                onChange={(e) => setCarrier(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white text-sm focus:outline-none focus:border-emerald-500 font-medium"
              >
                {availableCarriers.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Tracking Number / Code</label>
              <input
                type="text"
                value={trackingCode}
                onChange={(e) => setTrackingCode(e.target.value)}
                placeholder="e.g. TRK-9A8B7C6D"
                required
                className="w-full px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white text-sm font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            {dispatchModalOrder.shipping_address && (
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 text-xs space-y-1">
                <span className="text-slate-400 font-bold block">Delivery Address:</span>
                <p className="text-white font-medium">{dispatchModalOrder.shipping_address.full_name}</p>
                <p className="text-slate-300">{dispatchModalOrder.shipping_address.address_line_1}, {dispatchModalOrder.shipping_address.city}, {dispatchModalOrder.shipping_address.country}</p>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              <button
                type="button"
                onClick={() => setDispatchModalOrder(null)}
                className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 hover:bg-white/10 text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={dispatchingId === dispatchModalOrder.id}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 transition-colors shadow-lg shadow-emerald-900/40"
              >
                <Truck className="w-4 h-4" />
                {dispatchingId === dispatchModalOrder.id ? 'Dispatching...' : 'Confirm Shipment & Dispatch'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Order Details Modal */}
      {selectedOrder && (
        <Modal
          isOpen={!!selectedOrder}
          onClose={() => setSelectedOrder(null)}
          title={`Order #${selectedOrder.id} Details`}
          maxWidth="max-w-3xl"
        >
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
              <div>
                <span className="text-xs text-slate-400 block">Status</span>
                <Badge status={selectedOrder.status} />
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-400 block">Total Amount</span>
                <span className="text-2xl font-black text-indigo-300">
                  ${Number(selectedOrder.total_amount || selectedOrder.subtotal || 0).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Shipments List */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Truck className="w-4 h-4 text-cyan-400" /> Order Shipments ({orderShipments.length})
                </h4>
              </div>

              {orderShipments.length === 0 ? (
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-400 text-center">
                  No active shipments recorded for this order yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {orderShipments.map((s) => (
                    <ShipmentCard
                      key={s.id}
                      shipment={s}
                      onUpdateStatus={(shipment) => setEditingShipment(shipment)}
                    />
                  ))}
                </div>
              )}
            </div>

            <div>
              <h4 className="text-sm font-bold text-slate-200 mb-3">Order Items</h4>
              <div className="rounded-xl border border-white/10 overflow-hidden">
                <table className="w-full text-left text-sm">
                  <thead className="bg-white/5 text-slate-400 text-xs uppercase border-b border-white/10">
                    <tr>
                      <th className="p-3">Product Name</th>
                      <th className="p-3">Qty</th>
                      <th className="p-3">Unit Price</th>
                      <th className="p-3 text-right">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-slate-200 text-xs">
                    {(selectedOrder.items || []).map((item, idx) => (
                      <tr key={idx}>
                        <td className="p-3 font-medium text-white">{item.product_name || `Product #${item.product_id}`}</td>
                        <td className="p-3">{item.quantity}</td>
                        <td className="p-3">${Number(item.unit_price || item.price || 0).toFixed(2)}</td>
                        <td className="p-3 text-right font-bold text-white">
                          ${(Number(item.quantity || 1) * Number(item.unit_price || item.price || 0)).toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
              {['PAID', 'PROCESSING'].includes((selectedOrder.status || '').toUpperCase()) && (
                <button
                  onClick={() => {
                    const ord = selectedOrder;
                    setSelectedOrder(null);
                    openDispatchModal(ord);
                  }}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors"
                >
                  <Truck className="w-4 h-4" />
                  Start Shipment & Dispatch Order
                </button>
              )}

              <button onClick={() => setSelectedOrder(null)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 hover:bg-white/10 text-xs">
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Shipment Status Edit Modal */}
      {editingShipment && (
        <ShipmentStatusModal
          isOpen={!!editingShipment}
          onClose={() => setEditingShipment(null)}
          shipment={editingShipment}
          onSubmit={handleUpdateShipmentStatus}
          loading={updatingShipment}
        />
      )}
    </div>
  );
}

