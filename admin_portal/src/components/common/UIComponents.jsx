import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, ChevronLeft, ChevronRight, Inbox, Upload, Search, Filter, LayoutList, LayoutGrid, CheckCircle, RefreshCw } from 'lucide-react';
import { mediaService } from '../../services/apiServices';
import { getErrorMessage } from '../../services/api';
import { Breadcrumbs } from './Breadcrumbs';

export const ControlPanel = ({
  title,
  subtitle,
  breadcrumbs,
  primaryAction,
  secondaryActions = [],
  searchQuery,
  searchValue,
  onSearchChange,
  searchPlaceholder = 'Search...',
  filterOptions = [],
  activeFilter,
  onFilterChange,
  customFilters,
  viewMode,
  onViewModeChange,
  pagination,
  onRefresh
}) => {
  const currentSearch = searchQuery !== undefined ? searchQuery : (searchValue !== undefined ? searchValue : '');

  const curPage = pagination?.page ?? pagination?.currentPage ?? 1;
  const pSize = pagination?.pageSize ?? pagination?.page_size ?? 10;
  const total = pagination?.totalItems ?? pagination?.total_items ?? 0;
  const totPages = pagination?.totalPages ?? pagination?.total_pages ?? (pSize > 0 ? Math.ceil(total / pSize) : 1);
  const onPageChg = pagination?.onPageChange || pagination?.handlePageChange;

  const startItem = total > 0 ? Math.min((curPage - 1) * pSize + 1, total) : 0;
  const endItem = total > 0 ? Math.min(curPage * pSize, total) : 0;

  const hasToolbar = onSearchChange !== undefined || customFilters || (filterOptions.length > 0) || (viewMode && onViewModeChange) || (pagination && total > 0);

  return (
    <div className="bg-[#111827] border-b border-slate-800/80 px-4 md:px-6 lg:px-8 py-4 sticky top-0 z-20 shadow-md mb-4">
      <div className="space-y-3">
        {/* Row 1: Breadcrumbs, Title, Subtitle, Primary & Secondary Action Buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <Breadcrumbs customCrumbs={breadcrumbs} activeTitle={title} />
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                {title}
              </h1>
              {subtitle && (
                <span className="text-xs text-slate-400 font-medium px-2.5 py-0.5 rounded-full bg-slate-800/80 border border-slate-700/60 hidden sm:inline-block">
                  {subtitle}
                </span>
              )}
            </div>
          </div>

          {(primaryAction || secondaryActions.length > 0 || onRefresh) && (
            <div className="flex flex-wrap items-center gap-2">
              {primaryAction && (
                <button
                  type="button"
                  onClick={primaryAction.onClick}
                  className="app-btn-primary"
                >
                  {primaryAction.icon && <primaryAction.icon size={14} />}
                  <span>{primaryAction.label}</span>
                </button>
              )}

              {secondaryActions.map((action, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={action.onClick}
                  className={action.isTeal ? 'app-btn-teal' : 'app-btn-secondary'}
                >
                  {action.icon && <action.icon size={14} />}
                  <span>{action.label}</span>
                </button>
              ))}

              {onRefresh && (
                <button
                  type="button"
                  onClick={onRefresh}
                  className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
                  title="Refresh Data"
                >
                  <RefreshCw size={14} />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Row 2: Search Input, Custom Filters, View Toggles, Compact Pagination */}
        {hasToolbar && (
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2.5 border-t border-slate-800/60">
            <div className="flex flex-wrap items-center gap-2.5 flex-1">
              {/* Search Box */}
              {onSearchChange !== undefined && (
                <div className="relative min-w-[200px] max-w-sm flex-1">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={currentSearch}
                    onChange={(e) => onSearchChange(e)}
                    placeholder={searchPlaceholder}
                    className="w-full app-input pl-9 pr-8 text-xs py-1.5"
                  />
                  {currentSearch && (
                    <button
                      onClick={() => onSearchChange({ target: { value: '' } })}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                    >
                      <X size={13} />
                    </button>
                  )}
                </div>
              )}

              {/* Custom Filters Slot */}
              {customFilters}

              {/* Filter Options */}
              {filterOptions.length > 0 && onFilterChange && (
                <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 p-1 rounded-lg">
                  <Filter size={13} className="text-slate-400 ml-1.5 shrink-0" />
                  <select
                    value={activeFilter || ''}
                    onChange={(e) => onFilterChange(e.target.value)}
                    className="bg-transparent text-xs font-semibold text-purple-300 focus:outline-none cursor-pointer pr-2"
                  >
                    {filterOptions.map((opt) => (
                      <option key={opt.value} value={opt.value} className="bg-slate-900 text-white">
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2.5">
              {/* View Toggles */}
              {viewMode && onViewModeChange && (
                <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1">
                  <button
                    type="button"
                    onClick={() => onViewModeChange('list')}
                    className={`p-1.5 rounded ${viewMode === 'list' ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40' : 'text-slate-400 hover:text-slate-200'}`}
                    title="List View"
                  >
                    <LayoutList size={14} />
                  </button>
                  <button
                    type="button"
                    onClick={() => onViewModeChange('kanban')}
                    className={`p-1.5 rounded ${viewMode === 'kanban' ? 'bg-purple-600/30 text-purple-300 border border-purple-500/40' : 'text-slate-400 hover:text-slate-200'}`}
                    title="Kanban View"
                  >
                    <LayoutGrid size={14} />
                  </button>
                </div>
              )}

              {/* Compact Pagination Header Summary */}
              {pagination && total > 0 && (
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-lg shrink-0 font-mono">
                  <span>
                    {startItem}-{endItem} / {total}
                  </span>
                  {onPageChg && (
                    <div className="flex items-center gap-1 border-l border-slate-700 pl-2">
                      <button
                        type="button"
                        onClick={() => onPageChg(curPage - 1)}
                        disabled={curPage <= 1}
                        className="p-0.5 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft size={14} />
                      </button>
                      <button
                        type="button"
                        onClick={() => onPageChg(curPage + 1)}
                        disabled={curPage >= totPages}
                        className="p-0.5 text-slate-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const DataTable = ({ 
  headers, 
  columns, 
  data = [], 
  keyField = 'id', 
  children, 
  isEmpty, 
  emptyStateProps 
}) => {
  const effectiveHeaders = headers || (columns ? columns.map(col => {
    if (typeof col === 'string') return col;
    return {
      label: col.header || col.label || col.name || '',
      className: col.align === 'right' ? 'text-right' : (col.className || '')
    };
  }) : []);

  const tableIsEmpty = isEmpty !== undefined ? isEmpty : (data && data.length === 0 && !children);

  return (
    <div className="app-card overflow-hidden my-4 border border-slate-800/80 shadow-xl">
      <div className="overflow-x-auto custom-scrollbar max-w-full">
        <table className="app-table min-w-full">
          <thead>
            <tr>
              {effectiveHeaders.map((h, i) => (
                <th key={i} className={typeof h === 'object' ? (h.className || (h.align === 'right' ? 'text-right' : '')) : ''}>
                  {typeof h === 'object' ? (h.label || h.header || '') : h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {children ? (
              children
            ) : columns && data ? (
              data.map((row, rowIdx) => (
                <tr key={row[keyField] ?? row.id ?? rowIdx} className="hover:bg-slate-800/40 transition-colors">
                  {columns.map((col, colIdx) => (
                    <td key={colIdx} className={col.align === 'right' ? 'text-right' : (col.cellClassName || '')}>
                      {col.render ? col.render(row) : row[col.accessor]}
                    </td>
                  ))}
                </tr>
              ))
            ) : null}
          </tbody>
        </table>
      </div>
      {tableIsEmpty && emptyStateProps && (
        <EmptyState {...emptyStateProps} />
      )}
    </div>
  );
};

export const FormSheet = ({ 
  isOpen, 
  onClose, 
  title, 
  subtitle, 
  statusPipeline = [], 
  activeStage, 
  children, 
  actions, 
  onSave, 
  saveLabel = 'Save Changes',
  maxWidth = 'max-w-4xl'
}) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && onClose) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (isOpen !== undefined && !isOpen) return null;

  const content = (
    <div className={`app-card p-4 sm:p-6 border border-slate-800 shadow-2xl ${maxWidth} w-full mx-auto flex flex-col max-h-[90vh] sm:max-h-[85vh] bg-slate-900/95 backdrop-blur-xl relative my-auto overflow-hidden`}>
      {/* Form Sheet Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 sm:pb-4 border-b border-slate-800 shrink-0">
        <div>
          <h2 className="text-lg sm:text-xl font-bold text-white tracking-wide">{title}</h2>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* Status Pipeline / Stages Bar */}
          {statusPipeline.length > 0 && (
            <div className="flex items-center gap-1 overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
              {statusPipeline.map((stage, idx) => {
                const isActive = stage.key === activeStage || stage.label === activeStage;
                return (
                  <div
                    key={idx}
                    className={`px-2.5 py-0.5 sm:px-3 sm:py-1 rounded-md text-[10px] sm:text-xs font-semibold uppercase tracking-wider flex items-center gap-1 sm:gap-1.5 transition-all whitespace-nowrap ${
                      isActive
                        ? 'bg-purple-600 text-white shadow'
                        : 'bg-slate-900 text-slate-400 border border-slate-800'
                    }`}
                  >
                    {isActive && <CheckCircle size={12} />}
                    <span>{stage.label || stage.key}</span>
                  </div>
                );
              })}
            </div>
          )}

          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors shrink-0 touch-target"
              title="Close (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar py-4 pr-1">{children}</div>

      {(actions || onSave || onClose) && (
        <div className="flex items-center justify-end gap-2.5 pt-3 sm:pt-4 border-t border-slate-800 shrink-0">
          {actions ? (
            actions
          ) : (
            <>
              {onClose && (
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs font-semibold transition-colors"
                >
                  Cancel
                </button>
              )}
              <button
                type="button"
                onClick={onSave}
                className="app-btn-primary text-xs font-bold px-5 py-2"
              >
                {saveLabel}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );

  if (isOpen !== undefined) {
    return (
      <div 
        className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md overflow-y-auto"
        onClick={(e) => {
          if (e.target === e.currentTarget && onClose) onClose();
        }}
      >
        {content}
      </div>
    );
  }

  return content;
};

export const Modal = ({ isOpen, onClose, title, children, maxWidth = 'max-w-2xl' }) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md overflow-y-auto"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className={`relative w-full ${maxWidth} app-card border border-slate-700/80 p-4 sm:p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200 my-auto max-h-[90vh] sm:max-h-[85vh] flex flex-col overflow-hidden`}>
        <div className="flex items-center justify-between pb-3 sm:pb-4 border-b border-slate-800 mb-4 shrink-0">
          <h3 className="text-base sm:text-lg font-extrabold text-white tracking-wide">{title}</h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors touch-target"
            title="Close (Esc)"
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
        <div className={`p-3 rounded-xl ${isDanger ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'}`}>
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div>
          <p className="text-slate-300 text-sm leading-relaxed">{message}</p>
        </div>
      </div>
      <div className="flex justify-end gap-3 mt-6">
        <button onClick={onClose} className="app-btn-secondary">Cancel</button>
        <button 
          onClick={onConfirm} 
          className={isDanger ? 'px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-lg text-xs shadow-md transition-all' : 'app-btn-primary'}
        >
          {confirmText}
        </button>
      </div>
    </Modal>
  );
};

export const EmptyState = ({ icon: Icon = Inbox, title = 'No data found', description = 'There are no items to display right now.', action }) => (
  <div className="p-12 text-center flex flex-col items-center justify-center my-4">
    <div className="p-4 rounded-2xl bg-purple-500/10 text-purple-400 mb-4 border border-purple-500/20 shadow-inner">
      <Icon className="w-10 h-10" />
    </div>
    <h3 className="text-base font-extrabold text-white mb-1">{title}</h3>
    <p className="text-slate-400 text-xs max-w-sm mb-6 leading-relaxed">{description}</p>
    {action && action}
  </div>
);

export const LoadingSkeleton = ({ count = 3, type = 'table' }) => {
  if (type === 'table') {
    return (
      <div className="app-card p-6 space-y-4 animate-pulse border border-slate-800">
        <div className="h-6 bg-slate-800 rounded w-1/4"></div>
        <div className="space-y-2">
          <div className="h-4 bg-slate-800/60 rounded"></div>
          <div className="h-4 bg-slate-800/60 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="app-card p-5 animate-pulse space-y-4 border border-slate-800">
          <div className="h-44 bg-slate-800/80 rounded-xl w-full"></div>
          <div className="h-5 bg-slate-800/80 rounded w-3/4"></div>
          <div className="h-4 bg-slate-800/50 rounded w-1/2"></div>
          <div className="h-8 bg-slate-800/80 rounded-xl w-full mt-4"></div>
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
    <div className="flex flex-wrap items-center justify-between gap-4 my-6 p-4 app-card border border-slate-800 rounded-xl">
      <div className="flex items-center gap-3 text-xs text-slate-400 font-medium">
        {totalItems > 0 && (
          <span>
            Showing <strong className="text-white">{startItem}</strong> to <strong className="text-white">{endItem}</strong> of <strong className="text-white">{totalItems}</strong> items
          </span>
        )}
        {onPageSizeChange && (
          <div className="flex items-center gap-2 ml-2">
            <span>Show:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="bg-slate-900 border border-slate-700 text-white text-xs rounded-md px-2 py-1 focus:outline-none focus:border-purple-500"
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
          className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title="Previous Page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <span className="px-3 py-1 text-xs text-slate-300 font-semibold bg-slate-800 rounded-lg border border-slate-700">
          Page {currentPage} of {Math.max(1, totalPages)}
        </span>

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          className="p-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
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
  let color = 'bg-slate-800 text-slate-300 border-slate-700';

  if (['completed', 'paid', 'active', 'delivered', 'approved', 'processed'].includes(s)) {
    color = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
  } else if (['pending', 'created', 'processing', 'reserved', 'unpaid', 'draft'].includes(s)) {
    color = 'bg-amber-500/20 text-amber-300 border-amber-500/40';
  } else if (['failed', 'cancelled', 'expired', 'rejected', 'out_of_stock'].includes(s)) {
    color = 'bg-rose-500/20 text-rose-300 border-rose-500/40';
  } else if (['shipped', 'in_transit'].includes(s)) {
    color = 'bg-blue-500/20 text-blue-300 border-blue-500/40';
  } else if (['platform', 'superadmin'].includes(s)) {
    color = 'bg-purple-500/20 text-purple-300 border-purple-500/40';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${color} capitalize tracking-wide`}>
      {text || status}
    </span>
  );
};

export const ImageUploader = ({ value, onChange, label = 'Image URL or Upload' }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('visibility', 'PUBLIC');

    setUploading(true);
    setError(null);

    try {
      const res = await mediaService.uploadFile(formData);
      const url = res.data?.file_url || res.data?.file || res.data?.url || (res.data?.file_id ? `/api/media/files/${res.data.file_id}/download/` : '');
      if (url) {
        onChange(url);
      } else {
        setError('Failed to extract uploaded file URL');
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">{label}</label>
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder="https://example.com/image.jpg"
          className="flex-1 app-input"
        />
        <label className="cursor-pointer bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-2 rounded-lg border border-slate-700 transition-colors inline-flex items-center gap-2 text-xs font-semibold shrink-0">
          <Upload className="w-4 h-4 text-purple-400" />
          <span>{uploading ? 'Uploading...' : 'Upload'}</span>
          <input type="file" onChange={handleFileUpload} accept="image/*" className="hidden" disabled={uploading} />
        </label>
      </div>
      {error && <p className="text-xs text-rose-400">{error}</p>}
      {value && (
        <div className="mt-2 relative w-20 h-20 rounded-lg overflow-hidden border border-slate-700 bg-slate-900 flex items-center justify-center shadow-inner">
          <img 
            src={value} 
            alt="Preview" 
            className="w-full h-full object-cover" 
            onError={(e) => { 
              e.target.onerror = null;
              e.target.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="%23818cf8" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>'; 
            }} 
          />
        </div>
      )}
    </div>
  );
};

