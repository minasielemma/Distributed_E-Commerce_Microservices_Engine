import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';

export default function CheckoutSuccessPage() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get('order_id');

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-12 px-4 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded shadow-sm border border-[#D5D9D9] p-8 text-center space-y-6">
        <CheckCircle className="mx-auto text-green-600 mb-4" size={64} />
        <h1 className="text-3xl font-normal text-[#111]">Thank you for your purchase!</h1>
        <p className="text-[#565959] text-base">
          Your order {orderId ? <span className="font-bold text-[#111]">#{orderId.substring(0, 8)}</span> : ''} has been placed successfully.
        </p>
        <p className="text-[#565959] text-sm">
          We'll send you a confirmation email with details of your order.
        </p>
        <div className="pt-4 flex flex-col gap-3">
          <Link
            to={orderId ? `/orders/${orderId}/tracking` : "/orders"}
            className="w-full py-2 px-4 rounded bg-[#FFD814] hover:bg-[#F7CA00] text-[#111] text-sm font-medium border border-[#FCD200] hover:border-[#F2C200] shadow-sm cursor-pointer block"
          >
            Track Order
          </Link>
          <Link
            to="/"
            className="w-full py-2 px-4 rounded bg-white hover:bg-[#F7FAFA] text-[#111] text-sm font-medium border border-[#D5D9D9] shadow-sm cursor-pointer block"
          >
            Continue Shopping
          </Link>
        </div>
      </div>
    </div>
  );
}
