import React from 'react';
import { X, AlertTriangle, Star, ChevronLeft, ChevronRight, Inbox } from 'lucide-react';

export const Modal = ({ isOpen, onClose, title, children, maxWidth = 'max-w-2xl' }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/70 backdrop-blur-sm overflow-y-auto">
      <div className={`relative w-full ${maxWidth} bg-white rounded-lg border border-amazon-border-card p-4 sm:p-6 shadow-xl animate-in fade-in zoom-in-95 duration-200 my-auto flex flex-col max-h-[90vh] sm:max-h-[85vh] overflow-hidden`}>
        <div className="flex items-center justify-between pb-3 sm:pb-4 border-b border-[#D5D9D9] mb-4 shrink-0">
          <h3 className="text-lg sm:text-xl font-bold text-amazon-text-primary">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-500 hover:text-black hover:bg-slate-100 transition-colors touch-target"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-1">{children}</div>
      </div>
    </div>
  );
};

export const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message, confirmText = 'Delete', isDanger = true }) => {
  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} maxWidth="max-w-md">
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-xl ${isDanger ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'}`}>
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <p className="text-amazon-text-secondary text-sm leading-relaxed">{message}</p>
        </div>
      </div>
      <div className="flex justify-end gap-3 mt-6">
        <button onClick={onClose} className="btn-secondary">Cancel</button>
        <button
          onClick={() => { onConfirm(); onClose(); }}
          className={isDanger ? 'px-4 py-2 bg-amazon-deal-red hover:bg-red-800 text-white font-medium rounded-lg transition-colors' : 'btn-cart'}
        >
          {confirmText}
        </button>
      </div>
    </Modal>
  );
};

export const EmptyState = ({ icon: Icon = Inbox, title = 'No data found', description = 'There are no items to display right now.', action }) => (
  <div className="amz-card p-12 text-center flex flex-col items-center justify-center my-6">
    <div className="p-4 rounded-full bg-slate-100 text-slate-400 mb-4 border border-[#D5D9D9]">
      <Icon className="w-10 h-10" />
    </div>
    <h3 className="text-lg font-bold text-amazon-text-primary mb-1">{title}</h3>
    <p className="text-amazon-text-secondary text-sm max-w-sm mb-6">{description}</p>
    {action && action}
  </div>
);

export const LoadingSkeleton = ({ count = 3, type = 'card' }) => {
  if (type === 'table') {
    return (
      <div className="amz-card p-6 space-y-4 animate-pulse">
        <div className="h-6 bg-slate-200 rounded w-1/4 mb-4"></div>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-10 bg-slate-100 rounded-lg w-full"></div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 my-6">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="amz-card p-5 animate-pulse space-y-4">
          <div className="h-44 bg-slate-200 rounded-xl w-full"></div>
          <div className="h-5 bg-slate-200 rounded w-3/4"></div>
          <div className="h-4 bg-slate-100 rounded w-1/2"></div>
          <div className="h-8 bg-slate-200 rounded-full w-full mt-4"></div>
        </div>
      ))}
    </div>
  );
};

export const Pagination = ({
  currentPage = 1,
  totalPages = 1,
  totalItems = 0,
  pageSize = 10,
  onPageChange,
  onPageSizeChange
}) => {
  if (totalPages <= 1 && !onPageSizeChange && totalItems === 0) return null;

  const startItem = totalItems > 0 ? Math.min((currentPage - 1) * pageSize + 1, totalItems) : 0;
  const endItem = totalItems > 0 ? Math.min(currentPage * pageSize, totalItems) : 0;

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 my-6 p-4 amz-card">
      <div className="flex items-center gap-3 text-xs text-amazon-text-secondary font-medium">
        {totalItems > 0 && (
          <span>
            Showing <strong className="text-amazon-text-primary">{startItem}</strong> to <strong className="text-amazon-text-primary">{endItem}</strong> of <strong className="text-amazon-text-primary">{totalItems}</strong> items
          </span>
        )}
        {onPageSizeChange && (
          <div className="flex items-center gap-2 ml-2">
            <span>Show:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="bg-white border border-[#D5D9D9] text-amazon-text-primary text-xs rounded-lg px-2 py-1 focus:outline-none focus:border-amazon-link-teal focus:shadow-sm"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="p-2 rounded-lg border border-[#D5D9D9] bg-white text-amazon-text-primary hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
          title="Previous Page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <span className="px-3.5 py-1.5 text-xs text-amazon-text-primary font-medium bg-slate-50 rounded-lg border border-[#D5D9D9]">
          Page {currentPage} of {Math.max(1, totalPages)}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="p-2 rounded-lg border border-[#D5D9D9] bg-white text-amazon-text-primary hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
          title="Next Page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const Badge = ({ status = 'pending', text }) => {
  const s = (status || '').toLowerCase();
  let color = 'bg-slate-100 text-slate-700 border-[#D5D9D9]';

  if (['completed', 'paid', 'active', 'delivered', 'approved', 'processed'].includes(s)) {
    color = 'bg-[#E7F4E4] text-amazon-stock-green border-[#007600]/30';
  } else if (['pending', 'created', 'processing', 'reserved', 'unpaid'].includes(s)) {
    color = 'bg-[#FFF8E7] text-amazon-cta-secondary border-[#FFA41C]/50';
  } else if (['failed', 'cancelled', 'expired', 'rejected', 'out_of_stock'].includes(s)) {
    color = 'bg-[#FDF2F5] text-amazon-deal-red border-[#CC0C39]/30';
  } else if (['shipped', 'in_transit'].includes(s)) {
    color = 'bg-[#EAF3FE] text-amazon-prime-blue border-[#00A8E1]/30';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${color} capitalize`}>
      {text || status}
    </span>
  );
};

export const StarRating = ({ rating = 5, max = 5, onRatingChange, interactive = false, size = 'w-4 h-4' }) => {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: max }).map((_, i) => {
        const starValue = i + 1;
        const isFilled = starValue <= rating;
        return (
          <button
            key={i}
            type={interactive ? 'button' : undefined}
            disabled={!interactive}
            onClick={() => interactive && onRatingChange && onRatingChange(starValue)}
            className={`${interactive ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-transform`}
          >
            <Star
              className={`${size} ${isFilled ? 'text-amazon-orange fill-amazon-orange' : 'text-slate-300 fill-slate-300'}`}
            />
          </button>
        );
      })}
    </div>
  );
};
