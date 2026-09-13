import React, { useState, useEffect, useCallback } from 'react';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ControlPanel, DataTable, EmptyState, LoadingSkeleton, Modal } from '../components/common/UIComponents';
import { usePagination } from '../hooks/usePagination';
import { History, ShieldCheck, ShieldAlert, Eye, UserCheck } from 'lucide-react';
import { ActivityLogBadge, ActivityLogDetails } from '../components/ActivityLogFormatter';

export const ActivityLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [resourceType, setResourceType] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const { showError } = useToast();
  const pagination = usePagination({ initialPage: 1, initialPageSize: 10 });

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
      };
      if (search) params.search = search;
      if (resourceType) params.resource_type = resourceType;
      if (statusFilter) params.status = statusFilter;

      const res = await authService.getActivityLogs(params);
      const data = res.data;

      if (Array.isArray(data)) {
        setLogs(data);
        pagination.updatePaginationState({ count: data.length, total_pages: 1, current_page: 1 });
      } else {
        setLogs(data?.results || []);
        pagination.updatePaginationState(data);
      }
    } catch (err) {
      showError(getErrorMessage(err));
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, search, resourceType, statusFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const columns = [
    {
      header: 'Log ID',
      accessor: 'id',
      render: (row) => <span className="font-mono text-xs text-[#94a3b8]">#{String(row.id).slice(0, 8)}</span>
    },
    {
      header: 'Actor',
      accessor: 'actor_email',
      render: (row) => (
        <div className="flex flex-col">
          <span className="font-semibold text-white text-xs flex items-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5 text-[#00a09d]" />
            {row.actor_email || row.user_id || 'System'}
          </span>
          {row.actor_role && (
            <span className="text-[10px] text-[#94a3b8] font-mono uppercase">
              {row.actor_role}
            </span>
          )}
        </div>
      )
    },
    {
      header: 'Action',
      accessor: 'action',
      render: (row) => <ActivityLogBadge action={row.action} />
    },
    {
      header: 'Resource',
      accessor: 'resource_type',
      render: (row) => row.resource_type ? (
        <span className="px-2 py-0.5 rounded bg-[#0f172a] border border-[#2d3748] text-slate-300 font-mono text-xs">
          {row.resource_type} {row.resource_id ? `#${row.resource_id.slice(0, 6)}` : ''}
        </span>
      ) : (
        <span className="text-slate-500">-</span>
      )
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => row.status === 'FAILED' ? (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
          <ShieldAlert className="w-3 h-3" /> FAILED
        </span>
      ) : (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-[#48bb78]/20 text-[#48bb78] border border-[#48bb78]/30">
          <ShieldCheck className="w-3 h-3" /> SUCCESS
        </span>
      )
    },
    {
      header: 'Timestamp',
      accessor: 'timestamp',
      render: (row) => <span className="text-xs text-[#94a3b8] font-mono">{new Date(row.timestamp || Date.now()).toLocaleString()}</span>
    },
    {
      header: 'Details',
      accessor: 'details',
      align: 'right',
      render: (row) => (
        <button
          onClick={() => setSelectedLog(row)}
          className="p-1.5 rounded bg-white/5 hover:bg-white/15 text-slate-300 hover:text-white transition-colors"
          title="View Full Context"
        >
          <Eye className="w-3.5 h-3.5" />
        </button>
      )
    }
  ];

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Audit Logs & System Trail"
        subtitle="Role-aware system audit trail recording API actions, authentication, and operations"
        breadcrumbs={['System', 'Audit Logs']}
        searchValue={search}
        onSearchChange={(e) => {
          setSearch(e.target.value);
          pagination.resetPage();
        }}
        searchPlaceholder="Search action, actor, resource..."
        customFilters={
          <div className="flex items-center gap-2">
            <select
              value={resourceType}
              onChange={(e) => {
                setResourceType(e.target.value);
                pagination.resetPage();
              }}
              className="bg-[#1f293d] border border-[#3b4b68] text-white text-xs rounded px-3 py-1.5 focus:outline-none"
            >
              <option value="">All Resource Types</option>
              <option value="PRODUCT">PRODUCT</option>
              <option value="ORDER">ORDER</option>
              <option value="TENANT">TENANT</option>
              <option value="USER_PROFILE">USER_PROFILE</option>
              <option value="AUTH">AUTH</option>
            </select>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                pagination.resetPage();
              }}
              className="bg-[#1f293d] border border-[#3b4b68] text-white text-xs rounded px-3 py-1.5 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>
        }
        pagination={pagination}
      />

      <div className="px-4 md:px-6">
        {loading ? (
          <LoadingSkeleton count={4} type="table" />
        ) : logs.length === 0 ? (
          <EmptyState
            icon={History}
            title="No audit log records"
            description="System operations and user activities will be indexed here in real-time."
          />
        ) : (
          <DataTable
            columns={columns}
            data={logs}
            keyField="id"
            pagination={pagination}
          />
        )}
      </div>

      {/* Log Detail Drawer Modal */}
      {selectedLog && (
        <Modal
          isOpen={!!selectedLog}
          onClose={() => setSelectedLog(null)}
          title={`Audit Log Detail #${String(selectedLog.id).slice(0, 8)}`}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4 text-xs text-slate-300">
            <div className="grid grid-cols-2 gap-3 p-3 rounded bg-[#0f172a] border border-[#2d3748]">
              <div>
                <span className="text-[#94a3b8] block mb-0.5">Action</span>
                <strong className="text-white font-mono">{selectedLog.action}</strong>
              </div>
              <div>
                <span className="text-[#94a3b8] block mb-0.5">Actor</span>
                <strong className="text-white">{selectedLog.actor_email || selectedLog.actor_id}</strong>
              </div>
              <div>
                <span className="text-[#94a3b8] block mb-0.5">IP Address</span>
                <span className="font-mono text-slate-200">{selectedLog.ip_address || 'Internal'}</span>
              </div>
              <div>
                <span className="text-[#94a3b8] block mb-0.5">Timestamp</span>
                <span className="font-mono">{new Date(selectedLog.timestamp).toLocaleString()}</span>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider mb-2">Metadata Details</h4>
              <ActivityLogDetails details={selectedLog.details} />
            </div>

            {selectedLog.changes && Object.keys(selectedLog.changes).length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-[#94a3b8] uppercase tracking-wider mb-2">State Changes</h4>
                <pre className="p-3 rounded bg-[#0b0f19] text-xs font-mono text-[#00a09d] overflow-x-auto border border-[#2d3748]">
                  {JSON.stringify(selectedLog.changes, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
};

