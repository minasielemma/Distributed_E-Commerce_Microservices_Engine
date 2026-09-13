import React, { useState } from 'react';
import { Truck, Calendar, MapPin, ExternalLink, Plus, Edit, Clock, CheckCircle2 } from 'lucide-react';
import { Badge } from './common/UIComponents';

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
                className="text-cyan-400 hover:underline ml-2 inline-flex items-center gap-1"
              >
                Track Link <ExternalLink size={10} />
              </a>
            )}
          </div>
        </div>

        {onUpdateStatus && (
          <button
            onClick={() => onUpdateStatus(shipment)}
            className="px-3 py-1.5 rounded-xl bg-cyan-600/20 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-600 hover:text-white transition-all text-xs font-semibold inline-flex items-center gap-1.5"
          >
            <Edit className="w-3.5 h-3.5" /> Update Status
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div>
          <span className="text-slate-400 block font-medium">Recipient</span>
          <span className="font-bold text-white truncate block">{shipment.full_name}</span>
        </div>
        <div>
          <span className="text-slate-400 block font-medium">Destination</span>
          <span className="text-slate-300 truncate block">{shipment.city}, {shipment.country}</span>
        </div>
        <div>
          <span className="text-slate-400 block font-medium">Estimated Delivery</span>
          <span className="text-slate-200 font-semibold block">
            {shipment.estimated_delivery_date ? new Date(shipment.estimated_delivery_date).toLocaleDateString() : 'N/A'}
          </span>
        </div>
        <div>
          <span className="text-slate-400 block font-medium">Dispatched At</span>
          <span className="text-slate-200 font-semibold block">
            {shipment.shipped_at ? new Date(shipment.shipped_at).toLocaleDateString() : 'Not dispatched'}
          </span>
        </div>
      </div>

      {shipment.notes && (
        <div className="text-xs bg-slate-950 p-2.5 rounded-xl border border-white/5 text-slate-300 italic">
          "{shipment.notes}"
        </div>
      )}
    </div>
  );
};

export const ShipmentFormModal = ({ isOpen, onClose, order, onSubmit, loading }) => {
  if (!isOpen || !order) return null;

  const addr = order.shipping_address || {};
  const [carrier, setCarrier] = useState('FedEx');
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
                className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="FedEx">FedEx</option>
                <option value="UPS">UPS</option>
                <option value="USPS">USPS</option>
                <option value="DHL">DHL</option>
                <option value="Standard Delivery">Standard Delivery / Local</option>
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

  const [status, setStatus] = useState(shipment.status || 'PREPARING');
  const [notes, setNotes] = useState(shipment.notes || '');
  const [carrier, setCarrier] = useState(shipment.carrier || '');
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
            <input
              type="text"
              value={carrier}
              onChange={(e) => setCarrier(e.target.value)}
              className="w-full bg-slate-900 border border-white/10 rounded-xl p-2.5 text-sm text-white"
            />
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
