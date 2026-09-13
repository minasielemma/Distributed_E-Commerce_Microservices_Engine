import React from 'react';
import { Package, Truck, CheckCircle2, Clock, AlertCircle, ExternalLink, MapPin, Calendar } from 'lucide-react';
import { Badge } from './common/UIComponents';

const STAGES = [
  { key: 'PREPARING', label: 'Preparing' },
  { key: 'LABEL_CREATED', label: 'Label Created' },
  { key: 'SHIPPED', label: 'Shipped' },
  { key: 'IN_TRANSIT', label: 'In Transit' },
  { key: 'OUT_FOR_DELIVERY', label: 'Out for Delivery' },
  { key: 'DELIVERED', label: 'Delivered' },
];

const STAGE_ORDER = ['PREPARING', 'LABEL_CREATED', 'SHIPPED', 'IN_TRANSIT', 'OUT_FOR_DELIVERY', 'DELIVERED'];

export const ShipmentTracker = ({ shipment, history = [] }) => {
  if (!shipment) return null;

  const currentStatus = shipment.status || 'PREPARING';
  const currentStageIndex = STAGE_ORDER.indexOf(currentStatus);

  return (
    <div className="border border-[#D5D9D9] rounded-lg p-6 bg-white mb-6">
      {/* Shipment Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4">
        <div>
          <h2 className="text-xl font-bold text-[#111]">
            {currentStatus === 'DELIVERED' ? 'Delivered' : 'Arriving soon'}
          </h2>
          {shipment.estimated_delivery_date && (
             <div className="text-[#007185] font-bold text-sm mt-1">
               {new Date(shipment.estimated_delivery_date).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
             </div>
          )}
          <div className="text-sm text-[#565959] mt-2">
            Tracking ID: {shipment.tracking_code}
          </div>
          <div className="text-sm text-[#565959] flex items-center gap-2">
            <span>Carrier: <strong className="text-[#111]">{shipment.carrier || 'Standard Delivery'}</strong></span>
            {shipment.tracking_url && (
              <a
                href={shipment.tracking_url}
                target="_blank"
                rel="noreferrer"
                className="text-amazon-link-teal hover:text-amazon-orange hover:underline inline-flex items-center gap-1"
              >
                Track on carrier website <ExternalLink size={12} />
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Visual Progression Bar */}
      <div className="py-8 my-4 border-t border-b border-[#D5D9D9]">
        <div className="relative flex items-center justify-between max-w-2xl mx-auto">
          {/* Connecting Line */}
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-[#D5D9D9] z-0" />
          <div
            className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-[#007185] z-0 transition-all duration-500"
            style={{
              width: currentStageIndex >= 0 ? `${(currentStageIndex / (STAGE_ORDER.length - 1)) * 100}%` : '0%',
            }}
          />

          {/* Stage Nodes */}
          {STAGES.map((st, idx) => {
            const isDone = currentStageIndex >= idx;
            const isCurrent = currentStageIndex === idx;

            return (
              <div key={st.key} className="relative z-10 flex flex-col items-center group bg-white px-2">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isCurrent || isDone
                      ? 'bg-[#007185]'
                      : 'bg-[#D5D9D9]'
                  }`}
                >
                  {(isDone || isCurrent) && <CheckCircle2 className="w-4 h-4 text-white" />}
                </div>
                <span
                  className={`text-xs font-bold mt-2 text-center absolute top-8 w-24 -ml-12 left-1/2 leading-tight ${
                    isCurrent || isDone
                      ? 'text-[#111]'
                      : 'text-[#565959]'
                  }`}
                >
                  {st.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Delivery Address & Notes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 text-sm text-[#111]">
        <div>
          <div className="font-bold mb-2">Shipping Address</div>
          <div className="text-[#565959]">
            <div className="font-medium text-[#111]">{shipment.full_name}</div>
            <div>{shipment.address_line_1} {shipment.address_line_2}</div>
            <div>{shipment.city}{shipment.state ? `, ${shipment.state}` : ''} {shipment.postcode}, {shipment.country}</div>
            {shipment.contact_phone && <div>Phone: {shipment.contact_phone}</div>}
          </div>
        </div>

        {shipment.notes && (
          <div>
            <div className="font-bold mb-2">Delivery Instructions</div>
            <p className="text-[#565959] italic">"{shipment.notes}"</p>
          </div>
        )}
      </div>

      {/* Status History Timeline */}
      {history.length > 0 && (
        <div className="pt-6 mt-6 border-t border-[#D5D9D9]">
          <h4 className="text-base font-bold text-[#111] mb-4">Tracking History</h4>
          <div className="space-y-4">
            {history.map((log) => (
              <div key={log.id} className="flex items-start gap-4 text-sm">
                 <div className="w-32 shrink-0 text-[#565959] font-medium">
                  {new Date(log.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </div>
                <div className="flex-1">
                  <div className="font-bold text-[#111]">
                    {log.to_status}
                    {log.from_status && <span className="font-normal text-[#565959] ml-2">(Previously: {log.from_status})</span>}
                  </div>
                  {log.notes && <div className="text-[#565959] mt-1">{log.notes}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
