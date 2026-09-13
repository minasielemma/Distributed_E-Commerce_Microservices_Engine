import React, { useState, useEffect, useCallback } from 'react';
import { catalogService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, FormSheet, ConfirmDialog, EmptyState, LoadingSkeleton } from '../components/common/UIComponents';
import { Tag, Plus, Edit2, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function CouponsPage() {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingCoupon, setEditingCoupon] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange, resetPage } = pagination;

  // Test coupon state
  const [testCode, setTestCode] = useState('');
  const [testSubtotal, setTestSubtotal] = useState(100);
  const [testResult, setTestResult] = useState(null);

  const [formData, setFormData] = useState({
    code: '',
    discount_type: 'PERCENTAGE',
    value: 10,
    min_purchase_amount: 0,
    usage_limit: 100,
    is_active: true,
  });

  const fetchCoupons = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (searchTerm.trim()) params.search = searchTerm.trim();

      const res = await catalogService.getCoupons(params);
      const resData = res?.data;
      const list = Array.isArray(resData) ? resData : (resData?.results || []);
      setCoupons(list);
      updatePaginationState(resData);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchTerm, updatePaginationState, showError]);

  useEffect(() => {
    fetchCoupons();
  }, [fetchCoupons]);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
    resetPage();
  };

  const handleOpenModal = (c = null) => {
    if (c) {
      setEditingCoupon(c);
      setFormData({
        code: c.code || '',
        discount_type: c.discount_type || 'PERCENTAGE',
        value: c.value ?? c.discount_value ?? 10,
        min_purchase_amount: c.min_purchase_amount ?? c.min_order_amount ?? 0,
        usage_limit: c.usage_limit ?? c.max_uses ?? '',
        is_active: c.is_active ?? true,
      });
    } else {
      setEditingCoupon(null);
      setFormData({
        code: '',
        discount_type: 'PERCENTAGE',
        value: 10,
        min_purchase_amount: 0,
        usage_limit: 100,
        is_active: true,
      });
    }
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valNum = parseFloat(formData.value) || 0;
    const minOrderNum = parseFloat(formData.min_purchase_amount) || 0;
    const limitNum = formData.usage_limit !== '' && formData.usage_limit !== null ? parseInt(formData.usage_limit) : null;

    const payload = {
      code: formData.code.trim().toUpperCase(),
      discount_type: formData.discount_type,
      value: valNum,
      discount_value: valNum,
      min_purchase_amount: minOrderNum,
      min_order_amount: minOrderNum,
      usage_limit: limitNum,
      max_uses: limitNum,
      is_active: formData.is_active,
    };

    try {
      if (editingCoupon) {
        await catalogService.updateCoupon(editingCoupon.id, payload);
        showSuccess('Coupon updated successfully');
      } else {
        await catalogService.createCoupon(payload);
        showSuccess('Coupon created successfully');
      }
      setModalOpen(false);
      fetchCoupons();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await catalogService.deleteCoupon(deleteId);
      showSuccess('Coupon deleted successfully');
      fetchCoupons();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteId(null);
    }
  };

  const handleTestCoupon = async (e) => {
    e.preventDefault();
    try {
      const res = await catalogService.validateCoupon(testCode, Number(testSubtotal));
      setTestResult(res.data);
    } catch (err) {
      setTestResult({ valid: false, message: getErrorMessage(err) });
    }
  };

  const columns = [
    {
      header: 'Code',
      accessor: 'code',
      render: (row) => (
        <span className="bg-purple-500/10 border border-purple-500/30 text-purple-300 px-2 py-0.5 rounded font-mono font-bold uppercase tracking-wider text-xs">
          {row.code}
        </span>
      )
    },
    {
      header: 'Type & Value',
      accessor: 'value',
      render: (row) => {
        const val = row.value ?? row.discount_value ?? 0;
        if (row.discount_type === 'PERCENTAGE') return <span className="text-[#48bb78] font-bold font-mono">{val}% OFF</span>;
        if (row.discount_type === 'FIXED') return <span className="text-[#48bb78] font-bold font-mono">${Number(val).toFixed(2)} OFF</span>;
        return <span className="text-[#00a09d] font-bold">Free Shipping</span>;
      }
    },
    {
      header: 'Min Order',
      accessor: 'min_purchase_amount',
      render: (row) => <span className="font-mono text-xs text-slate-200">${Number(row.min_purchase_amount ?? row.min_order_amount ?? 0).toFixed(2)}</span>
    },
    {
      header: 'Usage Limit',
      accessor: 'usage_limit',
      render: (row) => {
        const limit = row.usage_limit ?? row.max_uses;
        const used = row.times_used ?? 0;
        return <span className="text-xs text-slate-300 font-mono">{limit ? `${used} / ${limit} uses` : `${used} / Unlimited`}</span>;
      }
    },
    {
      header: 'Status',
      accessor: 'is_active',
      render: (row) => (
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${row.is_active ? 'bg-[#48bb78]/20 text-[#48bb78] border-[#48bb78]/40' : 'bg-rose-500/20 text-rose-300 border-rose-500/40'}`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      )
    },
    {
      header: 'Actions',
      accessor: 'actions',
      align: 'right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <button onClick={() => handleOpenModal(row)} className="p-1.5 rounded bg-slate-800 text-slate-300 hover:text-white" title="Edit Coupon">
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => setDeleteId(row.id)} className="p-1.5 rounded bg-slate-800 text-slate-400 hover:text-rose-400" title="Delete Coupon">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Coupons & Promos Governance"
        subtitle={`${coupons.length} Active Coupons`}
        breadcrumbs={['Sales', 'Promotions', 'Coupons']}
        primaryAction={{
          label: 'Create Coupon',
          icon: Plus,
          onClick: () => handleOpenModal()
        }}
        searchValue={searchTerm}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Search coupons by code..."
        pagination={pagination}
      />

      <div className="px-4 md:px-6 space-y-4">
        {/* Coupon Validator Sandbox */}
        <div className="app-card p-4 border-[#7c7bad]/40 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Tag className="w-4 h-4 text-[#7c7bad]" /> Live Coupon Rule Validation Sandbox
          </h3>
          <form onSubmit={handleTestCoupon} className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              placeholder="COUPON CODE (e.g. SUMMER10)"
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              required
              className="app-input uppercase w-52 text-xs"
            />
            <input
              type="number"
              placeholder="Subtotal $"
              value={testSubtotal}
              onChange={(e) => setTestSubtotal(e.target.value)}
              required
              className="w-32 app-input text-xs"
            />
            <button type="submit" className="app-btn-secondary text-xs">
              Test Validation
            </button>
          </form>

          {testResult && (
            <div className={`p-2.5 rounded text-xs font-semibold flex items-center gap-2 ${testResult.valid ? 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-300' : 'bg-rose-950/80 border border-rose-500/40 text-rose-300'}`}>
              {testResult.valid ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />}
              <span>
                {testResult.valid
                  ? `Valid Coupon! Code: ${testResult.code} | Discount: $${testResult.discount_amount}`
                  : `Invalid: ${testResult.message || 'Coupon criteria not met'}`}
              </span>
            </div>
          )}
        </div>

        {/* Coupons Table */}
        {loading && coupons.length === 0 ? (
          <LoadingSkeleton count={4} type="table" />
        ) : coupons.length === 0 ? (
          <EmptyState
            icon={Tag}
            title="No coupons created"
            description="Create coupon codes to offer percentage or fixed value discounts."
            action={
              <button onClick={() => handleOpenModal()} className="app-btn-primary mt-3">
                <Plus size={14} /> Create First Coupon
              </button>
            }
          />
        ) : (
          <DataTable
            columns={columns}
            data={coupons}
            keyField="id"
            pagination={pagination}
          />
        )}
      </div>

      {/* Form Sheet / Modal */}
      <FormSheet
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingCoupon ? 'Edit Coupon' : 'Create New Coupon'}
        subtitle="Configure promo codes, usage limits, and order subtotal criteria"
        onSave={handleSubmit}
        saveLabel={editingCoupon ? 'Save Changes' : 'Create Coupon'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Coupon Code</label>
            <input
              type="text"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              placeholder="e.g. WELCOME10"
              required
              className="app-input font-mono uppercase"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Discount Type</label>
              <select
                value={formData.discount_type}
                onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })}
                className="app-input"
              >
                <option value="PERCENTAGE">Percentage (%)</option>
                <option value="FIXED">Fixed Amount ($)</option>
                <option value="FREE_SHIPPING">Free Shipping</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Discount Value</label>
              <input
                type="number"
                step="0.01"
                value={formData.value}
                onChange={(e) => setFormData({ ...formData, value: e.target.value })}
                required={formData.discount_type !== 'FREE_SHIPPING'}
                disabled={formData.discount_type === 'FREE_SHIPPING'}
                className="app-input font-mono disabled:opacity-40"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Min Order Amount ($)</label>
              <input
                type="number"
                step="0.01"
                value={formData.min_purchase_amount}
                onChange={(e) => setFormData({ ...formData, min_purchase_amount: e.target.value })}
                className="app-input font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Max Uses Limit</label>
              <input
                type="number"
                value={formData.usage_limit}
                onChange={(e) => setFormData({ ...formData, usage_limit: e.target.value })}
                placeholder="Leave blank for unlimited"
                className="app-input font-mono"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 rounded bg-slate-900 border-white/20 text-[#7c7bad] focus:ring-[#7c7bad]"
            />
            <label htmlFor="is_active" className="text-sm font-semibold text-slate-300">Active and available for buyers</label>
          </div>
        </form>
      </FormSheet>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Coupon"
        message="Are you sure you want to delete this promotional coupon code?"
      />
    </div>
  );
}

