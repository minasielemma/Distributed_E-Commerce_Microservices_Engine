import React, { useState, useEffect } from 'react';
import { Truck, Calendar, MapPin, ExternalLink, Plus, Edit, Clock, CheckCircle2 } from 'lucide-react';
import { Badge } from './common/UIComponents';
import { orderService } from '../services/apiServices';

export const useAvailableCarriers = () => {
  const [carriers, setCarriers] = useState(['Standard Delivery', 'FedEx', 'UPS', 'USPS', 'DHL']);

  useEffect(() => {
    let isMounted = true;
    orderService.getAvailableCarriers()
      .then(res => {
        if (!isMounted) return;
        const names = res?.data?.names || (Array.isArray(res?.data?.carriers) ? res.data.carriers.map(c => c.name) : null);
        if (names && names.length > 0) {
          setCarriers(names);
        }
      })
      .catch(err => {
        console.warn('Failed to load carriers dynamically:', err);
      });
    return () => { isMounted = false; };
  }, []);

  return { carriers };
};

export const ShipmentCard = ({ shipment, onUpdateStatus }) => {
  if (!shipment) return null;

  return (
    <div className="bg-slate-900/80 p-5 rounded-2xl border border-white/10 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <Truck className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-sm font-bold text-white">{shipment.tracking_code}</span>
            <Badge status={shipment.status} />
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Carrier: <strong className="text-slate-200">{shipment.carrier || 'Standard Delivery'}</strong>
            {shipment.tracking_url && (
              <a
                href={shipment.tracking_url}
                target="_blank"
                rel="noreferrer"
                className="text-cyan-400 hover:text-cyan-300 ml-2 inline-flex items-center gap-1 hover:underline"
              >
                Track external <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
        <button
          onClick={() => onUpdateStatus(shipment)}
          className="px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors self-start sm:self-auto"
        >
          <Edit className="w-3.5 h-3.5 text-cyan-400" />
          Update Status
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="flex items-start gap-2 text-slate-300">
          <MapPin className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block text-white">{shipment.full_name}</span>
            <span>{shipment.address_line_1}{shipment.address_line_2 ? `, ${shipment.address_line_2}` : ''}</span>
            <span className="block text-slate-400">{shipment.city}, {shipment.postcode}, {shipment.country}</span>
          </div>
        </div>

        <div className="space-y-1 text-slate-400">
          {shipment.estimated_delivery_date && (
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <Calendar className="w-3.5 h-3.5" /> Est. Delivery: {shipment.estimated_delivery_date}
            </div>
          )}
          {shipment.shipped_at && (
            <div className="flex items-center gap-1.5 text-slate-400">
              <Clock className="w-3.5 h-3.5" /> Shipped: {new Date(shipment.shipped_at).toLocaleDateString()}
            </div>
          )}
          {shipment.notes && (
            <p className="italic text-slate-400 text-xs bg-white/5 p-2 rounded-lg border border-white/5 mt-1">
              "{shipment.notes}"
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export const ShipmentFormModal = ({ isOpen, onClose, order, onSubmit, loading }) => {
  if (!isOpen || !order) return null;

  const { carriers: availableCarriers } = useAvailableCarriers();
  const addr = order.shipping_address || {};
  const [carrier, setCarrier] = useState('Standard Delivery');
  const [trackingCode, setTrackingCode] = useState('');
  const [estDate, setEstDate] = useState('');
  const [fullName, setFullName] = useState(addr.full_name || 'Customer');
  const [phone, setPhone] = useState(addr.phone || addr.phone_number || '');
  const [line1, setLine1] = useState(addr.address_line_1 || addr.street || '');
  const [line2, setLine2] = useState(addr.address_line_2 || '');
  const [city, setCity] = useState(addr.city || '');
  const [state, setState] = useState(addr.state || '');
  const [postcode, setPostcode] = useState(addr.postal_code || addr.postcode || '00000');
  const [country, setCountry] = useState(addr.country || 'USA');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      carrier,
      tracking_code: trackingCode || undefined,
      estimated_delivery_date: estDate || undefined,
      full_name: fullName,
      contact_phone: phone,
      address_line_1: line1,
      address_line_2: line2,
      city,
      state,
      postcode,
      country,
      notes,
      status: 'SHIPPED',
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="glass-panel border border-white/15 p-6 w-full max-w-xl shadow-2xl animate-in fade-in my-8">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Truck className="text-cyan-400" /> Dispatch / Create Shipment for Order #{order.id}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Carrier / Provider</label>
              <select
                value={carrier}
                onChange={(e) => setCarrier(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-medium"
              >
                {availableCarriers.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-300 block mb-1">Custom Tracking Number (Optional)</label>
              <input
                type="text"
                placeholder="Auto-generated if empty"
                value={trackingCode}
                onChange={(e) => setTrackingCode(e.target.value)}
                className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-300 block mb-1">Estimated Delivery Date</label>
            <input
              type="date"
              value={estDate}
              onChange={(e) => setEstDate(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="space-y-3 pt-2 border-t border-white/10">
            <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 block">Shipping Destination</span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Full Name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-xl p-2 text-xs text-white"
                required
              />
              <input
                type="text"
                placeholder="Phone Number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-xl p-2 text-xs text-white"
              />
              <input
                type="text"
                placeholder="Address Line 1"
                value={line1}
                onChange={(e) => setLine1(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-xl p-2 text-xs text-white md:col-span-2"
                required
              />
              <input
                type="text"
                placeholder="City"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-xl p-2 text-xs text-white"
                required
              />
              <input
                type="text"
                placeholder="Country"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                className="bg-slate-900 border border-white/10 rounded-xl p-2 text-xs text-white"
                required
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-300 block mb-1">Dispatch Notes</label>
            <textarea
              rows={2}
              placeholder="Internal or customer notes regarding dispatch..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 text-xs font-medium">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Shipment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export const ShipmentStatusModal = ({ isOpen, onClose, shipment, onSubmit, loading }) => {
  if (!isOpen || !shipment) return null;

  const { carriers: availableCarriers } = useAvailableCarriers();
  const [status, setStatus] = useState(shipment.status || 'PREPARING');
  const [notes, setNotes] = useState(shipment.notes || '');
  const [carrier, setCarrier] = useState(shipment.carrier || 'Standard Delivery');
  const [trackingCode, setTrackingCode] = useState(shipment.tracking_code || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(shipment.id, { status, notes, carrier, tracking_code: trackingCode });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="glass-panel border border-white/15 p-6 w-full max-w-md shadow-2xl animate-in fade-in my-8 space-y-5">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Edit className="text-cyan-400" /> Update Shipment Status
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-bold text-slate-300 block mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-cyan-500 font-bold"
            >
              <option value="PREPARING">PREPARING</option>
              <option value="LABEL_CREATED">LABEL_CREATED</option>
              <option value="SHIPPED">SHIPPED</option>
              <option value="IN_TRANSIT">IN_TRANSIT</option>
              <option value="OUT_FOR_DELIVERY">OUT_FOR_DELIVERY</option>
              <option value="DELIVERED">DELIVERED</option>
              <option value="FAILED_ATTEMPT">FAILED_ATTEMPT</option>
              <option value="RETURNED">RETURNED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-300 block mb-1">Carrier</label>
            <select
              value={carrier || 'Standard Delivery'}
              onChange={(e) => setCarrier(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-medium"
            >
              {availableCarriers.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-300 block mb-1">Tracking Code</label>
            <input
              type="text"
              value={trackingCode}
              onChange={(e) => setTrackingCode(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white font-mono"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-300 block mb-1">Status Update Notes / Location</label>
            <textarea
              rows={3}
              placeholder="e.g. Arrived at regional sorting facility in Chicago..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 text-xs font-medium">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Update & Notify'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
