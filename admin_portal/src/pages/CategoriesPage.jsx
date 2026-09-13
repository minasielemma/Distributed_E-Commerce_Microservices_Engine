import React, { useState, useEffect, useMemo } from 'react';
import { catalogService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ControlPanel, DataTable, Modal, ConfirmDialog, EmptyState, LoadingSkeleton, Pagination } from '../components/common/UIComponents';
import { 
  Layers, Plus, Edit2, Trash2, Tag, Search, Filter, 
  FolderTree, Folder, CornerDownRight, ChevronRight, ChevronDown, Box, RefreshCw, LayoutList, LayoutGrid, CheckCircle2 
} from 'lucide-react';

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'grid'
  const [expandedParents, setExpandedParents] = useState(new Set());

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  const [modalOpen, setModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const { showSuccess, showError } = useToast();

  // Search and Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all'); // 'all', 'main', 'sub'
  const [parentFilter, setParentFilter] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parent: '',
    variant_attributes: [],
  });
  const [newPresetName, setNewPresetName] = useState('');
  const [newPresetValues, setNewPresetValues] = useState('');

  const fetchCategories = async () => {
    setLoading(true);
    try {
      const res = await catalogService.getCategories({ is_main: true });
      const mainCats = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setCategories(mainCats);

      const initialExpanded = new Set();
      mainCats.forEach((c) => {
        if (c.subcategories && c.subcategories.length > 0) {
          initialExpanded.add(c.id);
        }
      });
      setExpandedParents(initialExpanded);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  // Reset to page 1 on filter/search change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, filterType, parentFilter]);

  // Main categories (top-level)
  const mainCategories = useMemo(() => {
    return categories.filter((c) => !c.parent);
  }, [categories]);

  // All subcategories flattened
  const allSubcategories = useMemo(() => {
    const subs = [];
    categories.forEach((main) => {
      if (main.subcategories && main.subcategories.length > 0) {
        main.subcategories.forEach((sub) => {
          subs.push({
            ...sub,
            parent_name: main.name,
          });
        });
      }
    });
    return subs;
  }, [categories]);

  // Table flat row representation (Main categories + subcategory child rows)
  const tableRows = useMemo(() => {
    const rows = [];
    mainCategories.forEach((main) => {
      const mainMatchesParent = !parentFilter || main.id === parentFilter;
      const mainMatchesSearch = !searchQuery.trim() || 
        main.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
        main.slug?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const subs = main.subcategories || [];

      if (filterType === 'all' || filterType === 'main') {
        if (mainMatchesParent && mainMatchesSearch) {
          rows.push({ ...main, is_sub: false, parent_name: '-' });
        }
      }

      if (filterType === 'all' || filterType === 'sub') {
        subs.forEach((sub) => {
          const subMatchesParent = !parentFilter || sub.parent === parentFilter;
          const subMatchesSearch = !searchQuery.trim() || 
            sub.name?.toLowerCase().includes(searchQuery.toLowerCase()) || 
            sub.slug?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            main.name?.toLowerCase().includes(searchQuery.toLowerCase());

          if (subMatchesParent && subMatchesSearch) {
            rows.push({
              ...sub,
              is_sub: true,
              parent_name: main.name,
            });
          }
        });
      }
    });
    return rows;
  }, [mainCategories, filterType, parentFilter, searchQuery]);

  // Pagination calculation
  const totalPages = Math.ceil(tableRows.length / pageSize) || 1;
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return tableRows.slice(start, start + pageSize);
  }, [tableRows, currentPage, pageSize]);

  const handleOpenModal = (cat = null, defaultParentId = '') => {
    setNewPresetName('');
    setNewPresetValues('');
    if (cat) {
      setEditingCategory(cat);
      setFormData({
        name: cat.name || '',
        description: cat.description || '',
        parent: cat.parent || '',
        variant_attributes: Array.isArray(cat.variant_attributes) ? cat.variant_attributes : [],
      });
    } else {
      setEditingCategory(null);
      setFormData({
        name: '',
        description: '',
        parent: defaultParentId || '',
        variant_attributes: [],
      });
    }
    setModalOpen(true);
  };

  const handleAddPreset = (e) => {
    e.preventDefault();
    if (!newPresetName.trim()) return;
    const values = newPresetValues.split(',').map((v) => v.trim()).filter(Boolean);
    const updated = [...(formData.variant_attributes || []), { name: newPresetName.trim(), values }];
    setFormData({ ...formData, variant_attributes: updated });
    setNewPresetName('');
    setNewPresetValues('');
  };

  const handleRemovePreset = (index) => {
    const updated = (formData.variant_attributes || []).filter((_, i) => i !== index);
    setFormData({ ...formData, variant_attributes: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: formData.name,
        description: formData.description,
        parent: formData.parent || null,
        variant_attributes: formData.variant_attributes || [],
      };

      if (editingCategory) {
        await catalogService.updateCategory(editingCategory.id, payload);
        showSuccess('Category updated successfully');
      } else {
        await catalogService.createCategory(payload);
        showSuccess(
          payload.parent
            ? `Subcategory "${formData.name}" created!`
            : `Main Category "${formData.name}" created!`
        );
      }

      if (payload.parent) {
        setExpandedParents((prev) => new Set([...prev, payload.parent]));
      }

      setModalOpen(false);
      fetchCategories();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await catalogService.deleteCategory(deleteId);
      showSuccess('Category deleted');
      fetchCategories();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteId(null);
    }
  };

  if (loading) {
    return (
      <div className="w-full p-6 md:p-8 space-y-6">
        <h1 className="text-3xl font-extrabold text-white">Categories & Taxonomy</h1>
        <LoadingSkeleton count={4} type="table" />
      </div>
    );
  }

  return (
    <div className="w-full pb-12">
      <ControlPanel
        title="Global Categories & Taxonomies"
        subtitle={`${tableRows.length} Categories Total`}
        primaryAction={{
          label: 'Add Category',
          icon: Plus,
          onClick: () => handleOpenModal()
        }}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search categories by name, slug, parent..."
        filterOptions={[
          { label: 'All Levels', value: 'all' },
          { label: 'Main Categories Only', value: 'main' },
          { label: 'Subcategories Only', value: 'sub' },
        ]}
        activeFilter={filterType}
        onFilterChange={setFilterType}
        viewMode={viewMode === 'grid' ? 'kanban' : 'list'}
        onViewModeChange={(m) => setViewMode(m === 'kanban' ? 'grid' : 'table')}
        pagination={{
          currentPage: currentPage,
          totalPages: totalPages,
          totalItems: tableRows.length,
          pageSize: pageSize,
          onPageChange: setCurrentPage
        }}
        onRefresh={fetchCategories}
      />

      <div className="p-4 md:p-8 space-y-6">
        {/* Parent Group Filter Bar */}
        <div className="app-card p-4 flex flex-wrap items-center justify-between gap-4 border border-slate-800">
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-purple-400" />
            <span className="text-xs font-bold text-slate-400">Parent Group Filter:</span>
            <select
              value={parentFilter}
              onChange={(e) => setParentFilter(e.target.value)}
              className="app-input py-1.5 text-xs font-medium"
            >
              <option value="">All Parent Groups</option>
              {mainCategories.map((main) => (
                <option key={main.id} value={main.id}>
                  📁 {main.name} ({main.subcategories_count || main.subcategories?.length || 0} sub)
                </option>
              ))}
            </select>
          </div>

          {parentFilter && (
            <button
              onClick={() => setParentFilter('')}
              className="text-xs font-semibold text-rose-400 hover:underline"
            >
              Clear Parent Filter
            </button>
          )}
        </div>

        {/* DATA TABLE VIEW WITH PAGINATION */}
        {viewMode === 'table' && (
          <div>
            <DataTable
              headers={['Category Name', 'Level / Type', 'Parent Group', 'Subcategories', 'Preset Attributes', { label: 'Actions', className: 'text-right' }]}
              isEmpty={tableRows.length === 0}
              emptyStateProps={{
                icon: Layers,
                title: 'No categories found',
                description: 'No matching categories found for your search or filter settings.'
              }}
            >
              {paginatedRows.map((row) => (
                      <tr
                        key={row.id}
                        className={`hover:bg-white/[0.04] transition-colors ${
                          row.is_sub ? 'bg-slate-950/40' : 'bg-transparent font-medium'
                        }`}
                      >
                        {/* Name with indentation for subcategories */}
                        <td className="py-3.5 px-6">
                          <div className="flex items-center gap-2">
                            {row.is_sub ? (
                              <span className="pl-6 text-cyan-400 font-semibold flex items-center gap-1.5">
                                <CornerDownRight size={14} className="text-cyan-400 shrink-0" />
                                <span className="text-white font-bold">{row.name}</span>
                              </span>
                            ) : (
                              <span className="font-extrabold text-white flex items-center gap-2 text-base">
                                <Folder size={18} className="text-indigo-400 shrink-0" />
                                <span>{row.name}</span>
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Level / Type Badge */}
                        <td className="py-3.5 px-4">
                          {row.is_sub ? (
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                              Subcategory
                            </span>
                          ) : (
                            <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                              Main Category
                            </span>
                          )}
                        </td>

                        {/* Parent Group */}
                        <td className="py-3.5 px-4 text-xs font-semibold">
                          {row.is_sub ? (
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800/80 text-indigo-300 border border-white/10">
                              📁 {row.parent_name}
                            </span>
                          ) : (
                            <span className="text-slate-500 italic">None (Root)</span>
                          )}
                        </td>

                        {/* Subcategories count */}
                        <td className="py-3.5 px-4 text-xs">
                          {!row.is_sub ? (
                            <span className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-bold">
                              {row.subcategories?.length || row.subcategories_count || 0} subs
                            </span>
                          ) : (
                            <span className="text-slate-600">-</span>
                          )}
                        </td>

                        {/* Products count */}
                        <td className="py-3.5 px-4 text-xs">
                          <span className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-300 border border-purple-500/20 font-bold">
                            {row.products_count || 0} items
                          </span>
                        </td>

                        {/* Slug */}
                        <td className="py-3.5 px-4 font-mono text-xs text-slate-400">
                          {row.slug}
                        </td>

                        {/* Action buttons */}
                        <td className="py-3.5 px-6 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {!row.is_sub && (
                              <button
                                onClick={() => handleOpenModal(null, row.id)}
                                className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 border border-cyan-500/30 text-xs font-bold flex items-center gap-1 transition-colors"
                                title="Add Subcategory"
                              >
                                <Plus size={12} /> Add Sub
                              </button>
                            )}
                            <button
                              onClick={() => handleOpenModal(row)}
                              className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white hover:bg-white/10 text-xs transition-colors"
                              title="Edit Category"
                            >
                              <Edit2 size={14} />
                            </button>
                            <button
                              onClick={() => setDeleteId(row.id)}
                              className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-rose-400 hover:bg-white/10 text-xs transition-colors"
                              title="Delete Category"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
            </DataTable>

            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={tableRows.length}
              pageSize={pageSize}
              onPageChange={(page) => setCurrentPage(page)}
            />
          </div>
        )}

      {/* CARD GRID VIEW WITH PAGINATION */}
      {viewMode === 'grid' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedRows.map((row) => (
              <div key={row.id} className="glass-panel p-6 flex flex-col justify-between space-y-4 border border-white/10 hover:border-indigo-500/40 transition-all group">
                <div>
                  <div className="flex items-center justify-between">
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                      row.is_sub ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30' : 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/30'
                    }`}>
                      {row.is_sub ? 'Subcategory' : 'Main Category'}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">slug: {row.slug}</span>
                  </div>

                  <h3 className="text-xl font-bold text-white mt-2 group-hover:text-indigo-300 transition-colors flex items-center gap-2">
                    {row.is_sub ? <CornerDownRight size={18} className="text-cyan-400" /> : <Folder size={18} className="text-indigo-400" />}
                    <span>{row.name}</span>
                  </h3>

                  {row.is_sub && (
                    <div className="mt-2 text-xs text-slate-400">
                      Parent Category: <strong className="text-indigo-300">{row.parent_name}</strong>
                    </div>
                  )}

                  <p className="text-slate-400 text-xs mt-2 line-clamp-2">{row.description || 'No description provided.'}</p>

                  <div className="flex items-center gap-3 mt-3 pt-3 border-t border-white/10 text-xs font-semibold">
                    {!row.is_sub && (
                      <span className="px-2.5 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {row.subcategories?.length || 0} Subcategories
                      </span>
                    )}
                    <span className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-300 border border-purple-500/20">
                      {row.products_count || 0} Products
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-4 border-t border-white/10">
                  {!row.is_sub && (
                    <button
                      onClick={() => handleOpenModal(null, row.id)}
                      className="px-2 py-1 rounded-xl bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 border border-cyan-500/30 text-xs font-bold flex items-center gap-1"
                    >
                      <Plus size={12} /> Add Sub
                    </button>
                  )}
                  <button
                    onClick={() => handleOpenModal(row)}
                    className="p-2 rounded-xl bg-white/5 text-slate-300 hover:text-white hover:bg-white/10 text-xs flex items-center gap-1"
                  >
                    <Edit2 size={14} /> Edit
                  </button>
                  <button
                    onClick={() => setDeleteId(row.id)}
                    className="p-2 rounded-xl bg-white/5 text-slate-400 hover:text-rose-400 hover:bg-white/10 text-xs"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={(page) => setCurrentPage(page)}
          />
        </div>
      )}
      </div>

      {/* Modal Form */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingCategory ? 'Edit Category' : 'Create Category'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Category Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Electronics, Smart Phones, Apparel"
              required
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Parent Category (Taxonomy Level)</label>
            <select
              value={formData.parent}
              onChange={(e) => setFormData({ ...formData, parent: e.target.value })}
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">-- None (Top-Level / Main Category) --</option>
              {mainCategories
                .filter((c) => !editingCategory || c.id !== editingCategory.id)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    📁 {c.name} (Main Category)
                  </option>
                ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1">
              Select a Main Category to create a Subcategory under it, or leave empty to create a Main Category.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
            <textarea
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Category overview and marketing summary..."
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-indigo-500 text-xs"
            />
          </div>

          {/* Variant Attributes Presets Builder */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-white/10 space-y-3">
            <label className="block text-xs font-bold text-indigo-300 uppercase tracking-wider">
              Category Variant Attribute Presets (JSON Schema)
            </label>
            <p className="text-[11px] text-slate-400">
              Define preset attributes (e.g. Color, Size) for products created in this category.
            </p>

            {formData.variant_attributes && formData.variant_attributes.length > 0 && (
              <div className="space-y-2">
                {formData.variant_attributes.map((attr, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900 border border-white/10 text-xs">
                    <div>
                      <strong className="text-white font-bold">{attr.name}:</strong>{' '}
                      <span className="text-indigo-300">{Array.isArray(attr.values) ? attr.values.join(', ') : ''}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemovePreset(idx)}
                      className="text-rose-400 hover:text-rose-300 p-1"
                      title="Remove Preset"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="pt-2 border-t border-white/10 grid grid-cols-1 sm:grid-cols-12 gap-2 text-xs">
              <div className="sm:col-span-5">
                <input
                  type="text"
                  placeholder="Attribute (e.g. Color, Size)"
                  value={newPresetName}
                  onChange={(e) => setNewPresetName(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs"
                />
              </div>
              <div className="sm:col-span-5">
                <input
                  type="text"
                  placeholder="Values (comma-separated: Red, Blue, Green)"
                  value={newPresetValues}
                  onChange={(e) => setNewPresetValues(e.target.value)}
                  className="w-full bg-slate-900 border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs"
                />
              </div>
              <div className="sm:col-span-2">
                <button
                  type="button"
                  onClick={handleAddPreset}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-1.5 px-2 rounded-lg text-xs"
                >
                  + Add
                </button>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setModalOpen(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 hover:bg-white/10">
              Cancel
            </button>
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl">
              {editingCategory ? 'Save Changes' : 'Create Category'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Category"
        message="Are you sure you want to delete this category? Any linked items will be unassigned."
      />
    </div>
  );
}
