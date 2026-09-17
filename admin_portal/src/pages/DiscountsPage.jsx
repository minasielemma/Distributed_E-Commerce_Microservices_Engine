import React, { useState, useEffect, useCallback } from 'react';
import { catalogService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, FormSheet, ConfirmDialog, EmptyState, LoadingSkeleton, Badge } from '../components/common/UIComponents';
import { Percent, Plus, Edit2, Trash2, CheckCircle2, XCircle, Tag, Sparkles, X, Search } from 'lucide-react';

const getInitialTimes = () => {
  const now = new Date();
  const nextMonth = new Date(Date.now() + 30 * 86400000);
  return {
    start_time: now.toISOString().slice(0, 16),
    end_time: nextMonth.toISOString().slice(0, 16)
  };
};

function ProductSearchPicker({ value, onChange, placeholder = "Search 100k+ products by name..." }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  useEffect(() => {
    if (value) {
      if (!selectedProduct || String(selectedProduct.id) !== String(value)) {
        catalogService.getProduct(value)
          .then((r) => setSelectedProduct(r.data))
          .catch(() => setSelectedProduct(null));
      }
    } else {
      setSelectedProduct(null);
    }
  }, [value]);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    const timer = setTimeout(() => {
      catalogService.getProducts({ search: query.trim(), page_size: 20 })
        .then((r) => {
          const list = Array.isArray(r.data) ? r.data : (r.data?.results || []);
          setResults(list);
        })
        .catch(() => setResults([]))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [query, open]);

  return (
    <div className="relative">
      {selectedProduct ? (
        <div className="flex items-center justify-between p-2.5 bg-slate-800/90 border border-purple-500/50 rounded-lg text-xs">
          <div className="flex items-center gap-2 truncate">
            <Tag className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span className="font-bold text-white truncate">{selectedProduct.name}</span>
            <span className="text-emerald-400 font-mono">(Base: ${selectedProduct.base_price})</span>
          </div>
          <button
            type="button"
            onClick={() => {
              setSelectedProduct(null);
              onChange('');
            }}
            className="text-slate-400 hover:text-rose-400 p-1"
            title="Clear product selection"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div>
          <div className="relative">
            <input
              type="text"
              value={query}
              onFocus={() => setOpen(true)}
              onChange={(e) => {
                setQuery(e.target.value);
                setOpen(true);
              }}
              placeholder={placeholder}
              className="app-input pr-8"
            />
            <Search className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
          </div>
          {open && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-900 border border-slate-700 rounded-lg shadow-2xl z-50 max-h-60 overflow-y-auto divide-y divide-slate-800">
              {loading ? (
                <div className="p-3 text-xs text-slate-400 text-center">Searching catalog products...</div>
              ) : results.length === 0 ? (
                <div className="p-3 text-xs text-slate-400 text-center">No products found matching "{query}"</div>
              ) : (
                results.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      setSelectedProduct(p);
                      onChange(p.id);
                      setOpen(false);
                    }}
                    className="w-full text-left p-2.5 hover:bg-purple-600/20 text-xs flex items-center justify-between transition-colors"
                  >
                    <span className="font-semibold text-slate-200 truncate pr-2">{p.name}</span>
                    <span className="text-emerald-400 font-mono text-[11px] shrink-0">${p.base_price}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function DiscountsPage() {
  const [discounts, setDiscounts] = useState([]);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange, resetPage } = pagination;

  const times = getInitialTimes();
  const [formData, setFormData] = useState({
    title: '',
    discount_type: 'PERCENTAGE',
    discount_value: 10,
    target_type: 'PRODUCT',
    product: '',
    category: '',
    start_time: times.start_time,
    end_time: times.end_time,
    priority: 1,
    is_active: true,
  });

  const { showSuccess, showError } = useToast();

  const fetchDiscounts = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (searchTerm.trim()) params.search = searchTerm.trim();
      const res = await catalogService.getDiscounts(params);
      const resData = res?.data;
      const list = Array.isArray(resData) ? resData : (resData?.results || []);
      setDiscounts(list);
      updatePaginationState(resData);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchTerm, updatePaginationState, showError]);

  useEffect(() => {
    fetchDiscounts();
  }, [fetchDiscounts]);

  useEffect(() => {
    catalogService.getCategories({ fetch_all: true })
      .then((r) => setCategories(Array.isArray(r.data) ? r.data : r.data.results || []))
      .catch(() => {});
  }, []);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
    resetPage();
  };

  const toLocalDatetime = (iso) => (iso ? iso.slice(0, 16) : '');
  const toISOString = (local) => (local ? new Date(local).toISOString() : '');
  const field = (key, val) => setFormData((f) => ({ ...f, [key]: val }));

  const handleOpenModal = (d = null) => {
    const defaultTimes = getInitialTimes();
    if (d) {
      setEditing(d);
      setFormData({
        title: d.title || '',
        discount_type: d.discount_type || 'PERCENTAGE',
        discount_value: d.discount_value ?? 10,
        target_type: d.category ? 'CATEGORY' : 'PRODUCT',
        product: d.product || '',
        category: d.category || '',
        start_time: toLocalDatetime(d.start_time) || defaultTimes.start_time,
        end_time: toLocalDatetime(d.end_time) || defaultTimes.end_time,
        priority: d.priority ?? 1,
        is_active: d.is_active ?? true,
      });
    } else {
      setEditing(null);
      setFormData({
        title: '',
        discount_type: 'PERCENTAGE',
        discount_value: 10,
        target_type: 'PRODUCT',
        product: '',
        category: '',
        start_time: defaultTimes.start_time,
        end_time: defaultTimes.end_time,
        priority: 1,
        is_active: true,
      });
    }
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.target_type === 'PRODUCT' && !formData.product) {
      return showError('Please select a product for this price discount.');
    }
    if (formData.target_type === 'CATEGORY' && !formData.category) {
      return showError('Please select a category for this price discount.');
    }
    if (!formData.start_time || !formData.end_time) {
      return showError('Start and end times are required.');
    }
    if (new Date(formData.end_time) <= new Date(formData.start_time)) {
      return showError('End time must be after start time.');
    }

    const payload = {
      title: formData.title.trim(),
      discount_type: formData.discount_type,
      discount_value: parseFloat(formData.discount_value) || 0,
      product: formData.target_type === 'PRODUCT' ? (formData.product || null) : null,
      category: formData.target_type === 'CATEGORY' ? (formData.category || null) : null,
      start_time: toISOString(formData.start_time),
      end_time: toISOString(formData.end_time),
      priority: parseInt(formData.priority) || 1,
      is_active: formData.is_active,
    };

    try {
      if (editing) {
        await catalogService.updateDiscount(editing.id, payload);
        showSuccess('Price discount updated successfully');
      } else {
        await catalogService.createDiscount(payload);
        showSuccess('Price discount created successfully');
      }
      setModalOpen(false);
      fetchDiscounts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await catalogService.deleteDiscount(deleteId);
      showSuccess('Price discount deleted');
      fetchDiscounts();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteId(null);
    }
  };

  const columns = [
    {
      header: 'Title',
      accessor: 'title',
      render: (row) => (
        <div className="font-bold text-white flex items-center gap-2">
          <Percent className="w-4 h-4 text-purple-400 shrink-0" />
          <span>{row.title}</span>
        </div>
      )
    },
    {
      header: 'Type & Value',
      accessor: 'discount_value',
      render: (row) => (
        <span className="text-emerald-400 font-extrabold font-mono">
          {row.discount_type === 'PERCENTAGE'
            ? `${row.discount_value}% OFF`
            : `$${Number(row.discount_value).toFixed(2)} OFF`}
        </span>
      )
    },
    {
      header: 'Target (Product / Category)',
      accessor: 'target',
      render: (row) => {
        const productName = row.product_detail?.name || (row.product ? `Product ID: ${row.product}` : null);
        const categoryName = row.category_detail?.name || (row.category ? categories.find((c) => String(c.id) === String(row.category))?.name : null);
        if (productName) {
          return (
            <span className="bg-purple-500/10 border border-purple-500/30 text-purple-300 px-2.5 py-1 rounded-md text-xs inline-flex items-center gap-1">
              <Tag className="w-3 h-3 text-purple-400" /> {productName}
            </span>
          );
        }
        if (categoryName) {
          return (
            <span className="bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 px-2.5 py-1 rounded-md text-xs inline-flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Category: {categoryName}
            </span>
          );
        }
        return <span className="text-slate-500">—</span>;
      }
    },
    {
      header: 'Active Window',
      accessor: 'start_time',
      render: (row) => (
        <div className="text-xs text-slate-300 font-mono">
          <div>{new Date(row.start_time).toLocaleDateString()}</div>
          <div className="text-slate-500">→ {new Date(row.end_time).toLocaleDateString()}</div>
        </div>
      )
    },
    {
      header: 'Priority',
      accessor: 'priority',
      render: (row) => <span className="font-mono text-xs text-slate-300">P{row.priority || 1}</span>
    },
    {
      header: 'Status',
      accessor: 'is_currently_valid',
      render: (row) => row.is_currently_valid ? (
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400"><CheckCircle2 className="w-3.5 h-3.5" /> Active</span>
      ) : (
        <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500"><XCircle className="w-3.5 h-3.5" /> Inactive</span>
      )
    },
    {
      header: 'Actions',
      accessor: 'actions',
      align: 'right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <button onClick={() => handleOpenModal(row)} className="p-1.5 rounded bg-white/5 text-slate-300 hover:text-white hover:bg-white/10" title="Edit">
            <Edit2 className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => setDeleteId(row.id)} className="p-1.5 rounded bg-white/5 text-slate-400 hover:text-rose-400 hover:bg-white/10" title="Delete">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Price Discounts"
        subtitle="Configure time-based promotional discounts for products or categories"
        breadcrumbs={['Sales', 'Promotions', 'Price Discounts']}
        primaryAction={{
          label: 'Create Discount',
          icon: Plus,
          onClick: () => handleOpenModal(),
        }}
        searchValue={searchTerm}
        onSearchChange={handleSearchChange}
        searchPlaceholder="Search price discounts..."
        pagination={pagination}
      />

      <div className="px-4 md:px-6">
        {loading && discounts.length === 0 ? (
          <LoadingSkeleton count={4} type="table" />
        ) : discounts.length === 0 ? (
          <EmptyState
            icon={Percent}
            title="No price discounts created"
            description="Create promotional price discounts to dynamically calculate sale prices for your shop."
            action={
              <button onClick={() => handleOpenModal()} className="app-btn-primary">
                <Plus className="w-4 h-4" /> Create First Discount
              </button>
            }
          />
        ) : (
          <DataTable
            columns={columns}
            data={discounts}
            keyField="id"
            pagination={pagination}
          />
        )}
      </div>

      {/* Form Sheet / Modal */}
      <FormSheet
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? 'Edit Price Discount' : 'New Price Discount'}
        subtitle="Specify rules, discount values, and target products or categories"
        onSave={handleSubmit}
        saveLabel={editing ? 'Save Changes' : 'Create Discount'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Discount Title</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => field('title', e.target.value)}
              placeholder="e.g. Summer Flash Sale 20% OFF"
              required
              className="app-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Discount Type</label>
              <select
                value={formData.discount_type}
                onChange={(e) => field('discount_type', e.target.value)}
                className="app-input"
              >
                <option value="PERCENTAGE">Percentage (%)</option>
                <option value="FIXED_AMOUNT">Fixed Amount ($)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Discount Value {formData.discount_type === 'PERCENTAGE' ? '(%)' : '($)'}
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.discount_value}
                onChange={(e) => field('discount_value', e.target.value)}
                required
                className="app-input font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Target Scope</label>
            <div className="flex gap-4 mb-2">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer">
                <input
                  type="radio"
                  name="target_type"
                  value="PRODUCT"
                  checked={formData.target_type === 'PRODUCT'}
                  onChange={() => field('target_type', 'PRODUCT')}
                  className="text-purple-600 focus:ring-purple-500"
                />
                Specific Product
              </label>
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-300 cursor-pointer">
                <input
                  type="radio"
                  name="target_type"
                  value="CATEGORY"
                  checked={formData.target_type === 'CATEGORY'}
                  onChange={() => field('target_type', 'CATEGORY')}
                  className="text-purple-600 focus:ring-purple-500"
                />
                Entire Category
              </label>
            </div>

            {formData.target_type === 'PRODUCT' ? (
              <ProductSearchPicker
                value={formData.product}
                onChange={(pId) => field('product', pId)}
              />
            ) : (
              <select
                value={formData.category}
                onChange={(e) => field('category', e.target.value)}
                required
                className="app-input"
              >
                <option value="">— Select target category —</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Start Time</label>
              <input
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => field('start_time', e.target.value)}
                required
                className="app-input text-xs"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">End Time</label>
              <input
                type="datetime-local"
                value={formData.end_time}
                onChange={(e) => field('end_time', e.target.value)}
                required
                className="app-input text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Priority <span className="text-slate-500 font-normal lowercase">(higher number overrides conflicting discounts)</span>
            </label>
            <input
              type="number"
              min="1"
              value={formData.priority}
              onChange={(e) => field('priority', e.target.value)}
              className="app-input font-mono"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="disc_active"
              checked={formData.is_active}
              onChange={(e) => field('is_active', e.target.checked)}
              className="w-4 h-4 rounded bg-slate-900 border-white/20 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="disc_active" className="text-sm font-semibold text-slate-300">Active</label>
          </div>
        </form>
      </FormSheet>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Price Discount"
        message="Are you sure you want to delete this price discount?"
      />
    </div>
  );
}


