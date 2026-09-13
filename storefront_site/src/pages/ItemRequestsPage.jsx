import React, { useState, useEffect, useRef } from 'react';
import { cartService, authService } from '../services/apiServices';
import api, { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Badge } from '../components/common/UIComponents';
import { Link } from 'react-router-dom';
import { RefreshCw, Radio } from 'lucide-react';

const RequestProgressTracker = ({ status, createdAt, updatedAt, adminResponse }) => {
  const s = (status || 'PENDING').toUpperCase();
  const isRejected = s === 'REJECTED';
  const isFulfilled = s === 'FULFILLED';
  const isApproved = s === 'APPROVED' || isFulfilled;
  const isPending = s === 'PENDING';

  let percent = 25;
  if (isPending) percent = 35;
  if (s === 'APPROVED') percent = 70;
  if (isFulfilled) percent = 100;
  if (isRejected) percent = 100;

  const steps = [
    {
      id: 'submitted',
      title: 'Submitted',
      subtitle: createdAt ? new Date(createdAt).toLocaleDateString([], { month: 'short', day: 'numeric' }) : 'Received',
      completed: true,
      active: false,
    },
    {
      id: 'review',
      title: 'Merchant Review',
      subtitle: isRejected ? 'Declined' : isApproved ? 'Approved' : 'Reviewing',
      completed: isApproved || isRejected,
      active: isPending,
      error: isRejected,
    },
    {
      id: 'sourcing',
      title: 'Stock Sourcing',
      subtitle: isFulfilled ? 'Procured' : isApproved ? 'In Progress' : isRejected ? 'Cancelled' : 'Queued',
      completed: isFulfilled,
      active: s === 'APPROVED',
      error: isRejected,
    },
    {
      id: 'fulfilled',
      title: 'Available on Store',
      subtitle: isFulfilled ? 'Ready to Order' : 'Awaiting Stock',
      completed: isFulfilled,
      active: false,
    },
  ];

  return (
    <div className="mt-4 pt-4 border-t border-[#D5D9D9] space-y-3">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-semibold">
        <span className="text-[#565959]">Request Progress Tracker</span>
        <span
          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
            isRejected
              ? 'bg-rose-100 text-rose-700 border border-rose-300'
              : isFulfilled
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : s === 'APPROVED'
              ? 'bg-blue-100 text-blue-800 border border-blue-300'
              : 'bg-amber-100 text-amber-800 border border-amber-300'
          }`}
        >
          {isPending && 'Step 1 of 3: Merchant Review'}
          {s === 'APPROVED' && 'Step 2 of 3: Approved & Procuring Stock'}
          {isFulfilled && 'Step 3 of 3: Fulfilled & Available'}
          {isRejected && 'Closed: Merchant Declined Request'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full bg-[#E7E7E7] h-2.5 rounded-full overflow-hidden shadow-inner">
        <div
          className={`h-full transition-all duration-500 rounded-full ${
            isRejected
              ? 'bg-rose-500'
              : isFulfilled
              ? 'bg-emerald-500'
              : 'bg-gradient-to-r from-amber-400 to-[#e77600]'
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Timeline Steps */}
      <div className="grid grid-cols-4 gap-1 pt-1">
        {steps.map((step, idx) => (
          <div key={step.id} className="flex flex-col items-center text-center">
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold mb-1 transition-all ${
                step.error
                  ? 'bg-rose-600 text-white shadow-sm'
                  : step.completed
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : step.active
                  ? 'bg-[#e77600] text-white ring-4 ring-amber-100 animate-pulse'
                  : 'bg-[#F0F2F2] text-[#565959] border border-[#D5D9D9]'
              }`}
            >
              {step.error ? '✕' : step.completed ? '✓' : idx + 1}
            </div>
            <span
              className={`text-[11px] font-bold leading-tight ${
                step.error
                  ? 'text-rose-700'
                  : step.completed
                  ? 'text-[#111]'
                  : step.active
                  ? 'text-[#007185]'
                  : 'text-[#767676]'
              }`}
            >
              {step.title}
            </span>
            <span className="text-[10px] text-[#565959] mt-0.5 hidden sm:block">
              {step.subtitle}
            </span>
          </div>
        ))}
      </div>

      {/* Merchant Response Note */}
      {adminResponse && (
        <div className="mt-3 text-xs bg-[#F0F2F2] border-l-4 border-l-[#007185] border border-[#D5D9D9] rounded p-3 text-[#111] space-y-1">
          <span className="font-bold text-[#007185] flex items-center gap-1.5">
            <span>Response from Merchant:</span>
          </span>
          <p className="text-slate-800 leading-relaxed italic">"{adminResponse}"</p>
        </div>
      )}
    </div>
  );
};

export const ItemRequestsPage = () => {
  const [requests, setRequests] = useState([]);
  const [shops, setShops] = useState([]);
  const [loadingShops, setLoadingShops] = useState(true);
  const [selectedShopId, setSelectedShopId] = useState('');
  const [productName, setProductName] = useState('');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const currentPageRef = useRef(currentPage);
  const prevRequestsRef = useRef({});
  const pageSize = 5;
  const { showSuccess, showError } = useToast();

  useEffect(() => {
    currentPageRef.current = currentPage;
  }, [currentPage]);

  useEffect(() => {
    fetchShops();
    fetchRequests(1);

    // Real-time notification listener
    const handleNotif = (e) => {
      if (e.detail?.notification_type === 'ITEM_REQUEST') {
        const notifTitle = e.detail?.title || 'Item Request Updated';
        const notifMsg = e.detail?.message || '';
        showSuccess(`🔔 ${notifTitle}: ${notifMsg}`);
        fetchRequests(currentPageRef.current);
      }
    };

    window.addEventListener('notification_received', handleNotif);

    // Auto-polling interval (every 8 seconds)
    const intervalId = setInterval(() => {
      fetchRequests(currentPageRef.current, true);
    }, 8000);

    return () => {
      window.removeEventListener('notification_received', handleNotif);
      clearInterval(intervalId);
    };
  }, []);

  const fetchShops = async () => {
    setLoadingShops(true);
    try {
      const res = await authService.getTenants({ scope: 'active' })
        .catch(() => api.get('/auth/tenants/?scope=active'))
        .catch(() => api.get('/auth/tenant/list/?scope=active'))
        .catch(() => null);

      const rawData = res?.data;
      let list = [];
      if (Array.isArray(rawData)) {
        list = rawData;
      } else if (Array.isArray(rawData?.results)) {
        list = rawData.results;
      } else if (Array.isArray(rawData?.tenants)) {
        list = rawData.tenants;
      } else if (Array.isArray(rawData?.data)) {
        list = rawData.data;
      }

      setShops(list);
      if (list.length > 0 && !selectedShopId) {
        setSelectedShopId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load shops:', err);
    } finally {
      setLoadingShops(false);
    }
  };

  const fetchRequests = async (page = 1, silent = false) => {
    if (!silent) setIsRefreshing(true);
    try {
      const res = await cartService.getItemRequests({ page, page_size: pageSize });
      const data = res.data?.results || res.data || [];
      const count = res.data?.count ?? (Array.isArray(data) ? data.length : 0);
      const newList = Array.isArray(data) ? data : [];

      // Check if any request status changed for user alert
      newList.forEach((req) => {
        const prev = prevRequestsRef.current[req.id];
        if (prev && prev.status !== req.status) {
          showSuccess(`🎉 Item request "${req.product_name}" status updated to ${req.status}!`);
        }
        prevRequestsRef.current[req.id] = req;
      });

      setRequests(newList);
      setTotalCount(count);
    } catch (err) {
      if (!silent) console.error(err);
    } finally {
      if (!silent) setIsRefreshing(false);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    fetchRequests(newPage);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!productName.trim()) {
      showError('Please enter a product title.');
      return;
    }
    setSubmitting(true);
    try {
      await cartService.createItemRequest({
        product_name: productName.trim(),
        description: description.trim(),
        quantity,
        tenant_id: selectedShopId || (shops[0]?.id || null),
      });
      setProductName('');
      setDescription('');
      setQuantity(1);
      showSuccess('Special item request submitted successfully!');
      fetchRequests(1);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await cartService.deleteItemRequest(id);
      showSuccess('Item request removed');
      fetchRequests(currentPage);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const getShopName = (tenantId) => {
    if (!tenantId) return 'General Store Request';
    const found = shops.find((s) => String(s.id).toLowerCase() === String(tenantId).toLowerCase());
    return found ? found.name : `Shop #${String(tenantId).substring(0, 8)}`;
  };

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto space-y-8">
        <div>
          <Link to="/profile" className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline mb-2 block">
            Your Account
          </Link>
          <h1 className="text-3xl font-normal">Special Product Requests</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="border border-[#D5D9D9] p-6 rounded bg-[#F9F9F9]">
            <h3 className="text-lg font-bold mb-4">Request a Product</h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-bold mb-1">Target Shop</label>
                <select
                  value={selectedShopId}
                  onChange={(e) => setSelectedShopId(e.target.value)}
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                >
                  <option value="">General Request (All Merchants / Apex Platform)</option>
                  {loadingShops ? (
                    <option value="" disabled>Loading Shops...</option>
                  ) : (
                    shops.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.domain || 'Active Store'})
                      </option>
                    ))
                  )}
                </select>
                {shops.length === 0 && !loadingShops && (
                  <p className="text-xs text-[#565959] mt-1">No specific merchant shops registered yet — your request will be submitted to the general store platform.</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">Product Title</label>
                <input
                  type="text"
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  placeholder="e.g. Ergonomic Standing Desk Cable Kit"
                  value={productName}
                  onChange={(e) => setProductName(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">Quantity</label>
                <input
                  type="number"
                  min="1"
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  value={quantity}
                  onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-bold mb-1">Description</label>
                <textarea
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow min-h-[100px]"
                  placeholder="Specify colors, dimensions, or technical details..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="pt-2">
                <button 
                  type="submit" 
                  disabled={submitting || !productName.trim()} 
                  className="btn-buy-now w-full py-2 rounded shadow-sm text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Submitting...' : 'Submit Request'}
                </button>
              </div>
            </form>
          </div>

          {/* List */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">My Requests</h3>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full inline-flex items-center gap-1.5">
                  <Radio className="w-3 h-3 text-emerald-600 animate-pulse" />
                  <span>Live Sync</span>
                </span>
                <button
                  type="button"
                  onClick={() => fetchRequests(currentPage)}
                  disabled={isRefreshing}
                  className="text-xs text-[#007185] hover:text-[#C7511F] hover:underline flex items-center gap-1 p-1"
                  title="Refresh Request Status"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>
            </div>

            <div className="space-y-4">
              {requests.length === 0 ? (
                <div className="py-4 text-[#565959]">
                  No requests submitted yet.
                </div>
              ) : (
                requests.map((req) => (
                  <div key={req.id} className="border border-[#D5D9D9] rounded-lg p-5 relative bg-white shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start pr-12 mb-1">
                      <span className="font-bold text-base text-[#111]">{req.product_name}</span>
                      <Badge status={req.status || 'PENDING'} />
                    </div>
                    <div className="text-xs font-semibold text-[#007185] mb-2 flex items-center gap-1">
                      <span>Target Merchant:</span>
                      <span className="font-bold">{getShopName(req.tenant_id)}</span>
                    </div>
                    <div className="text-xs text-[#565959] font-medium">Quantity Requested: <span className="font-bold text-[#111]">{req.quantity}</span></div>
                    {req.description && (
                      <div className="text-xs text-[#333] mt-2 border-l-2 border-[#D5D9D9] pl-3 py-1 bg-[#FAF9F6] rounded-r italic">
                        "{req.description}"
                      </div>
                    )}

                    {/* Progress Tracker */}
                    <RequestProgressTracker
                      status={req.status}
                      createdAt={req.created_at}
                      updatedAt={req.updated_at}
                      adminResponse={req.admin_response}
                    />

                    <button
                      onClick={() => handleDelete(req.id)}
                      className="absolute top-4 right-4 text-xs font-semibold text-amazon-link-teal hover:text-amazon-orange hover:underline p-1"
                      title="Delete Request"
                    >
                      Delete
                    </button>
                  </div>
                ))
              )}

              {totalPages > 1 && (
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#D5D9D9] text-sm text-[#565959]">
                  <div>
                    Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} requests
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      disabled={currentPage === 1}
                      onClick={() => handlePageChange(currentPage - 1)}
                      className="btn-secondary py-1 px-3 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    {Array.from({ length: totalPages }).map((_, i) => {
                      const pageNum = i + 1;
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`w-8 h-8 rounded text-sm ${
                            currentPage === pageNum
                              ? 'bg-[#F0F2F2] border border-[#D5D9D9] font-bold text-[#111]'
                              : 'text-amazon-link-teal hover:underline'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    <button
                      disabled={currentPage === totalPages}
                      onClick={() => handlePageChange(currentPage + 1)}
                      className="btn-secondary py-1 px-3 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
