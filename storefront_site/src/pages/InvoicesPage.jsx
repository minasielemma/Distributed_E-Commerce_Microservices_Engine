import React, { useState, useEffect } from 'react';
import { financeService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Modal, LoadingSkeleton, Badge, Pagination } from '../components/common/UIComponents';
import { Printer } from 'lucide-react';
import { usePagination } from '../hooks/usePagination';
import { Link } from 'react-router-dom';

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const { showError } = useToast();

  const pagination = usePagination({ initialPage: 1, initialPageSize: 10 });

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const res = await financeService.getInvoices({
        page: pagination.page,
        page_size: pagination.pageSize,
      });
      const data = res?.data;
      if (Array.isArray(data)) {
        setInvoices(data);
        pagination.updatePaginationState({ count: data.length, total_pages: 1, current_page: 1 });
      } else {
        setInvoices(data?.results || []);
        pagination.updatePaginationState(data);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [pagination.page, pagination.pageSize]);

  const handlePrintInvoice = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <h1 className="text-3xl font-normal">Invoices & Receipts</h1>
          <LoadingSkeleton count={3} type="table" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto space-y-6">
        <div>
          <Link to="/profile" className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline mb-2 block">
            Your Account
          </Link>
          <h1 className="text-3xl font-normal">Invoices & Receipts</h1>
        </div>

        {invoices.length === 0 ? (
          <div className="py-8">
             <p className="text-lg">No invoices found.</p>
             <p className="text-sm mt-2 text-[#565959]">Invoices are automatically created whenever you place and complete an order.</p>
          </div>
        ) : (
          <div className="border border-[#D5D9D9] rounded bg-white overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#F0F2F2] text-[#565959] border-b border-[#D5D9D9]">
                <tr>
                  <th className="p-4 font-bold">Issued Date</th>
                  <th className="p-4 font-bold">Invoice #</th>
                  <th className="p-4 font-bold">Total Amount</th>
                  <th className="p-4 font-bold">Status</th>
                  <th className="p-4 text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D5D9D9]">
                {invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td className="p-4 text-[#565959]">
                      {new Date(inv.created_at || Date.now()).toLocaleDateString()}
                    </td>
                    <td className="p-4 font-medium">{inv.invoice_number}</td>
                    <td className="p-4 font-bold text-[#B12704]">
                      ${Number(inv.total_amount || inv.amount || 0).toFixed(2)}
                    </td>
                    <td className="p-4"><Badge status={inv.status} /></td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => setSelectedInvoice(inv)}
                        className="text-amazon-link-teal hover:text-amazon-orange hover:underline text-sm font-medium"
                      >
                        View Receipt
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {pagination.totalPages > 1 && (
              <div className="p-4 border-t border-[#D5D9D9] flex justify-center bg-white">
                <Pagination
                  currentPage={pagination.page}
                  totalPages={pagination.totalPages}
                  onPageChange={pagination.handlePageChange}
                />
              </div>
            )}
          </div>
        )}

        {/* Invoice Detail Modal */}
        {selectedInvoice && (
          <Modal
            isOpen={!!selectedInvoice}
            onClose={() => setSelectedInvoice(null)}
            title={`Invoice ${selectedInvoice.invoice_number}`}
            maxWidth="max-w-2xl"
          >
            <div className="space-y-6 text-[#111] printable-area">
              <div className="p-6 border border-[#D5D9D9] rounded bg-white space-y-6">
                <div className="flex justify-between items-start border-b border-[#D5D9D9] pb-6">
                  <div>
                    <div className="font-bold text-lg mb-1">
                      Payment Receipt
                    </div>
                    <p className="text-sm text-[#565959]">Invoice Number: {selectedInvoice.invoice_number}</p>
                    {selectedInvoice.order_id && (
                      <p className="text-sm text-[#565959]">Order Reference: #{selectedInvoice.order_id.slice(0, 8)}</p>
                    )}
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-sm uppercase text-[#565959]">
                      {selectedInvoice.status || 'PAID'}
                    </span>
                    <p className="text-sm text-[#565959] mt-2">Issued: {new Date(selectedInvoice.created_at || Date.now()).toLocaleDateString()}</p>
                  </div>
                </div>

                <div className="flex justify-between items-center py-2">
                  <span className="text-base font-bold">Total Paid Amount:</span>
                  <span className="text-2xl font-bold text-[#B12704]">
                    ${Number(selectedInvoice.total_amount || selectedInvoice.amount || 0).toFixed(2)}
                  </span>
                </div>

                {selectedInvoice.items_summary && selectedInvoice.items_summary.length > 0 && (
                  <div>
                    <h4 className="text-sm font-bold text-[#111] mb-2">Purchased Items</h4>
                    <div className="border border-[#D5D9D9] rounded overflow-hidden text-sm">
                      <table className="w-full text-left">
                        <thead className="bg-[#F0F2F2] text-[#565959]">
                          <tr>
                            <th className="p-3">Item</th>
                            <th className="p-3">Qty</th>
                            <th className="p-3 text-right">Price</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#D5D9D9]">
                          {selectedInvoice.items_summary.map((it, idx) => (
                            <tr key={idx}>
                              <td className="p-3">{it.product_name || `Item #${idx + 1}`}</td>
                              <td className="p-3">{it.quantity || 1}</td>
                              <td className="p-3 text-right font-bold">${Number(it.unit_price || it.total_price || 0).toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-4 no-print">
                <button
                  onClick={() => setSelectedInvoice(null)}
                  className="btn-secondary py-2 px-4 shadow-sm text-sm"
                >
                  Close
                </button>
                <button
                  onClick={handlePrintInvoice}
                  className="btn-buy-now py-2 px-4 shadow-sm text-sm flex items-center gap-2"
                >
                  <Printer className="w-4 h-4" /> Print / Save PDF
                </button>
              </div>
            </div>
          </Modal>
        )}
      </div>
    </div>
  );
}
