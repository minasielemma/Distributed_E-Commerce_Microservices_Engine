import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { cartService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, FormSheet, EmptyState, LoadingSkeleton, Badge } from '../components/common/UIComponents';
import { PackageSearch, MessageSquare } from 'lucide-react';

export default function ItemRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState({ total: 0, pending: 0, approved: 0, rejected: 0, fulfilled: 0 });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [statusInput, setStatusInput] = useState('');
  const [adminResponseInput, setAdminResponseInput] = useState('');
  const [updating, setUpdating] = useState(false);
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, resetPage } = pagination;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize, scope: 'shop' };
      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }
      if (searchQuery.trim()) {
        params.search = searchQuery.trim();
      }

      const [reqRes, statsRes] = await Promise.allSettled([
        cartService.getItemRequests(params),
        cartService.getItemRequestStats(params),
      ]);

      if (reqRes.status === 'fulfilled') {
        const resData = reqRes.value?.data;
        const list = Array.isArray(resData) ? resData : (resData?.results || []);
        setRequests(list);
        updatePaginationState(resData);
      }
      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data || { total: 0, pending: 0, approved: 0, rejected: 0, fulfilled: 0 });
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, statusFilter, searchQuery, updatePaginationState, showError]);

  useEffect(() => {
    fetchData();

    const handleNotif = (e) => {
      if (e.detail?.notification_type === 'ITEM_REQUEST') {
        fetchData();
      }
    };
    window.addEventListener('notification_received', handleNotif);
    return () => window.removeEventListener('notification_received', handleNotif);
  }, [fetchData]);

  const filteredRequests = useMemo(() => {
    return requests.filter((req) => {
      const matchStatus = statusFilter === 'ALL' || (req.status || '').toUpperCase() === statusFilter.toUpperCase();
      const query = searchQuery.trim().toLowerCase();
      const matchSearch = !query || 
        (req.product_name || '').toLowerCase().includes(query) ||
        (req.description || '').toLowerCase().includes(query) ||
        (req.admin_response || '').toLowerCase().includes(query) ||
        (String(req.user_id || '')).toLowerCase().includes(query);
      return matchStatus && matchSearch;
    });
  }, [requests, statusFilter, searchQuery]);

  const openUpdateModal = (req) => {
    setSelectedRequest(req);
    setStatusInput(req.status);
    setAdminResponseInput(req.admin_response || '');
    setModalOpen(true);
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    if (!selectedRequest) return;

    setUpdating(true);
    try {
      await cartService.updateItemRequestStatus(selectedRequest.id, statusInput, adminResponseInput);
      showSuccess(`Item request status updated to ${statusInput}`);
      setModalOpen(false);
      fetchData();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setUpdating(false);
    }
  };

  const columns = [
    {
      header: 'Product Requested',
      accessor: 'product_name',
      render: (row) => (
        <div className="max-w-xs">
          <div className="font-bold text-white flex items-center gap-1.5">
            <PackageSearch className="w-4 h-4 text-[#7c7bad] shrink-0" />
            <span>{row.product_name}</span>
          </div>
          {row.description && (
            <div className="text-xs text-[#94a3b8] font-normal truncate mt-0.5" title={row.description}>
              {row.description}
            </div>
          )}
        </div>
      )
    },
    {
      header: 'Qty',
      accessor: 'quantity',
      render: (row) => <span className="font-mono font-bold text-slate-200">x{row.quantity}</span>
    },
    {
      header: 'Customer ID',
      accessor: 'user_id',
      render: (row) => <span className="text-xs font-mono text-[#94a3b8]">{row.user_id ? `${String(row.user_id).substring(0, 8)}...` : 'Anonymous'}</span>
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <Badge status={row.status} />
    },
    {
      header: 'Shop Response',
      accessor: 'admin_response',
      render: (row) => <span className="text-xs text-[#e2e8f0] max-w-xs truncate block">{row.admin_response || <span className="text-slate-500 italic">No response added</span>}</span>
    },
    {
      header: 'Requested At',
      accessor: 'created_at',
      render: (row) => <span className="text-xs text-[#94a3b8] font-mono">{row.created_at ? new Date(row.created_at).toLocaleDateString() : 'N/A'}</span>
    },
    {
      header: 'Actions',
      accessor: 'actions',
      align: 'right',
      render: (row) => (
        <button
          onClick={() => openUpdateModal(row)}
          className="app-btn-teal text-xs py-1 px-2.5 inline-flex items-center gap-1"
        >
          <MessageSquare className="w-3 h-3" /> Manage
        </button>
      )
    }
  ];

  const safeStats = { total: 0, pending: 0, approved: 0, rejected: 0, fulfilled: 0, ...(stats || {}) };

  return (
    <div className="w-full space-y-6 pb-8">
      <ControlPanel
        title="Customer Item Requests"
        subtitle="Manage product request submissions from customers asking for out-of-stock or custom items"
        breadcrumbs={['Inventory', 'Item Requests']}
        searchValue={searchQuery}
        onSearchChange={(e) => {
          const val = typeof e === 'string' ? e : (e?.target?.value ?? '');
          setSearchQuery(val);
          resetPage();
        }}
        searchPlaceholder="Search product or details..."
        customFilters={
          <div className="flex items-center gap-1">
            {['ALL', 'PENDING', 'APPROVED', 'FULFILLED', 'REJECTED'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st);
                  resetPage();
                }}
                className={`px-2.5 py-1 rounded text-xs font-bold transition-all ${
                  statusFilter === st
                    ? 'bg-[#7c7bad] text-white'
                    : 'bg-[#1f293d] text-[#94a3b8] hover:bg-[#334155]'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        }
        pagination={pagination}
      />

      <div className="px-4 md:px-6 lg:px-8 space-y-6">
        {/* Stats Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="app-card p-3 border-l-4 border-l-slate-400">
            <span className="text-[10px] text-[#94a3b8] font-bold uppercase">Total Requests</span>
            <span className="text-xl font-black text-white block mt-1">{safeStats.total ?? 0}</span>
          </div>
          <div className="app-card p-3 border-l-4 border-l-amber-400">
            <span className="text-[10px] text-amber-400 font-bold uppercase">Pending</span>
            <span className="text-xl font-black text-amber-300 block mt-1">{safeStats.pending ?? 0}</span>
          </div>
          <div className="app-card p-3 border-l-4 border-l-[#7c7bad]">
            <span className="text-[10px] text-[#7c7bad] font-bold uppercase">Approved</span>
            <span className="text-xl font-black text-[#7c7bad] block mt-1">{safeStats.approved ?? 0}</span>
          </div>
          <div className="app-card p-3 border-l-4 border-l-[#48bb78]">
            <span className="text-[10px] text-[#48bb78] font-bold uppercase">Fulfilled</span>
            <span className="text-xl font-black text-[#48bb78] block mt-1">{safeStats.fulfilled ?? 0}</span>
          </div>
          <div className="app-card p-3 border-l-4 border-l-rose-400">
            <span className="text-[10px] text-rose-400 font-bold uppercase">Rejected</span>
            <span className="text-xl font-black text-rose-300 block mt-1">{safeStats.rejected ?? 0}</span>
          </div>
        </div>

        {/* Table List */}
        {loading ? (
          <LoadingSkeleton count={4} type="table" />
        ) : filteredRequests.length === 0 ? (
          <EmptyState
            icon={PackageSearch}
            title="No item requests found"
            description={searchQuery || statusFilter !== 'ALL' ? 'Try clearing filters or search terms.' : 'Customers have not submitted any product requests yet.'}
          />
        ) : (
          <DataTable
            columns={columns}
            data={filteredRequests}
            keyField="id"
            pagination={pagination}
          />
        )}
      </div>

      {/* Update Status Form Sheet */}
      {selectedRequest && (
        <FormSheet
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Manage Item Request"
          subtitle={`Request #${selectedRequest.id}`}
          onSave={handleUpdateStatus}
          saveLabel={updating ? 'Saving...' : 'Save & Notify Customer'}
        >
          <form onSubmit={handleUpdateStatus} className="space-y-4 text-xs">
            <div className="bg-[#0f172a] p-3 rounded border border-[#2d3748] space-y-1.5">
              <div className="text-[10px] font-bold text-[#94a3b8] uppercase">Request Summary</div>
              <div className="text-sm font-extrabold text-white">{selectedRequest.product_name}</div>
              <div className="text-xs text-slate-300">Requested Quantity: <span className="font-mono text-[#00a09d] font-bold">x{selectedRequest.quantity}</span></div>
              {selectedRequest.description && (
                <div className="text-xs text-[#94a3b8] bg-[#0b0f19] p-2 rounded border border-[#2d3748] mt-1 italic">
                  "{selectedRequest.description}"
                </div>
              )}
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">Update Status</label>
              <select
                value={statusInput}
                onChange={(e) => setStatusInput(e.target.value)}
                className="app-input font-bold"
              >
                <option value="PENDING">PENDING — Under Review</option>
                <option value="APPROVED">APPROVED — Processing Stock</option>
                <option value="FULFILLED">FULFILLED — Product Available in Store</option>
                <option value="REJECTED">REJECTED — Cannot Fulfill</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                Shop Response / Customer Note
              </label>
              <textarea
                value={adminResponseInput}
                onChange={(e) => setAdminResponseInput(e.target.value)}
                rows={3}
                placeholder="e.g. 'We have requested this item from our supplier. Expected arrival in 3 business days.'"
                className="app-input"
              />
            </div>
          </form>
        </FormSheet>
      )}
    </div>
  );
}

