import React, { useState, useEffect } from 'react';
import { paymentService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { LoadingSkeleton, Badge } from '../components/common/UIComponents';
import { Link } from 'react-router-dom';

export default function PaymentsPage() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showError } = useToast();

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const res = await paymentService.getPayments();
      const list = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setPayments(list);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();

    const handleRealtimeNotification = (e) => {
      const notif = e.detail;
      if (!notif) return;
      if (notif.notification_type === 'PAYMENT' || notif.metadata?.payment_id || notif.metadata?.order_id) {
        fetchPayments();
      }
    };

    window.addEventListener('notification_received', handleRealtimeNotification);
    return () => window.removeEventListener('notification_received', handleRealtimeNotification);
  }, []);

  if (loading) {
    return (
      <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <h1 className="text-3xl font-normal">Transactions</h1>
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
          <h1 className="text-3xl font-normal">Transactions</h1>
        </div>

        {payments.length === 0 ? (
          <div className="py-8">
             <p className="text-lg">You do not have any recent transactions.</p>
          </div>
        ) : (
          <div className="border border-[#D5D9D9] rounded bg-white overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap min-w-[600px]">
              <thead className="bg-[#F0F2F2] text-[#565959] border-b border-[#D5D9D9]">
                <tr>
                  <th className="p-4 font-bold">Date</th>
                  <th className="p-4 font-bold">Order ID</th>
                  <th className="p-4 font-bold">Amount</th>
                  <th className="p-4 font-bold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D5D9D9]">
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td className="p-4 text-[#565959]">
                      {new Date(p.created_at || Date.now()).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                    </td>
                    <td className="p-4">
                      <Link to={`/orders`} className="text-amazon-link-teal hover:text-amazon-orange hover:underline">
                        {p.order_id || p.order}
                      </Link>
                    </td>
                    <td className="p-4 font-bold text-[#B12704]">
                      ${Number(p.amount || 0).toFixed(2)}
                    </td>
                    <td className="p-4">
                       <span className="font-bold uppercase text-xs tracking-wide">
                          {p.status || p.state}
                       </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
