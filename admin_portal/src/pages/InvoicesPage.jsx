import React, { useState, useEffect, useCallback } from 'react';
import { financeService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, FormSheet, Modal, EmptyState, LoadingSkeleton, Badge } from '../components/common/UIComponents';
import { FileText, Plus, Eye } from 'lucide-react';

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange } = pagination;

  const [formData, setFormData] = useState({
    invoice_number: `INV-${Date.now()}`,
    customer_name: '',
    amount: 100,
    due_date: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
    status: 'ISSUED',
  });

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const res = await financeService.getInvoices({ page, page_size: pageSize });
      const resData = res?.data;
      const list = Array.isArray(resData) ? resData : (resData?.results || []);
      setInvoices(list);
      updatePaginationState(resData);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, updatePaginationState, showError]);

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await financeService.createInvoice(formData);
      showSuccess('Invoice generated successfully!');
      setModalOpen(false);
      fetchInvoices();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const columns = [
    {
      header: 'Invoice #',
      accessor: 'invoice_number',
      render: (row) => (
        <div className="font-mono font-bold text-white flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#7c7bad] shrink-0" />
          <span>{row.invoice_number || `#${row.id}`}</span>
        </div>
      )
    },
    {
      header: 'Customer / Tenant',
      accessor: 'customer_name',
      render: (row) => <span className="text-[#e2e8f0] font-semibold">{row.customer_name || row.customer_id || row.tenant_id || 'Client'}</span>
    },
    {
      header: 'Total Amount',
      accessor: 'amount',
      render: (row) => <span className="font-extrabold font-mono text-[#7c7bad]">${Number(row.total_amount || row.amount || 0).toFixed(2)}</span>
    },
    {
      header: 'Due Date',
      accessor: 'due_date',
      render: (row) => <span className="text-xs text-[#94a3b8] font-mono">{row.due_date || (row.created_at ? new Date(row.created_at).toLocaleDateString() : 'N/A')}</span>
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <Badge status={row.status} />
    },
    {
      header: 'Actions',
      accessor: 'actions',
      align: 'right',
      render: (row) => (
        <button onClick={() => setSelectedInvoice(row)} className="p-1.5 rounded bg-white/5 text-[#e2e8f0] hover:text-white hover:bg-white/10" title="View Detail">
          <Eye className="w-3.5 h-3.5" />
        </button>
      )
    }
  ];

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Invoices & Customer Billing"
        subtitle="Issue and track commercial tenant billing invoices and statements"
        breadcrumbs={['Finance', 'Invoices']}
        primaryAction={{
          label: 'Issue Invoice',
          icon: Plus,
          onClick: () => setModalOpen(true),
        }}
        pagination={pagination}
      />

      <div className="px-4 md:px-6">
        {loading && invoices.length === 0 ? (
          <LoadingSkeleton count={3} type="table" />
        ) : invoices.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No invoices issued"
            description="Generate commercial invoices for order transactions or SaaS tenant billing."
            action={
              <button onClick={() => setModalOpen(true)} className="app-btn-primary">
                <Plus className="w-4 h-4" /> Issue First Invoice
              </button>
            }
          />
        ) : (
          <DataTable
            columns={columns}
            data={invoices}
            keyField="id"
            pagination={pagination}
          />
        )}
      </div>

      {/* Issue Form Sheet */}
      <FormSheet
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Issue New Invoice"
        subtitle="Create commercial billing statement for customer or tenant"
        onSave={handleSubmit}
        saveLabel="Issue Invoice"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Invoice Number</label>
            <input
              type="text"
              value={formData.invoice_number}
              onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
              required
              className="app-input font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Customer / Tenant Name</label>
            <input
              type="text"
              value={formData.customer_name}
              onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
              placeholder="e.g. Acme Corp"
              required
              className="app-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Amount ($)</label>
              <input
                type="number"
                step="0.01"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
                required
                className="app-input font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                required
                className="app-input text-xs"
              />
            </div>
          </div>
        </form>
      </FormSheet>

      {/* Invoice Detail View */}
      {selectedInvoice && (
        <Modal
          isOpen={!!selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
          title={`Invoice Statement ${selectedInvoice.invoice_number || `#${selectedInvoice.id}`}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded bg-[#0f172a] border border-[#2d3748] space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-[#2d3748]">
                <span className="text-[#94a3b8]">Customer / Tenant:</span>
                <span className="font-bold text-white text-sm">{selectedInvoice.customer_name || 'Client'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94a3b8]">Amount Due:</span>
                <span className="font-bold text-[#7c7bad] text-base font-mono">${Number(selectedInvoice.amount || 0).toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[#94a3b8]">Due Date:</span>
                <span className="text-slate-200 font-mono">{selectedInvoice.due_date || 'N/A'}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-[#2d3748]">
                <span className="text-[#94a3b8]">Status:</span>
                <Badge status={selectedInvoice.status} />
              </div>
            </div>
            <div className="flex justify-end">
              <button onClick={() => setSelectedInvoice(null)} className="app-btn-secondary">
                Close Statement
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

