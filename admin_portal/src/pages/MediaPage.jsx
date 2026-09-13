import React, { useState, useEffect, useCallback } from 'react';
import { mediaService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { usePagination } from '../hooks/usePagination';
import { ControlPanel, FormSheet, ConfirmDialog, EmptyState, LoadingSkeleton } from '../components/common/UIComponents';
import { Image as ImageIcon, Upload, Download, Share2, Trash2, FileText, Lock, Globe } from 'lucide-react';

export default function MediaPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [shareFileItem, setShareFileItem] = useState(null);
  const { showSuccess, showError } = useToast();

  const pagination = usePagination({ initialPageSize: 12 });
  const { page, pageSize, updatePaginationState, handlePageChange, handlePageSizeChange } = pagination;

  const [visibility, setVisibility] = useState('PUBLIC');
  const [shareData, setShareData] = useState({
    visibility: 'SHARED',
    shared_with_users: '',
    shared_with_tenants: '',
  });

  const fetchFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await mediaService.getFiles({ page, page_size: pageSize });
      const resData = res?.data;
      const list = Array.isArray(resData) ? resData : (resData?.results || []);
      setFiles(list);
      updatePaginationState(resData);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, updatePaginationState, showError]);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('visibility', visibility);

    setUploading(true);
    try {
      await mediaService.uploadFile(formData);
      showSuccess(`File "${selectedFile.name}" uploaded successfully!`);
      fetchFiles();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDownload = async (fileItem) => {
    try {
      const res = await mediaService.downloadFile(fileItem.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileItem.original_name || fileItem.filename || `file-${fileItem.id}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      showSuccess('Download started!');
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await mediaService.deleteFile(deleteId);
      showSuccess('Media file deleted');
      fetchFiles();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteId(null);
    }
  };

  const handleShareSubmit = async (e) => {
    e.preventDefault();
    if (!shareFileItem) return;
    try {
      const payload = {
        visibility: shareData.visibility,
        shared_with_users: shareData.shared_with_users ? shareData.shared_with_users.split(',').map((s) => s.trim()) : [],
        shared_with_tenants: shareData.shared_with_tenants ? shareData.shared_with_tenants.split(',').map((s) => s.trim()) : [],
      };
      await mediaService.shareFile(shareFileItem.id, payload);
      showSuccess('ACL Sharing updated!');
      setShareFileItem(null);
      fetchFiles();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  return (
    <div className="w-full space-y-4">
      <ControlPanel
        title="Documents & Media"
        subtitle="Manage product photos, catalog assets, and document access ACLs"
        breadcrumbs={['Documents', 'Library']}
        customActions={
          <div className="flex items-center gap-2">
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
              className="bg-[#1f293d] border border-[#3b4b68] rounded px-3 py-1.5 text-xs text-[#e2e8f0] focus:outline-none focus:border-[#7c7bad]"
            >
              <option value="PUBLIC">Public Upload</option>
              <option value="PRIVATE">Private Upload</option>
              <option value="SHARED">Shared ACL</option>
            </select>

            <label className="app-btn-teal inline-flex items-center gap-1.5 cursor-pointer text-xs">
              <Upload className="w-3.5 h-3.5" />
              <span>{uploading ? 'Uploading...' : 'Upload File'}</span>
              <input type="file" onChange={handleFileUpload} disabled={uploading} className="hidden" />
            </label>
          </div>
        }
        pagination={pagination}
      />

      <div className="px-4 md:px-6">
        {loading ? (
          <LoadingSkeleton count={4} type="cards" />
        ) : files.length === 0 ? (
          <EmptyState
            icon={ImageIcon}
            title="No media files stored"
            description="Upload product photos, catalog assets, or documents to the shared media microservice."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {files.map((file) => {
              const isImage = (file.file_type || '').toUpperCase() === 'IMAGE' || (file.content_type || '').toLowerCase().startsWith('image/') || (file.file_url || file.url || '').match(/\.(jpg|jpeg|png|webp|gif|svg)$/i);
              const fileUrl = file.file_url || file.url || file.file || `/api/media/files/${file.id}/download/`;

              return (
                <div key={file.id} className="app-card p-3 flex flex-col justify-between space-y-3 hover:border-[#7c7bad] transition-all">
                  <div className="h-32 rounded bg-[#0f172a] border border-[#2d3748] overflow-hidden flex items-center justify-center relative">
                    {isImage ? (
                      <img 
                        src={fileUrl} 
                        alt={file.original_filename || file.original_name || 'Media'} 
                        className="w-full h-full object-cover" 
                        onError={(e) => {
                          e.target.style.display = 'none';
                          if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                    ) : (
                      <FileText className="w-10 h-10 text-[#7c7bad]/60" />
                    )}
                    <span className="absolute top-2 left-2 px-2 py-0.5 rounded text-[10px] font-bold bg-black/80 text-slate-300 uppercase flex items-center gap-1">
                      {(file.visibility || '').toUpperCase() === 'PUBLIC' ? <Globe className="w-3 h-3 text-emerald-400" /> : <Lock className="w-3 h-3 text-amber-400" />}
                      {file.visibility || 'PUBLIC'}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-bold text-white text-xs line-clamp-1">{file.original_name || file.filename || `File #${file.id}`}</h4>
                    <p className="text-[11px] text-[#94a3b8] mt-0.5 font-mono">
                      {file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : 'Media file'}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-[#2d3748] text-xs">
                    <button onClick={() => handleDownload(file)} className="p-1.5 rounded bg-white/5 text-[#e2e8f0] hover:text-white hover:bg-white/10" title="Download">
                      <Download className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => { setShareFileItem(file); setShareData({ visibility: file.visibility || 'SHARED', shared_with_users: '', shared_with_tenants: '' }); }} className="p-1.5 rounded bg-white/5 text-[#e2e8f0] hover:text-white hover:bg-white/10" title="Manage ACL">
                      <Share2 className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => setDeleteId(file.id)} className="p-1.5 rounded bg-white/5 text-[#94a3b8] hover:text-rose-400 hover:bg-white/10" title="Delete">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Share ACL Modal */}
      {shareFileItem && (
        <FormSheet
          isOpen={!!shareFileItem}
          onClose={() => setShareFileItem(null)}
          title={`File Access Control ACL #${shareFileItem.id}`}
          subtitle="Configure visibility and shared tenants/users"
          onSave={handleShareSubmit}
          saveLabel="Update ACL"
        >
          <form onSubmit={handleShareSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Visibility Level</label>
              <select
                value={shareData.visibility}
                onChange={(e) => setShareData({ ...shareData, visibility: e.target.value })}
                className="app-input"
              >
                <option value="PUBLIC">Public (Everyone)</option>
                <option value="PRIVATE">Private (Owner Only)</option>
                <option value="SHARED">Shared (ACL Users/Tenants)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Shared User IDs (Comma-separated)</label>
              <input
                type="text"
                placeholder="user1, user2, user3"
                value={shareData.shared_with_users}
                onChange={(e) => setShareData({ ...shareData, shared_with_users: e.target.value })}
                className="app-input font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">Shared Tenant IDs (Comma-separated)</label>
              <input
                type="text"
                placeholder="tenant-1, tenant-2"
                value={shareData.shared_with_tenants}
                onChange={(e) => setShareData({ ...shareData, shared_with_tenants: e.target.value })}
                className="app-input font-mono"
              />
            </div>
          </form>
        </FormSheet>
      )}

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Media File"
        message="Are you sure you want to permanently delete this media file?"
      />
    </div>
  );
}

