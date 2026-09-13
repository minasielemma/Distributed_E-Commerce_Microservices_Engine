import React, { useState, useEffect, useMemo } from 'react';
import { inventoryService, catalogService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ControlPanel, DataTable, Modal, ConfirmDialog, EmptyState, LoadingSkeleton, Pagination } from '../components/common/UIComponents';
import { 
  Boxes, Warehouse, Plus, Edit2, Trash2, ArrowRightLeft, 
  Search, RefreshCw, AlertTriangle, CheckCircle2, Package 
} from 'lucide-react';

export const InventoryPage = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [products, setProducts] = useState([]);
  const [items, setItems] = useState([]);
  const [movements, setMovements] = useState([]);
  const [activeTab, setActiveTab] = useState('inventory');
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);

  // Warehouse Modal
  const [showWhModal, setShowWhModal] = useState(false);
  const [editingWh, setEditingWh] = useState(null);
  const [whForm, setWhForm] = useState({ name: '', code: '', address: '' });
  const [deleteWhId, setDeleteWhId] = useState(null);

  // Inventory Item Modal
  const [showItemModal, setShowItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemForm, setItemForm] = useState({
    product_id: '',
    warehouse: '',
    quantity_available: 100,
    reorder_level: 10,
  });

  // Stock Action Modal (Reserve / Release / Commit / Add Stock)
  const [stockActionModal, setStockActionModal] = useState(false);
  const [stockActionType, setStockActionType] = useState('add');
  const [stockActionForm, setStockActionForm] = useState({
    product_id: '',
    quantity: 1,
    reference_id: `REF-${Date.now()}`,
  });
  const [actionLoading, setActionLoading] = useState(false);

  const { showSuccess, showError } = useToast();

  const fetchInventoryData = async () => {
    setLoading(true);
    try {
      const [whRes, itemRes, prodRes] = await Promise.all([
        inventoryService.getWarehouses().catch(() => ({ data: [] })),
        inventoryService.getInventoryItems().catch(() => ({ data: [] })),
        catalogService.getProducts({ all: 'true' }).catch(() => ({ data: [] })),
      ]);

      const whList = Array.isArray(whRes?.data) ? whRes.data : (whRes?.data?.results || []);
      setWarehouses(whList);

      const itemList = Array.isArray(itemRes?.data) ? itemRes.data : (itemRes?.data?.results || []);
      setItems(itemList);
      
      const prodList = Array.isArray(prodRes?.data) ? prodRes.data : (prodRes?.data?.results || []);
      setProducts(prodList);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventoryData();

    const handleRealtimeNotification = (e) => {
      const notif = e.detail;
      if (!notif) return;
      const notifType = (notif.notification_type || '').toUpperCase();
      if (notifType === 'INVENTORY' || notifType === 'STOCK' || notif.metadata?.product_id) {
        fetchInventoryData();
      }
    };

    window.addEventListener('notification_received', handleRealtimeNotification);
    return () => window.removeEventListener('notification_received', handleRealtimeNotification);
  }, []);

  useEffect(() => {
    if (activeTab === 'movements') {
      fetchMovements();
    }
  }, [activeTab]);

  const fetchMovements = async () => {
    try {
      const res = await inventoryService.getMovements();
      const movList = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setMovements(movList);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  // Merge products with inventory stock records
  const mergedStockItems = useMemo(() => {
    const itemMap = new Map();
    const safeItems = Array.isArray(items) ? items : [];
    safeItems.forEach((item) => {
      if (item && item.product_id) {
        itemMap.set(String(item.product_id), item);
      }
    });

    const search = searchTerm.trim().toLowerCase();
    const safeProducts = Array.isArray(products) ? products : [];

    return safeProducts.map((prod) => {
      const inv = itemMap.get(String(prod.id));
      return {
        product: prod,
        inventory_id: inv ? inv.id : null,
        warehouse: inv ? inv.warehouse : null,
        warehouse_name: inv ? (inv.warehouse_name || 'Main Warehouse') : 'Main Warehouse',
        quantity_available: inv ? inv.quantity_available : 0,
        quantity_reserved: inv ? inv.quantity_reserved : 0,
        reorder_level: inv ? inv.reorder_level : 10,
        has_record: !!inv,
      };
    }).filter((row) => {
      if (!search) return true;
      const nameMatch = row.product.name?.toLowerCase().includes(search);
      const skuMatch = row.product.sku?.toLowerCase().includes(search);
      const catMatch = row.product.category_name?.toLowerCase().includes(search);
      return nameMatch || skuMatch || catMatch;
    });
  }, [products, items, searchTerm]);

  // Pagination for merged items
  const PAGE_SIZE = 10;
  const totalPages = Math.ceil(mergedStockItems.length / PAGE_SIZE) || 1;
  const paginatedStockItems = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return mergedStockItems.slice(start, start + PAGE_SIZE);
  }, [mergedStockItems, currentPage]);

  const handleOpenWhModal = (wh = null) => {
    if (wh) {
      setEditingWh(wh);
      setWhForm({ name: wh.name || '', code: wh.code || '', address: wh.address || '' });
    } else {
      setEditingWh(null);
      setWhForm({ name: '', code: '', address: '' });
    }
    setShowWhModal(true);
  };

  const handleSaveWarehouse = async (e) => {
    e.preventDefault();
    try {
      if (editingWh) {
        await inventoryService.updateWarehouse(editingWh.id, whForm);
        showSuccess('Warehouse updated!');
      } else {
        await inventoryService.createWarehouse(whForm);
        showSuccess('Warehouse created!');
      }
      setShowWhModal(false);
      fetchInventoryData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDeleteWarehouse = async () => {
    if (!deleteWhId) return;
    try {
      await inventoryService.deleteWarehouse(deleteWhId);
      showSuccess('Warehouse deleted');
      fetchInventoryData();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteWhId(null);
    }
  };

  const handleOpenItemModal = (row = null) => {
    if (row) {
      setEditingItem(row);
      setItemForm({
        product_id: row.product.id,
        warehouse: row.warehouse || (warehouses[0]?.id || ''),
        quantity_available: row.quantity_available,
        reorder_level: row.reorder_level,
      });
    } else {
      setEditingItem(null);
      setItemForm({
        product_id: products[0]?.id || '',
        warehouse: warehouses[0]?.id || '',
        quantity_available: 100,
        reorder_level: 10,
      });
    }
    setShowItemModal(true);
  };

  const handleSaveInventoryItem = async (e) => {
    e.preventDefault();
    if (!itemForm.product_id) {
      showError('Please select a product');
      return;
    }

    try {
      await inventoryService.initProductInventory({
        product_id: itemForm.product_id,
        warehouse: itemForm.warehouse || null,
        quantity_available: Number(itemForm.quantity_available),
        reorder_level: Number(itemForm.reorder_level),
      });
      showSuccess('Inventory stock updated!');
      setShowItemModal(false);
      fetchInventoryData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleOpenStockActionModal = (prodId = '') => {
    setStockActionForm({
      product_id: prodId || (products[0]?.id || ''),
      quantity: 1,
      reference_id: `REF-${Date.now().toString().slice(-6)}`,
    });
    setStockActionModal(true);
  };

  const handleExecuteStockAction = async (e) => {
    e.preventDefault();
    if (!stockActionForm.product_id) {
      showError('Please select a product');
      return;
    }

    setActionLoading(true);
    try {
      const pId = stockActionForm.product_id;
      const qty = Number(stockActionForm.quantity);
      const ref = stockActionForm.reference_id;

      const targetProd = products.find((p) => String(p.id) === String(pId));
      const pName = targetProd ? targetProd.name : `Product #${pId}`;

      if (stockActionType === 'add') {
        await inventoryService.addStock(pId, qty, ref);
        showSuccess(`Added ${qty} units to '${pName}'`);
      } else if (stockActionType === 'reserve') {
        await inventoryService.reserveStock(pId, qty, ref);
        showSuccess(`Reserved ${qty} units of '${pName}'`);
      } else if (stockActionType === 'release') {
        await inventoryService.releaseStock(pId, qty, ref);
        showSuccess(`Released ${qty} reserved units of '${pName}'`);
      } else if (stockActionType === 'commit') {
        await inventoryService.commitStock(pId, qty, ref);
        showSuccess(`Committed ${qty} units of '${pName}'`);
      }
      setStockActionModal(false);
      fetchInventoryData();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && activeTab === 'inventory') {
    return (
      <div className="w-full p-6 md:p-8 space-y-6">
        <h1 className="text-3xl font-extrabold text-white">Inventory & Stock Management</h1>
        <LoadingSkeleton count={4} type="table" />
      </div>
    );
  }

  return (
    <div className="w-full pb-12">
      <ControlPanel
        title="Inventory & Stock Management"
        subtitle={`${mergedStockItems.length} Product SKUs Tracked`}
        primaryAction={{
          label: 'Record Stock',
          icon: Plus,
          onClick: () => handleOpenItemModal()
        }}
        secondaryActions={[
          { label: 'Stock Operation', icon: ArrowRightLeft, onClick: () => handleOpenStockActionModal(), isTeal: true },
          { label: 'Add Warehouse', icon: Warehouse, onClick: () => handleOpenWhModal() }
        ]}
        searchQuery={searchTerm}
        onSearchChange={(val) => {
          setSearchTerm(val);
          setCurrentPage(1);
        }}
        searchPlaceholder="Search product by title, SKU..."
        pagination={{
          currentPage: currentPage,
          totalPages: Math.ceil(mergedStockItems.length / 10),
          totalItems: mergedStockItems.length,
          pageSize: 10,
          onPageChange: setCurrentPage
        }}
        onRefresh={fetchInventoryData}
      />

      <div className="p-4 md:p-8 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          <button
            onClick={() => setActiveTab('inventory')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-all ${
              activeTab === 'inventory' ? 'bg-purple-600 text-white shadow' : 'bg-slate-900 text-slate-400 border border-slate-800'
            }`}
          >
            Stock & Warehouses
          </button>
          <button
            onClick={() => setActiveTab('movements')}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
              activeTab === 'movements' ? 'bg-purple-600 text-white shadow' : 'bg-slate-900 text-slate-400 border border-slate-800'
            }`}
          >
            <ArrowRightLeft size={13} /> Stock Movements Log
          </button>
        </div>

        {activeTab === 'inventory' ? (
          <div className="space-y-6">
            {/* Warehouses Grid */}
            <div>
              <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                <Warehouse size={15} className="text-purple-400" /> Fulfillment Centers ({warehouses.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {warehouses.map((wh) => (
                  <div key={wh.id} className="app-card p-4 relative flex flex-col justify-between border-slate-800 hover:border-purple-500/40 transition-all">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-purple-500/20 text-purple-300 border border-purple-500/30">{wh.code}</span>
                      </div>
                      <h4 className="text-base font-extrabold text-white mt-2">{wh.name}</h4>
                      <p className="text-xs text-slate-400 mt-1">{wh.address || 'No location address provided'}</p>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800 mt-3">
                      <button onClick={() => handleOpenWhModal(wh)} className="p-1 rounded bg-slate-800 text-slate-300 hover:text-white" title="Edit Warehouse">
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button onClick={() => setDeleteWhId(wh.id)} className="p-1 rounded bg-slate-800 text-slate-400 hover:text-rose-400" title="Delete Warehouse">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
                {warehouses.length === 0 && (
                  <div className="col-span-full text-xs text-slate-500 p-4 border border-slate-800 rounded-lg bg-slate-900">
                    No custom warehouses configured. Default "Main Warehouse" is active.
                  </div>
                )}
              </div>
            </div>

            {/* Product Stock Levels Table */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Boxes size={15} className="text-teal-400" /> Stock Levels Inventory
                </h3>
              </div>

            <DataTable
              headers={['Product Details', 'Category', 'Price', 'Available Stock', 'Reserved Stock', 'Reorder Level', { label: 'Stock Actions', className: 'text-right' }]}
              isEmpty={paginatedStockItems.length === 0}
              emptyStateProps={{
                icon: Boxes,
                title: 'No inventory items match search',
                description: 'No catalog products match your search keyword.'
              }}
            >
              {paginatedStockItems.map((row) => {
                const p = row.product;
                const isLow = row.quantity_available <= row.reorder_level;

                return (
                  <tr key={p.id}>
                    <td>
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 font-bold shrink-0">
                          <Package className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <div className="font-bold text-white text-xs truncate">{p.name}</div>
                          <span className="font-mono text-[10px] text-purple-300 bg-purple-500/10 px-1 py-0.5 rounded border border-purple-500/20 inline-block mt-0.5">
                            {p.sku || 'NO-SKU'}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="text-xs text-slate-300">
                      {p.category_name || 'Uncategorized'}
                    </td>
                    <td className="font-bold text-emerald-400">
                      ${Number(p.base_price || 0).toFixed(2)}
                    </td>
                    <td>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold inline-flex items-center gap-1 border ${
                        isLow 
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' 
                          : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                      }`}>
                        {isLow && <AlertTriangle className="w-3 h-3 text-rose-400" />}
                        {row.quantity_available} units
                      </span>
                    </td>
                    <td>
                      <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        {row.quantity_reserved} units
                      </span>
                    </td>
                    <td className="text-xs text-slate-400">
                      {row.reorder_level} units
                    </td>
                    <td className="text-right space-x-1.5 whitespace-nowrap">
                      <button
                        onClick={() => {
                          setStockActionType('add');
                          handleOpenStockActionModal(p.id);
                        }}
                        title="Add Stock"
                        className="px-2 py-1 rounded bg-emerald-600/30 text-emerald-300 hover:bg-emerald-600 hover:text-white transition-colors inline-flex items-center gap-1 border border-emerald-500/30 text-xs font-semibold"
                      >
                        <Plus className="w-3.5 h-3.5" /> Add Stock
                      </button>
                      <button
                        onClick={() => handleOpenItemModal(row)}
                        title="Edit Stock Level"
                        className="px-2 py-1 rounded bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors inline-flex items-center gap-1 text-xs font-semibold"
                      >
                        <Edit2 className="w-3.5 h-3.5" /> Adjust
                      </button>
                      <button
                        onClick={() => {
                          setStockActionType('reserve');
                          handleOpenStockActionModal(p.id);
                        }}
                        title="Reserve Stock"
                        className="px-2 py-1 rounded bg-purple-600/30 text-purple-300 hover:bg-purple-600 hover:text-white transition-colors inline-flex items-center gap-1 border border-purple-500/30 text-xs font-semibold"
                      >
                        <ArrowRightLeft className="w-3.5 h-3.5" /> Reserve
                      </button>
                    </td>
                  </tr>
                );
              })}
            </DataTable>

            <Pagination
              currentPage={currentPage}
              totalPages={Math.ceil(mergedStockItems.length / 10)}
              totalItems={mergedStockItems.length}
              pageSize={10}
              onPageChange={(p) => setCurrentPage(p)}
            />
            </div>
          </div>
        ) : (
          <div className="glass-panel p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-indigo-400" /> Stock Movement Audit Log
            </h3>
            <button onClick={fetchMovements} className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {movements.length === 0 ? (
            <p className="text-slate-500 text-xs text-center py-6">No stock movements recorded yet.</p>
          ) : (
            <div className="space-y-2">
              {movements.map((m) => {
                const targetProd = products.find((p) => String(p.id) === String(m.product_id));
                const pName = targetProd ? targetProd.name : `Product #${m.product_id}`;

                return (
                  <div key={m.id} className="p-3 rounded-xl bg-white/5 border border-white/10 font-mono text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <span className="font-bold text-indigo-300">[{m.movement_type || 'MOVEMENT'}]</span>
                      <span className="text-white font-sans font-bold ml-2">{pName}</span>
                      <span className="text-slate-400 ml-2">Qty: {m.quantity}</span>
                    </div>
                    <div className="text-slate-400 text-[11px]">
                      Ref: {m.reference_id || 'N/A'} • {new Date(m.created_at || Date.now()).toLocaleString()}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
      </div>

      {/* Warehouse Modal */}
      <Modal isOpen={showWhModal} onClose={() => setShowWhModal(false)} title={editingWh ? 'Edit Warehouse' : 'Add Fulfillment Center'}>
        <form onSubmit={handleSaveWarehouse} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Warehouse Name</label>
            <input type="text" value={whForm.name} onChange={(e) => setWhForm({ ...whForm, name: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Warehouse Code</label>
            <input type="text" value={whForm.code} onChange={(e) => setWhForm({ ...whForm, code: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Address</label>
            <input type="text" value={whForm.address} onChange={(e) => setWhForm({ ...whForm, address: e.target.value })} className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setShowWhModal(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300">Cancel</button>
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl">Save Warehouse</button>
          </div>
        </form>
      </Modal>

      {/* Stock Record Modal */}
      <Modal isOpen={showItemModal} onClose={() => setShowItemModal(false)} title={editingItem ? `Adjust Stock: ${editingItem.product.name}` : 'Record Inventory Stock'}>
        <form onSubmit={handleSaveInventoryItem} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Select Catalog Product</label>
            <select 
              value={itemForm.product_id} 
              onChange={(e) => setItemForm({ ...itemForm, product_id: e.target.value })} 
              required 
              disabled={!!editingItem}
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 disabled:opacity-60"
            >
              <option value="">-- Choose Product --</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku || 'No SKU'}) - ${Number(p.base_price || 0).toFixed(2)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Fulfillment Warehouse</label>
            <select 
              value={itemForm.warehouse} 
              onChange={(e) => setItemForm({ ...itemForm, warehouse: e.target.value })} 
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">Main Warehouse (Default)</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>{w.name} ({w.code})</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Available Quantity</label>
              <input type="number" value={itemForm.quantity_available} onChange={(e) => setItemForm({ ...itemForm, quantity_available: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Reorder Alert Level</label>
              <input type="number" value={itemForm.reorder_level} onChange={(e) => setItemForm({ ...itemForm, reorder_level: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setShowItemModal(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300">Cancel</button>
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-4 py-2 rounded-xl">Save Stock Level</button>
          </div>
        </form>
      </Modal>

      {/* Stock Action Modal */}
      <Modal isOpen={stockActionModal} onClose={() => setStockActionModal(false)} title="Execute Stock Operation">
        <form onSubmit={handleExecuteStockAction} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Operation Type</label>
            <select value={stockActionType} onChange={(e) => setStockActionType(e.target.value)} className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500">
              <option value="add">Add Stock (Inbound Restock)</option>
              <option value="reserve">Reserve Stock (Hold for Pending Order)</option>
              <option value="release">Release Stock (Cancel Order Hold)</option>
              <option value="commit">Commit Stock (Fulfill & Deduct Inventory)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Select Catalog Product</label>
            <select 
              value={stockActionForm.product_id} 
              onChange={(e) => setStockActionForm({ ...stockActionForm, product_id: e.target.value })} 
              required 
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">-- Choose Product --</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku || 'No SKU'})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Quantity</label>
              <input type="number" min="1" value={stockActionForm.quantity} onChange={(e) => setStockActionForm({ ...stockActionForm, quantity: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Reference Code</label>
              <input type="text" value={stockActionForm.reference_id} onChange={(e) => setStockActionForm({ ...stockActionForm, reference_id: e.target.value })} required className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500" />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setStockActionModal(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300">Cancel</button>
            <button type="submit" disabled={actionLoading} className="bg-amber-600 hover:bg-amber-500 text-white font-bold px-4 py-2 rounded-xl">
              {actionLoading ? 'Executing...' : 'Execute Operation'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deleteWhId} onClose={() => setDeleteWhId(null)} onConfirm={handleDeleteWarehouse} title="Delete Warehouse" message="Are you sure you want to delete this warehouse?" />
    </div>
  );
};

export default InventoryPage;
