import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { orderService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ShipmentTracker } from '../components/ShipmentTracker';
import { EmptyState, LoadingSkeleton } from '../components/common/UIComponents';
import { ChevronLeft, Search } from 'lucide-react';

export const OrderTrackingPage = () => {
  const { id, trackingCode } = useParams();
  const [order, setOrder] = useState(null);
  const [shipments, setShipments] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [customTrackingInput, setCustomTrackingInput] = useState('');
  const { showSuccess, showError } = useToast();

  useEffect(() => {
    fetchTrackingData();

    const handleRealtimeNotification = (e) => {
      const notif = e.detail;
      if (!notif) return;
      const meta = notif.metadata || {};

      const isMatchingOrder = id && (meta.order_id === id || String(meta.order_id) === String(id));
      const isMatchingTracking = trackingCode && (meta.tracking_code === trackingCode || String(meta.tracking_code) === String(trackingCode));

      if (isMatchingOrder || isMatchingTracking || notif.notification_type === 'SHIPMENT') {
        if (meta.status) {
          setShipments((prevShipments) => {
            if (!prevShipments || prevShipments.length === 0) {
              return [{
                id: meta.shipment_id || Math.random().toString(),
                order_id: meta.order_id || id,
                tracking_code: meta.tracking_code || trackingCode,
                status: meta.status,
                carrier: meta.carrier || 'Standard Carrier',
                estimated_delivery_date: meta.estimated_delivery,
                notes: meta.notes,
              }];
            }
            return prevShipments.map((s) => {
              if ((meta.tracking_code && s.tracking_code === meta.tracking_code) || (meta.order_id && s.order_id === meta.order_id) || prevShipments.length === 1) {
                return {
                  ...s,
                  status: meta.status,
                  carrier: meta.carrier || s.carrier,
                  estimated_delivery_date: meta.estimated_delivery || s.estimated_delivery_date,
                };
              }
              return s;
            });
          });

          setHistory((prevHistory) => [
            {
              id: Math.random().toString(),
              to_status: meta.status,
              notes: meta.notes || notif.message || `Package status updated to ${meta.status}`,
              created_at: meta.timestamp || notif.created_at || new Date().toISOString(),
            },
            ...prevHistory,
          ]);

          showSuccess(`Tracking update: Package status is now ${meta.status}`);
        } else {
          fetchTrackingData();
        }
      }
    };

    window.addEventListener('notification_received', handleRealtimeNotification);
    return () => window.removeEventListener('notification_received', handleRealtimeNotification);
  }, [id, trackingCode]);

  const fetchTrackingData = async () => {
    setLoading(true);
    try {
      if (trackingCode) {
        // Track by tracking code directly
        const res = await orderService.trackPackage(trackingCode);
        setShipments([res.data]);
        setHistory(res.data?.history || []);
      } else if (id) {
        // Track by order ID
        const [ordRes, shipRes] = await Promise.allSettled([
          orderService.getOrder(id),
          orderService.getShipments(id),
        ]);

        if (ordRes.status === 'fulfilled') {
          setOrder(ordRes.value.data);
        }
        if (shipRes.status === 'fulfilled') {
          const list = Array.isArray(shipRes.value.data) ? shipRes.value.data : [shipRes.value.data];
          setShipments(list.filter(Boolean));

          if (list.length > 0 && list[0]?.id) {
            const histRes = await orderService.getShipmentHistory(list[0].id).catch(() => null);
            if (histRes) setHistory(histRes.data || []);
          }
        }
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleManualSearch = (e) => {
    e.preventDefault();
    if (customTrackingInput.trim()) {
      window.location.href = `/orders/track/${encodeURIComponent(customTrackingInput.trim())}`;
    }
  };

  if (loading) {
    return (
      <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <LoadingSkeleton count={3} type="card" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto space-y-6">
        {/* Top Header & Breadcrumb */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <Link to="/orders" className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline inline-flex items-center gap-1 mb-2">
              <ChevronLeft size={16} /> Return to Orders
            </Link>
            <h1 className="text-3xl font-normal">Track Package</h1>
            {order && (
              <p className="text-sm mt-1">
                <span className="font-bold text-[#565959]">Order ID:</span> {order.id}
              </p>
            )}
          </div>

          {/* Manual Tracking Search */}
          <form onSubmit={handleManualSearch} className="flex items-center gap-2">
            <input
              type="text"
              value={customTrackingInput}
              onChange={(e) => setCustomTrackingInput(e.target.value)}
              placeholder="Enter tracking ID..."
              className="border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow w-48"
            />
            <button type="submit" className="btn-secondary py-2 px-4 shadow-sm text-sm">
              Track
            </button>
          </form>
        </div>

        {/* Main Trackers List */}
        {shipments.length === 0 ? (
           <div className="py-8">
             <p className="text-lg">No shipment info available yet.</p>
             <p className="text-sm mt-2 text-[#565959]">
               Your order is currently being processed. Shipment details will appear here once dispatched.
             </p>
           </div>
        ) : (
          <div>
            {shipments.map((shipment) => (
              <ShipmentTracker key={shipment.id} shipment={shipment} history={history} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
