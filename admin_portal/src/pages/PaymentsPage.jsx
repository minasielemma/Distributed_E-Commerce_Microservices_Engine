import React, { useState, useEffect, useCallback } from 'react';
import { paymentService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, DataTable, EmptyState, LoadingSkeleton, Badge } from '../components/common/UIComponents';
import { CreditCard } from 'lucide-react';

export default function PaymentsPage() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showError } = useToast();

  const pagination = usePagination({ initialPageSize: 10 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange } = pagination;

  const fetchPayments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await paymentService.getPayments({ page, page_size: pageSize });
      const resData = res?.data;
      const list = Array.isArray(resData) ? resData : (resData?.results || []);
      setPayments(list);
      updatePaginationState(resData);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, updatePaginationState, showError]);

  useEffect(() => {
    fetchPayments();
  }, [fetchPayments]);

  const columns = [
    {
      header: 'Payment ID',
      accessor: 'id',
      render: (row) => (
        <div className="font-mono font-bold text-white flex items-center gap-2">
          <CreditCard className="w-4 h-4 text-[#7c7bad] shrink-0" />
          <span>#{row.id}</span>
        </div>
      )
    },
    {
      header: 'Order Reference',
      accessor: 'order_id',
      render: (row) => <span className="font-mono text-xs text-[#7c7bad]">Order #{row.order_id || row.order}</span>
    },
    {
      header: 'Amount ($)',
      accessor: 'amount',
      render: (row) => <span className="font-extrabold font-mono text-[#48bb78]">${Number(row.amount || 0).toFixed(2)}</span>
    },
    {
      header: 'Payment Status',
      accessor: 'status',
      render: (row) => <Badge status={row.status || row.state} />
    },
    {
      header: 'Timestamp',
      accessor: 'created_at',
      render: (row) => <span className="text-xs text-[#94a3b8] font-mono">{new Date(row.created_at || Date.now()).toLocaleString()}</span>
    }
  ];

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Payment Transactions"
        subtitle="Polar.sh checkout transactions and webhook payment audit records"
        breadcrumbs={['Finance', 'Payments']}
        pagination={pagination}
      />

      <div className="px-4 md:px-6">
        {loading && payments.length === 0 ? (
          <LoadingSkeleton count={3} type="table" />
        ) : payments.length === 0 ? (
          <EmptyState
            icon={CreditCard}
            title="No payments recorded"
            description="Payment logs will automatically record when customers pay for orders."
          />
        ) : (
          <DataTable
            columns={columns}
            data={payments}
            keyField="id"
            pagination={pagination}
          />
        )}
      </div>
    </div>
  );
}

