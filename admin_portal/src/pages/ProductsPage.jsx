import React, { useState, useEffect, useMemo } from 'react';
import { catalogService, inventoryService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ControlPanel, DataTable, Modal, ConfirmDialog, EmptyState, LoadingSkeleton, ImageUploader, Badge, Pagination } from '../components/common/UIComponents';
import { 
  Package, Plus, Trash2, Tag, Layers, Zap, Clock, DollarSign, 
  Search, ArrowUpDown, Filter, Image as ImageIcon, Sliders, Edit2, Eye, Star,
  ChevronRight, CheckCircle2, AlertCircle, CornerDownRight, Box, Check, X, LayoutList, LayoutGrid 
} from 'lucide-react';

import { usePagination } from '../hooks/usePagination';

const CURRENCIES = [
  { code: 'USD', name: 'USD - US Dollar ($)' },
  { code: 'EUR', name: 'EUR - Euro (€)' },
  { code: 'GBP', name: 'GBP - British Pound (£)' },
  { code: 'JPY', name: 'JPY - Japanese Yen (¥)' },
  { code: 'CAD', name: 'CAD - Canadian Dollar ($)' },
  { code: 'AUD', name: 'AUD - Australian Dollar ($)' },
  { code: 'ETB', name: 'ETB - Ethiopian Birr (Br)' },
];

export const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [mainCategories, setMainCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [discounts, setDiscounts] = useState([]);
  const [attributes, setAttributes] = useState([]);
  const [loading, setLoading] = useState(true);

  // View Mode: Table vs Grid
  const [viewMode, setViewMode] = useState('table');

  // Reusable Pagination hook
  const pagination = usePagination({ initialPage: 1, initialPageSize: 10 });

  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('');
  const [search, setSearch] = useState('');
  const [ordering, setOrdering] = useState('-created_at');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');

  // Modals & Active Action States
  const [showAddProduct, setShowAddProduct] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [detailProduct, setDetailProduct] = useState(null);
  const [showAddDiscount, setShowAddDiscount] = useState(false);
  const [variantProduct, setVariantProduct] = useState(null);
  const [editingVariant, setEditingVariant] = useState(null);
  const [imageProduct, setImageProduct] = useState(null);
  const [deleteId, setDeleteId] = useState(null);

  const { showSuccess, showError } = useToast();

  // Form states for Product
  const [productFormTab, setProductFormTab] = useState('general');
  const [loadingSubcategories, setLoadingSubcategories] = useState(false);

  const [productForm, setProductForm] = useState({
    name: '',
    description: '',
    sku: '',
    category: '',
    subcategory: '',
    base_price: '0.00',
    cost_price: '0.00',
    currency: 'USD',
    image_url: '',
    image_alt_text: '',
    initial_stock: 10,
    initial_variant_sku: '',
    selected_attribute_values: [],
  });

  // Form states for Discount
  const [discountForm, setDiscountForm] = useState({
    title: '',
    product: '',
    category: '',
    discount_type: 'PERCENTAGE',
    discount_value: 10,
    start_time: '',
    end_time: '',
    priority: 1,
  });

  // Form states for Variant
  const [variantForm, setVariantForm] = useState({
    sku: '',
    price: '',
    stock: 10,
    is_active: true,
    attribute_value_ids: [],
    image_url: '',
  });
  const [productVariantsList, setProductVariantsList] = useState([]);

  // Attribute creation quick states
  const [showAttributeCreator, setShowAttributeCreator] = useState(false);
  const [newAttrName, setNewAttrName] = useState('');
  const [selectedAttrForVal, setSelectedAttrForVal] = useState('');
  const [newValName, setNewValName] = useState('');

  // Form states for Product Images
  const [productImagesList, setProductImagesList] = useState([]);
  const [newImageUrl, setNewImageUrl] = useState('');

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [pagination.page, pagination.pageSize, selectedCategory, selectedSubcategory, search, ordering, minPrice, maxPrice]);

  const fetchInitialData = async () => {
    try {
      const [catRes, discRes, attrRes] = await Promise.all([
        catalogService.getCategories({ all: 'true' }).catch(() => ({ data: [] })),
        catalogService.getDiscounts().catch(() => ({ data: [] })),
        catalogService.getAttributes().catch(() => ({ data: [] })),
      ]);
      const allCats = Array.isArray(catRes.data) ? catRes.data : (catRes.data?.results || []);
      setMainCategories(allCats.filter((c) => !c.parent));
      setSubcategories(allCats.filter((c) => !!c.parent));
      setDiscounts(Array.isArray(discRes.data) ? discRes.data : (discRes.data?.results || []));
      setAttributes(Array.isArray(attrRes.data) ? attrRes.data : (attrRes.data?.results || []));
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const fetchSubcategoriesForCategory = async (parentCatId) => {
    if (!parentCatId) return;
    setLoadingSubcategories(true);
    try {
      const res = await catalogService.getCategories({ parent: parentCatId });
      const fetched = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setSubcategories((prev) => {
        const existingIds = new Set(prev.map((c) => c.id));
        const toAdd = fetched.filter((s) => !existingIds.has(s.id));
        return [...prev, ...toAdd];
      });
    } catch (err) {
      console.error('Error fetching subcategories:', err);
    } finally {
      setLoadingSubcategories(false);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
      };
      if (selectedCategory) params.category_id = selectedCategory;
      if (selectedSubcategory) params.subcategory_id = selectedSubcategory;
      if (search) params.search = search;
      if (ordering) params.ordering = ordering;
      if (minPrice) params.min_price = minPrice;
      if (maxPrice) params.max_price = maxPrice;

      const res = await catalogService.getProducts(params);
      const data = res.data;
      if (Array.isArray(data)) {
        setProducts(data);
        pagination.updatePaginationState({ count: data.length, total_pages: 1, current_page: 1 });
      } else {
        setProducts(data?.results || []);
        pagination.updatePaginationState(data);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const availableSubcategoriesForForm = useMemo(() => {
    if (!productForm.category) return subcategories;
    return subcategories.filter((c) => {
      const pId = typeof c.parent === 'object' ? c.parent?.id : c.parent;
      return pId === productForm.category;
    });
  }, [subcategories, productForm.category]);

  const availableSubcategoriesForFilter = useMemo(() => {
    if (!selectedCategory) return subcategories;
    return subcategories.filter((c) => {
      const pId = typeof c.parent === 'object' ? c.parent?.id : c.parent;
      return pId === selectedCategory;
    });
  }, [subcategories, selectedCategory]);

  const selectedMainCatObj = useMemo(() => {
    return mainCategories.find((c) => c.id === productForm.category);
  }, [mainCategories, productForm.category]);

  const selectedSubCatObj = useMemo(() => {
    return subcategories.find((c) => c.id === productForm.subcategory);
  }, [subcategories, productForm.subcategory]);

  // Server-side paginated products
  const paginatedProducts = products;

  const handleOpenAddProductModal = (prod = null) => {
    setProductFormTab('general');
    if (prod) {
      setEditingProduct(prod);
      setProductForm({
        name: prod.name || '',
        description: prod.description || '',
        sku: prod.sku || '',
        category: prod.category || '',
        subcategory: prod.subcategory || '',
        base_price: prod.price_detail?.base_price || prod.base_price || '0.00',
        cost_price: prod.price_detail?.cost_price || '0.00',
        currency: prod.price_detail?.currency || 'USD',
        image_url: prod.images?.[0]?.image_url || '',
        image_alt_text: prod.images?.[0]?.alt_text || '',
        initial_stock: 10,
        initial_variant_sku: '',
        selected_attribute_values: [],
      });
      if (prod.category) {
        fetchSubcategoriesForCategory(prod.category);
      }
    } else {
      const generatedSku = `SKU-${Math.floor(100000 + Math.random() * 900000)}`;
      setEditingProduct(null);
      setProductForm({
        name: '',
        description: '',
        sku: generatedSku,
        category: '',
        subcategory: '',
        base_price: '0.00',
        cost_price: '0.00',
        currency: 'USD',
        image_url: '',
        image_alt_text: '',
        initial_stock: 10,
        initial_variant_sku: `${generatedSku}-VAR1`,
        selected_attribute_values: [],
      });
    }
    setShowAddProduct(true);
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        name: productForm.name,
        description: productForm.description,
        sku: productForm.sku,
        category: productForm.category || null,
        subcategory: productForm.subcategory || null,
        initial_stock: Number(productForm.initial_stock || 10),
        image_url: productForm.image_url || '',
        price_detail: {
          base_price: productForm.base_price,
          cost_price: productForm.cost_price,
          currency: productForm.currency,
        },
      };

      let res;
      if (editingProduct) {
        res = await catalogService.updateProduct(editingProduct.id, payload);
        showSuccess('Product updated successfully');
      } else {
        res = await catalogService.createProduct(payload);
        showSuccess('Product created successfully');
      }

      const prodId = res.data?.id || editingProduct?.id;

      if (prodId) {
        await inventoryService.initProductInventory({
          product_id: prodId,
          quantity_available: Number(productForm.initial_stock || 10),
        }).catch(() => {});
      }

      if (productForm.image_url && prodId) {
        await catalogService.createProductImage({
          product: prodId,
          product_id: prodId,
          image_url: productForm.image_url,
          alt_text: productForm.image_alt_text || productForm.name,
          is_primary: true,
        }).catch(() => {});
      }

      if (!editingProduct && prodId && (productForm.initial_stock > 0 || productForm.selected_attribute_values.length > 0)) {
        await catalogService.createVariant({
          product: prodId,
          sku: productForm.initial_variant_sku || `${productForm.sku}-VAR1`,
          price: productForm.base_price,
          stock: Number(productForm.initial_stock) || 0,
          is_active: true,
          attribute_value_ids: productForm.selected_attribute_values,
        }).catch(() => {});
      }

      setShowAddProduct(false);
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleCreateDiscount = async (e) => {
    e.preventDefault();
    try {
      await catalogService.createDiscount({
        ...discountForm,
        product: discountForm.product || null,
        category: discountForm.category || null,
        priority: Number(discountForm.priority) || 1,
        is_active: true,
      });
      showSuccess('Promotional discount activated!');
      setShowAddDiscount(false);
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDeleteProduct = async () => {
    if (!deleteId) return;
    try {
      await catalogService.deleteProduct(deleteId);
      showSuccess('Product removed');
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteId(null);
    }
  };

  // Variants management
  const openVariantsModal = async (prod) => {
    setVariantProduct(prod);
    setEditingVariant(null);
    try {
      const res = await catalogService.getVariants({ product_id: prod.id });
      const varList = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setProductVariantsList(varList);
      setVariantForm({
        sku: `${prod.sku}-V${varList.length + 1}`,
        price: prod.base_price || '',
        stock: 10,
        is_active: true,
        attribute_value_ids: [],
        image_url: '',
      });
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleAddOrUpdateVariant = async (e) => {
    e.preventDefault();
    if (!variantProduct) return;
    try {
      const payload = {
        product: variantProduct.id,
        sku: variantForm.sku,
        price: variantForm.price ? String(variantForm.price) : null,
        stock: Number(variantForm.stock) || 0,
        is_active: variantForm.is_active,
        attribute_value_ids: variantForm.attribute_value_ids,
        image_url: variantForm.image_url || '',
      };

      if (editingVariant) {
        await catalogService.updateVariant(editingVariant.id, payload);
        showSuccess('Variant updated successfully');
      } else {
        await catalogService.createVariant(payload);
        showSuccess('Product variant created!');
      }

      setEditingVariant(null);
      openVariantsModal(variantProduct);
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleEditVariantClick = (v) => {
    setEditingVariant(v);
    setVariantForm({
      sku: v.sku || '',
      price: v.price || '',
      stock: v.stock || 0,
      is_active: v.is_active ?? true,
      attribute_value_ids: v.attribute_values_detail?.map((a) => a.id) || [],
      image_url: v.image_url || v.images?.[0]?.image_url || '',
    });
  };

  const handleDeleteVariant = async (varId) => {
    try {
      await catalogService.deleteVariant(varId);
      showSuccess('Variant deleted');
      if (variantProduct) openVariantsModal(variantProduct);
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const toggleAttributeValueSelection = (valId) => {
    setVariantForm((prev) => {
      const exists = prev.attribute_value_ids.includes(valId);
      if (exists) {
        return { ...prev, attribute_value_ids: prev.attribute_value_ids.filter((id) => id !== valId) };
      }
      return { ...prev, attribute_value_ids: [...prev.attribute_value_ids, valId] };
    });
  };

  // Quick attribute & value creator inside variant modal
  const handleCreateAttribute = async (e) => {
    e.preventDefault();
    if (!newAttrName.trim()) return;
    try {
      await catalogService.createAttribute({ name: newAttrName.trim(), category: 'COLOR', is_active: true });
      showSuccess(`Attribute "${newAttrName}" created!`);
      setNewAttrName('');
      fetchInitialData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleCreateAttributeValue = async (e) => {
    e.preventDefault();
    if (!selectedAttrForVal || !newValName.trim()) return;
    try {
      await catalogService.createAttributeValue({
        attribute: selectedAttrForVal,
        value: newValName.trim(),
      });
      showSuccess(`Attribute value "${newValName}" added!`);
      setNewValName('');
      fetchInitialData();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  // Images management
  const openImagesModal = async (prod) => {
    setImageProduct(prod);
    try {
      const res = await catalogService.getProductImages({ product_id: prod.id });
      const imgList = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setProductImagesList(imgList);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleAddProductImage = async (e) => {
    e.preventDefault();
    if (!imageProduct || !newImageUrl) return;
    try {
      await catalogService.createProductImage({
        product: imageProduct.id,
        product_id: imageProduct.id,
        image_url: newImageUrl,
      });
      showSuccess('Image attached to product!');
      setNewImageUrl('');
      if (imageProduct) openImagesModal(imageProduct);
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleDeleteProductImage = async (imgId) => {
    try {
      await catalogService.deleteProductImage(imgId);
      showSuccess('Image detached');
      if (imageProduct) openImagesModal(imageProduct);
      fetchProducts();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  return (
    <div className="w-full pb-12">
      {/* Control Panel Sub-Header */}
      <ControlPanel
        title="Products Catalog & Variants"
        subtitle={`${products.length} Items Total`}
        primaryAction={{
          label: 'Add Product',
          icon: Plus,
          onClick: () => handleOpenAddProductModal()
        }}
        secondaryActions={[
          { label: 'Schedule Sale', icon: Zap, onClick: () => setShowAddDiscount(true), isTeal: true }
        ]}
        searchQuery={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search products by title, SKU..."
        filterOptions={[
          { label: 'Sort: Newest First', value: '-created_at' },
          { label: 'Sort: Oldest First', value: 'created_at' },
          { label: 'Sort: Name A-Z', value: 'name' },
          { label: 'Sort: Name Z-A', value: '-name' },
        ]}
        activeFilter={ordering}
        onFilterChange={setOrdering}
        viewMode={viewMode === 'grid' ? 'kanban' : 'list'}
        onViewModeChange={(m) => setViewMode(m === 'kanban' ? 'grid' : 'table')}
        pagination={{
          page: pagination.page,
          totalPages: pagination.totalPages,
          totalItems: pagination.totalItems,
          pageSize: pagination.pageSize,
          onPageChange: pagination.handlePageChange,
        }}
        onRefresh={fetchInitialData}
      />

      <div className="p-4 md:p-8 space-y-6">
        {/* Extra Filters Bar for Categories */}
        <div className="app-card p-4 flex flex-wrap items-center justify-between gap-4 border border-slate-800">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Layers size={14} className="text-purple-400" />
              <span className="text-xs font-bold text-slate-400">Category Filter:</span>
            </div>

            <select
              className="app-input py-1.5 text-xs font-medium"
              value={selectedCategory}
              onChange={(e) => {
                const id = e.target.value;
                setSelectedCategory(id);
                setSelectedSubcategory('');
                if (id) fetchSubcategoriesForCategory(id);
              }}
            >
              <option value="">All Main Categories</option>
              {mainCategories.map((c) => (
                <option key={c.id} value={c.id}>📁 {c.name}</option>
              ))}
            </select>

            <select
              className="app-input py-1.5 text-xs font-medium"
              value={selectedSubcategory}
              onChange={(e) => setSelectedSubcategory(e.target.value)}
            >
              <option value="">All Subcategories</option>
              {availableSubcategoriesForFilter.map((sub) => (
                <option key={sub.id} value={sub.id}>↳ {sub.name}</option>
              ))}
            </select>
          </div>

          {(selectedCategory || selectedSubcategory || search) && (
            <button
              onClick={() => {
                setSelectedCategory('');
                setSelectedSubcategory('');
                setSearch('');
              }}
              className="text-xs font-semibold text-rose-400 hover:underline flex items-center gap-1"
            >
              <X size={13} /> Reset Filters
            </button>
          )}
        </div>

        {/* DATA TABLE VIEW */}
        {viewMode === 'table' && (
          <div>
            {loading ? (
              <LoadingSkeleton count={5} type="table" />
            ) : (
              <>
                <DataTable
                headers={['Product Item', 'SKU', 'Category Taxonomy', 'Base Price', 'Effective Price', 'Variants', { label: 'Actions', className: 'text-right' }]}
                isEmpty={products.length === 0}
                emptyStateProps={{
                  icon: Package,
                  title: 'No products found',
                  description: 'Create your first catalog product or adjust filters to view items.',
                  action: (
                    <button onClick={() => handleOpenAddProductModal()} className="app-btn-primary mt-3">
                      <Plus size={14} /> Add Product
                    </button>
                  )
                }}
              >

                    {paginatedProducts.map((prod) => {
                      const hasDiscount = prod.active_discount;
                      const coverImage = prod.images?.[0]?.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60';
                      const variantsCount = prod.variants?.length || 0;
                      const curr = prod.price_detail?.currency || 'USD';

                      return (
                        <tr key={prod.id} className="hover:bg-white/[0.04] transition-colors">
                          {/* Product Item with Image Thumbnail */}
                          <td className="py-3.5 px-6">
                            <div className="flex items-center gap-3">
                              <div className="w-12 h-12 rounded-xl bg-slate-900 border border-white/10 overflow-hidden shrink-0">
                                <img src={coverImage} alt={prod.name} className="w-full h-full object-cover" />
                              </div>
                              <div>
                                <div className="font-bold text-white text-base hover:text-indigo-300 transition-colors line-clamp-1">
                                  {prod.name}
                                </div>
                                <div className="text-xs text-slate-400 line-clamp-1">{prod.description || 'No description'}</div>
                              </div>
                            </div>
                          </td>

                          {/* SKU */}
                          <td className="py-3.5 px-4 font-mono text-xs text-cyan-300">
                            <span className="bg-slate-900 px-2 py-1 rounded border border-white/10 font-bold">
                              {prod.sku}
                            </span>
                          </td>

                          {/* Category Taxonomy */}
                          <td className="py-3.5 px-4 text-xs font-semibold">
                            <div className="flex items-center gap-1 text-indigo-300 flex-wrap">
                              <span>📁 {prod.category_name || 'Uncategorized'}</span>
                              {prod.subcategory_name && (
                                <>
                                  <ChevronRight size={12} className="text-slate-500" />
                                  <span className="text-cyan-300 font-bold">↳ {prod.subcategory_name}</span>
                                </>
                              )}
                            </div>
                          </td>

                          {/* Base Price */}
                          <td className="py-3.5 px-4 font-mono text-xs font-bold text-slate-200">
                            {curr} {prod.base_price}
                          </td>

                          {/* Effective Price & Discount Badge */}
                          <td className="py-3.5 px-4">
                            {hasDiscount ? (
                              <div className="space-y-0.5">
                                <span className="font-extrabold text-emerald-400 font-mono text-sm">{curr} {prod.dynamic_price}</span>
                                <span className="block text-[10px] bg-pink-500/20 text-pink-300 px-2 py-0.5 rounded border border-pink-500/30 uppercase font-bold">
                                  {prod.active_discount.title}
                                </span>
                              </div>
                            ) : (
                              <span className="font-extrabold text-white font-mono text-sm">{curr} {prod.base_price}</span>
                            )}
                          </td>

                          {/* Variants Badge */}
                          <td className="py-3.5 px-4">
                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                              <Sliders size={12} /> {variantsCount}
                            </span>
                          </td>

                          {/* Action Buttons */}
                          <td className="py-3.5 px-6 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => setDetailProduct(prod)}
                                className="p-1.5 rounded-lg bg-indigo-500/10 text-cyan-300 hover:text-white hover:bg-indigo-600 text-xs transition-colors"
                                title="View Product Details"
                              >
                                <Eye size={14} />
                              </button>

                              <button
                                onClick={() => openVariantsModal(prod)}
                                className="px-2.5 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600 hover:text-white border border-indigo-500/30 text-xs font-bold flex items-center gap-1 transition-colors"
                                title="Manage Product Variants"
                              >
                                <Sliders size={12} /> Variants ({variantsCount})
                              </button>

                              <button
                                onClick={() => openImagesModal(prod)}
                                className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white hover:bg-white/10 text-xs"
                                title="Gallery Images"
                              >
                                <ImageIcon size={14} />
                              </button>

                              <button
                                onClick={() => handleOpenAddProductModal(prod)}
                                className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white hover:bg-white/10 text-xs"
                                title="Edit Product"
                              >
                                <Edit2 size={14} />
                              </button>

                              <button
                                onClick={() => setDeleteId(prod.id)}
                                className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-rose-400 hover:bg-white/10 text-xs"
                                title="Delete Product"
                              >
                                <Trash2 size={14} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
              </DataTable>

              {/* Pagination Controls */}
              <Pagination
                currentPage={pagination.page}
                totalPages={pagination.totalPages}
                totalItems={pagination.totalItems}
                pageSize={pagination.pageSize}
                onPageChange={pagination.handlePageChange}
                onPageSizeChange={pagination.handlePageSizeChange}
              />
            </>
          )}
        </div>
      )}

      {/* CARD GRID VIEW WITH PAGINATION */}
      {viewMode === 'grid' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedProducts.map((prod) => {
              const hasDiscount = prod.active_discount;
              const coverImage = prod.images?.[0]?.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60';
              const variantsCount = prod.variants?.length || 0;

              return (
                <div key={prod.id} className="glass-panel p-5 flex flex-col justify-between space-y-4 hover:border-indigo-500/40 transition-all group">
                  <div>
                    <div className="h-44 rounded-xl bg-slate-900 border border-white/10 overflow-hidden relative mb-3">
                      <img src={coverImage} alt={prod.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                      
                      {hasDiscount && (
                        <span className="absolute top-2.5 left-2.5 bg-pink-500 text-white font-bold text-[10px] px-2 py-0.5 rounded-md shadow-md uppercase">
                          {prod.active_discount.title}
                        </span>
                      )}

                      <span className="absolute bottom-2.5 right-2.5 bg-slate-900/90 text-cyan-300 font-mono font-semibold text-[11px] px-2 py-0.5 rounded-md border border-white/10">
                        SKU: {prod.sku}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-[11px] text-indigo-300 mb-1 flex-wrap">
                      <span className="font-semibold">{prod.category_name || 'Uncategorized'}</span>
                      {prod.subcategory_name && (
                        <>
                          <ChevronRight className="w-3 h-3 text-slate-500" />
                          <span className="text-cyan-400 font-semibold">{prod.subcategory_name}</span>
                        </>
                      )}
                    </div>

                    <h3 className="text-lg font-bold text-white group-hover:text-indigo-300 transition-colors line-clamp-1">{prod.name}</h3>
                    <p className="text-slate-400 text-xs mt-1 line-clamp-2">{prod.description || 'No description provided.'}</p>

                    <div className="mt-3 flex items-center justify-between pt-2 border-t border-white/10">
                      <div>
                        {hasDiscount ? (
                          <div className="flex items-center gap-2">
                            <span className="text-lg font-extrabold text-emerald-400">${prod.dynamic_price}</span>
                            <span className="text-xs text-slate-500 line-through">${prod.base_price}</span>
                          </div>
                        ) : (
                          <span className="text-lg font-extrabold text-white">${prod.base_price}</span>
                        )}
                      </div>

                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30">
                        <Sliders className="w-3 h-3" /> {variantsCount} Variants
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2 pt-3 border-t border-white/10">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => openVariantsModal(prod)}
                        className="px-2.5 py-1.5 rounded-xl bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600 hover:text-white border border-indigo-500/30 text-xs font-bold flex items-center gap-1 transition-colors"
                      >
                        <Sliders className="w-3.5 h-3.5" /> Variants ({variantsCount})
                      </button>

                      <button
                        onClick={() => openImagesModal(prod)}
                        className="p-1.5 rounded-xl bg-white/5 text-slate-300 hover:text-white hover:bg-white/10 text-xs"
                      >
                        <ImageIcon className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => setDetailProduct(prod)}
                        className="p-1.5 rounded-xl bg-indigo-500/10 text-cyan-300 hover:text-white hover:bg-indigo-600 text-xs"
                        title="View Product Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleOpenAddProductModal(prod)}
                        className="p-1.5 rounded-xl bg-white/5 text-slate-300 hover:text-white hover:bg-white/10 text-xs"
                        title="Edit Product"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setDeleteId(prod.id)}
                        className="p-1.5 rounded-xl bg-white/5 text-slate-400 hover:text-rose-400 hover:bg-white/10 text-xs"
                        title="Delete Product"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <Pagination
            currentPage={pagination.page}
            totalPages={pagination.totalPages}
            totalItems={pagination.totalItems}
            pageSize={pagination.pageSize}
            onPageChange={pagination.handlePageChange}
            onPageSizeChange={pagination.handlePageSizeChange}
          />
        </div>
      )}
      </div>

      {/* Add / Edit Product Modal */}
      <Modal
        isOpen={showAddProduct}
        onClose={() => setShowAddProduct(false)}
        title={editingProduct ? 'Edit Product Catalog Item' : 'Create Catalog Product Wizard'}
      >
        <form onSubmit={handleCreateProduct} className="space-y-4">
          {/* Tab Navigation Header */}
          <div className="flex bg-slate-900/90 p-1 rounded-xl border border-white/10 text-xs font-semibold">
            <button
              type="button"
              onClick={() => setProductFormTab('general')}
              className={`flex-1 py-2 px-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                productFormTab === 'general' ? 'bg-indigo-600 text-white shadow font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Package size={14} /> 1. General & Taxonomy
            </button>
            <button
              type="button"
              onClick={() => setProductFormTab('pricing')}
              className={`flex-1 py-2 px-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                productFormTab === 'pricing' ? 'bg-indigo-600 text-white shadow font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              <DollarSign size={14} /> 2. Pricing & Currency
            </button>
            <button
              type="button"
              onClick={() => setProductFormTab('media')}
              className={`flex-1 py-2 px-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                productFormTab === 'media' ? 'bg-indigo-600 text-white shadow font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              <ImageIcon size={14} /> 3. Media & Cover
            </button>
            <button
              type="button"
              onClick={() => setProductFormTab('variants')}
              className={`flex-1 py-2 px-2.5 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                productFormTab === 'variants' ? 'bg-indigo-600 text-white shadow font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Sliders size={14} /> 4. Stock & Attributes
            </button>
          </div>

          {/* TAB 1: GENERAL DETAILS & TAXONOMY */}
          {productFormTab === 'general' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Product Title</label>
                <input
                  type="text"
                  value={productForm.name}
                  onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
                  placeholder="e.g. Wireless Noise-Canceling Headphones"
                  required
                  className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-slate-300">SKU Code</label>
                  <button
                    type="button"
                    onClick={() => setProductForm({ ...productForm, sku: `SKU-${Math.floor(100000 + Math.random() * 900000)}` })}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 font-bold"
                  >
                    Auto Generate SKU
                  </button>
                </div>
                <input
                  type="text"
                  value={productForm.sku}
                  onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })}
                  required
                  className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 font-mono text-xs"
                />
              </div>

              {/* Taxonomy Selectors with Dynamic Fetching */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-white/10 space-y-3">
                <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-indigo-400" /> Category Taxonomy & Dynamic Subcategories
                </h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">📁 Main Category</label>
                    <select
                      value={productForm.category}
                      onChange={(e) => {
                        const mainId = e.target.value;
                        setProductForm({ ...productForm, category: mainId, subcategory: '' });
                        if (mainId) fetchSubcategoriesForCategory(mainId);
                      }}
                      className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">-- None (Uncategorized) --</option>
                      {mainCategories.map((c) => (
                        <option key={c.id} value={c.id}>
                          📁 {c.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1 flex items-center justify-between">
                      <span>↳ Subcategory</span>
                      {loadingSubcategories && <span className="text-[10px] text-cyan-400 animate-pulse">Loading...</span>}
                    </label>
                    <select
                      value={productForm.subcategory}
                      onChange={(e) => setProductForm({ ...productForm, subcategory: e.target.value })}
                      disabled={!productForm.category}
                      className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-40"
                    >
                      <option value="">-- None --</option>
                      {availableSubcategoriesForForm.map((sub) => (
                        <option key={sub.id} value={sub.id}>
                          ↳ {sub.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {(selectedMainCatObj || selectedSubCatObj) && (
                  <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/30 text-xs flex items-center gap-2 text-indigo-200">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>
                      <strong>Taxonomy Link:</strong> {selectedMainCatObj?.name || 'Top'}
                      {selectedSubCatObj && (
                        <>
                          <span className="mx-1 text-slate-500">&gt;</span>
                          <span className="text-cyan-300 font-semibold">{selectedSubCatObj.name}</span>
                        </>
                      )}
                    </span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  rows={3}
                  value={productForm.description}
                  onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
                  placeholder="Product specs, features, overview..."
                  className="w-full bg-slate-900/80 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>
            </div>
          )}

          {/* TAB 2: PRICING & MULTI-CURRENCY */}
          {productFormTab === 'pricing' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Target Currency</label>
                <select
                  value={productForm.currency}
                  onChange={(e) => setProductForm({ ...productForm, currency: e.target.value })}
                  className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                >
                  {CURRENCIES.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Base Sale Price ({productForm.currency})</label>
                  <input
                    type="number"
                    step="0.01"
                    value={productForm.base_price}
                    onChange={(e) => setProductForm({ ...productForm, base_price: e.target.value })}
                    required
                    className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Cost Price ({productForm.currency})</label>
                  <input
                    type="number"
                    step="0.01"
                    value={productForm.cost_price}
                    onChange={(e) => setProductForm({ ...productForm, cost_price: e.target.value })}
                    className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Profit Margin Preview Card */}
              {Number(productForm.base_price) > 0 && (
                <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-emerald-400 font-bold uppercase tracking-wider block">Estimated Profit Margin</span>
                    <span className="text-xl font-extrabold text-white">
                      {productForm.currency} {(Number(productForm.base_price) - Number(productForm.cost_price || 0)).toFixed(2)}
                    </span>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 font-bold text-xs border border-emerald-500/40">
                    {Number(productForm.base_price) > 0
                      ? `${(((Number(productForm.base_price) - Number(productForm.cost_price || 0)) / Number(productForm.base_price)) * 100).toFixed(1)}% Markup`
                      : '0%'}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: MEDIA & IMAGES */}
          {productFormTab === 'media' && (
            <div className="space-y-4">
              <ImageUploader
                value={productForm.image_url}
                onChange={(url) => setProductForm({ ...productForm, image_url: url })}
                label="Primary Cover Image (URL or Upload)"
              />

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Image Alt Text (SEO & Accessibility)</label>
                <input
                  type="text"
                  value={productForm.image_alt_text}
                  onChange={(e) => setProductForm({ ...productForm, image_alt_text: e.target.value })}
                  placeholder="e.g. Front view of wireless headphones in black"
                  className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>
            </div>
          )}

          {/* TAB 4: INITIAL VARIANTS & INVENTORY */}
          {productFormTab === 'variants' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Initial Stock Level</label>
                  <input
                    type="number"
                    value={productForm.initial_stock}
                    onChange={(e) => setProductForm({ ...productForm, initial_stock: e.target.value })}
                    className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Variant SKU</label>
                  <input
                    type="text"
                    value={productForm.initial_variant_sku}
                    onChange={(e) => setProductForm({ ...productForm, initial_variant_sku: e.target.value })}
                    className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500 font-mono text-xs"
                  />
                </div>
              </div>

              {/* Attributes Chips Selection */}
              <div>
                <label className="block text-xs font-bold text-indigo-300 uppercase tracking-wider mb-2">
                  Select Initial Attribute Options
                </label>
                <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                  {attributes.map((attr) => (
                    <div key={attr.id} className="p-3 rounded-xl bg-slate-950/60 border border-white/10 space-y-1.5">
                      <span className="text-xs font-bold text-white block">{attr.name}</span>
                      <div className="flex flex-wrap gap-1.5">
                        {attr.values?.map((val) => {
                          const isSelected = productForm.selected_attribute_values.includes(val.id);
                          return (
                            <button
                              type="button"
                              key={val.id}
                              onClick={() => {
                                setProductForm((prev) => {
                                  const exists = prev.selected_attribute_values.includes(val.id);
                                  return {
                                    ...prev,
                                    selected_attribute_values: exists
                                      ? prev.selected_attribute_values.filter((id) => id !== val.id)
                                      : [...prev.selected_attribute_values, val.id],
                                  };
                                });
                              }}
                              className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                                isSelected
                                  ? 'bg-indigo-600 text-white border-indigo-500 shadow'
                                  : 'bg-slate-900 text-slate-400 border-white/10 hover:text-white'
                              }`}
                            >
                              {val.value}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Modal Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-white/10">
            <div className="flex gap-2">
              {productFormTab !== 'general' && (
                <button
                  type="button"
                  onClick={() => {
                    const tabs = ['general', 'pricing', 'media', 'variants'];
                    const idx = tabs.indexOf(productFormTab);
                    if (idx > 0) setProductFormTab(tabs[idx - 1]);
                  }}
                  className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-slate-300 text-xs font-bold"
                >
                  Previous Tab
                </button>
              )}
              {productFormTab !== 'variants' && (
                <button
                  type="button"
                  onClick={() => {
                    const tabs = ['general', 'pricing', 'media', 'variants'];
                    const idx = tabs.indexOf(productFormTab);
                    if (idx < tabs.length - 1) setProductFormTab(tabs[idx + 1]);
                  }}
                  className="px-3 py-1.5 rounded-xl bg-indigo-600/30 border border-indigo-500/40 text-indigo-200 text-xs font-bold"
                >
                  Next Tab &rarr;
                </button>
              )}
            </div>

            <div className="flex gap-3">
              <button type="button" onClick={() => setShowAddProduct(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300 text-xs">
                Cancel
              </button>
              <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-5 py-2 rounded-xl text-xs shadow-lg shadow-indigo-600/30">
                {editingProduct ? 'Save Changes' : 'Create Product'}
              </button>
            </div>
          </div>
        </form>
      </Modal>

      {/* Add Discount Modal */}
      <Modal isOpen={showAddDiscount} onClose={() => setShowAddDiscount(false)} title="Schedule Time-Based Discount">
        <form onSubmit={handleCreateDiscount} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Promotion Title</label>
            <input
              type="text"
              value={discountForm.title}
              onChange={(e) => setDiscountForm({ ...discountForm, title: e.target.value })}
              required
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Discount Type</label>
              <select
                value={discountForm.discount_type}
                onChange={(e) => setDiscountForm({ ...discountForm, discount_type: e.target.value })}
                className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="PERCENTAGE">Percentage (%)</option>
                <option value="FIXED_AMOUNT">Fixed Amount ($)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Discount Value</label>
              <input
                type="number"
                step="0.01"
                value={discountForm.discount_value}
                onChange={(e) => setDiscountForm({ ...discountForm, discount_value: parseFloat(e.target.value) || 0 })}
                required
                className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Start Datetime</label>
              <input
                type="datetime-local"
                value={discountForm.start_time}
                onChange={(e) => setDiscountForm({ ...discountForm, start_time: e.target.value })}
                required
                className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">End Datetime</label>
              <input
                type="datetime-local"
                value={discountForm.end_time}
                onChange={(e) => setDiscountForm({ ...discountForm, end_time: e.target.value })}
                required
                className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
            <button type="button" onClick={() => setShowAddDiscount(false)} className="px-4 py-2 rounded-xl border border-white/10 text-slate-300">
              Cancel
            </button>
            <button type="submit" className="bg-pink-600 hover:bg-pink-500 text-white font-bold px-4 py-2 rounded-xl">
              Activate Promotion
            </button>
          </div>
        </form>
      </Modal>

      {/* Product Variants Management Modal */}
      {variantProduct && (
        <Modal
          isOpen={!!variantProduct}
          onClose={() => {
            setVariantProduct(null);
            setEditingVariant(null);
          }}
          title={`Product Variants — "${variantProduct.name}"`}
        >
          <div className="space-y-6">
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-white/10 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Tag className="w-4 h-4 text-indigo-400" /> Catalog Product Attributes
                </span>
                <button
                  onClick={() => setShowAttributeCreator(!showAttributeCreator)}
                  className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
                >
                  {showAttributeCreator ? 'Hide Attribute Tools' : '+ Create Attribute / Values'}
                </button>
              </div>

              {showAttributeCreator && (
                <div className="pt-2 border-t border-white/10 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  <form onSubmit={handleCreateAttribute} className="p-2.5 rounded-lg bg-slate-900 border border-white/10 space-y-2">
                    <span className="font-semibold text-slate-300 block">1. Create New Attribute (e.g. Size, Color)</span>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Attribute Name"
                        value={newAttrName}
                        onChange={(e) => setNewAttrName(e.target.value)}
                        className="w-full bg-slate-950 border border-white/10 rounded-lg px-2.5 py-1 text-white text-xs"
                      />
                      <button type="submit" className="bg-indigo-600 text-white px-3 py-1 rounded-lg font-bold shrink-0">
                        Add
                      </button>
                    </div>
                  </form>

                  <form onSubmit={handleCreateAttributeValue} className="p-2.5 rounded-lg bg-slate-900 border border-white/10 space-y-2">
                    <span className="font-semibold text-slate-300 block">2. Add Option Value (e.g. XL, Blue)</span>
                    <div className="space-y-1.5">
                      <select
                        value={selectedAttrForVal}
                        onChange={(e) => setSelectedAttrForVal(e.target.value)}
                        className="w-full bg-slate-950 border border-white/10 rounded-lg px-2 py-1 text-white text-xs"
                      >
                        <option value="">Select Attribute Group</option>
                        {attributes.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.name}
                          </option>
                        ))}
                      </select>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Value (e.g. XL, Red)"
                          value={newValName}
                          onChange={(e) => setNewValName(e.target.value)}
                          className="w-full bg-slate-950 border border-white/10 rounded-lg px-2.5 py-1 text-white text-xs"
                        />
                        <button type="submit" className="bg-cyan-600 text-white px-3 py-1 rounded-lg font-bold shrink-0">
                          Add
                        </button>
                      </div>
                    </div>
                  </form>
                </div>
              )}
            </div>

            <form onSubmit={handleAddOrUpdateVariant} className="p-4 rounded-xl bg-slate-900/90 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                  {editingVariant ? 'Edit Variant' : 'Add New Variant'}
                </h4>
                {editingVariant && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingVariant(null);
                      setVariantForm({
                        sku: `${variantProduct.sku}-V${productVariantsList.length + 1}`,
                        price: variantProduct.base_price || '',
                        stock: 10,
                        is_active: true,
                        attribute_value_ids: [],
                      });
                    }}
                    className="text-[11px] text-slate-400 hover:text-white"
                  >
                    Cancel Editing
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Variant SKU</label>
                  <input
                    type="text"
                    placeholder="SKU Code"
                    value={variantForm.sku}
                    onChange={(e) => setVariantForm({ ...variantForm, sku: e.target.value })}
                    required
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Override Price ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder={`Default: $${variantProduct.base_price}`}
                    value={variantForm.price}
                    onChange={(e) => setVariantForm({ ...variantForm, price: e.target.value })}
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Inventory Stock</label>
                  <input
                    type="number"
                    placeholder="Stock Qty"
                    value={variantForm.stock}
                    onChange={(e) => setVariantForm({ ...variantForm, stock: parseInt(e.target.value) || 0 })}
                    required
                    className="w-full bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white"
                  />
                </div>
              </div>

              {/* Variant Specific Image Uploader */}
              <ImageUploader
                value={variantForm.image_url}
                onChange={(url) => setVariantForm({ ...variantForm, image_url: url })}
                label="Variant Specific Image (Optional)"
              />

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-[11px] font-semibold text-slate-300">Attach Variant Attributes & Values</label>
                  <label className="inline-flex items-center gap-1.5 cursor-pointer text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={variantForm.is_active}
                      onChange={(e) => setVariantForm({ ...variantForm, is_active: e.target.checked })}
                      className="rounded border-white/10 bg-slate-950 text-indigo-600 focus:ring-0"
                    />
                    <span>Variant Active</span>
                  </label>
                </div>

                {attributes.length === 0 ? (
                  <p className="text-[11px] text-slate-500 italic">No attributes available. Use "+ Create Attribute / Values" above to add sizes or colors.</p>
                ) : (
                  <div className="space-y-2.5 p-3 rounded-xl bg-slate-950/60 border border-white/10">
                    {attributes.map((attr) => (
                      <div key={attr.id} className="space-y-1">
                        <span className="text-[11px] font-bold text-indigo-400 block">{attr.name}:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {attr.values?.map((val) => {
                            const isSelected = variantForm.attribute_value_ids.includes(val.id);
                            return (
                              <button
                                key={val.id}
                                type="button"
                                onClick={() => toggleAttributeValueSelection(val.id)}
                                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border inline-flex items-center gap-1 ${
                                  isSelected
                                    ? 'bg-indigo-600 text-white border-indigo-400 shadow-md shadow-indigo-600/30'
                                    : 'bg-slate-900 text-slate-300 border-white/10 hover:border-white/20'
                                }`}
                              >
                                {isSelected && <Check className="w-3 h-3 text-white" />}
                                <span>{val.value}</span>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end pt-1">
                <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs px-4 py-2 rounded-xl shadow-md shadow-indigo-600/30">
                  {editingVariant ? 'Update Variant' : 'Create Variant'}
                </button>
              </div>
            </form>

            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Existing Product Variants ({productVariantsList.length})
              </h4>

              {productVariantsList.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-4 text-center">No variants created for this product yet.</p>
              ) : (
                <div className="space-y-2.5">
                  {productVariantsList.map((v) => {
                    const varImg = v.image_url || v.images?.[0]?.image_url || variantProduct.images?.[0]?.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60';
                    return (
                      <div key={v.id} className="p-3 rounded-xl bg-slate-900 border border-white/10 flex flex-wrap sm:flex-nowrap items-center justify-between gap-3 text-xs hover:border-indigo-500/30 transition-all">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-slate-950 border border-white/10 overflow-hidden shrink-0">
                            <img src={varImg} alt={v.sku} className="w-full h-full object-cover" />
                          </div>
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-mono font-bold text-white bg-slate-950 px-2 py-0.5 rounded border border-white/10">
                                {v.sku}
                              </span>

                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                                v.is_active ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-red-500/15 text-red-300 border border-red-500/30'
                              }`}>
                                {v.is_active ? 'Active' : 'Disabled'}
                              </span>

                              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                v.stock > 0 ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30' : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                              }`}>
                                Stock: {v.stock}
                              </span>
                            </div>

                            {v.attribute_values_detail && v.attribute_values_detail.length > 0 && (
                              <div className="flex flex-wrap gap-1 pt-0.5">
                                {v.attribute_values_detail.map((attrVal) => (
                                  <span key={attrVal.id} className="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30 text-[11px] text-indigo-200">
                                    <strong className="text-slate-400 font-normal">{attrVal.attribute_name}:</strong> {attrVal.value}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          <span className="font-extrabold text-white text-sm">${v.effective_price || v.price || variantProduct.base_price}</span>
                          <button
                            onClick={() => handleEditVariantClick(v)}
                            className="p-1.5 rounded-lg bg-white/5 text-slate-300 hover:text-white hover:bg-white/10"
                            title="Edit Variant"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteVariant(v.id)}
                            className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-rose-400 hover:bg-white/10"
                            title="Delete Variant"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Gallery Images Modal */}
      {imageProduct && (
        <Modal
          isOpen={!!imageProduct}
          onClose={() => setImageProduct(null)}
          title={`Image Gallery for "${imageProduct.name}"`}
        >
          <div className="space-y-6">
            <form onSubmit={handleAddProductImage} className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
              <h4 className="text-xs font-bold text-indigo-300 uppercase">Attach New Image</h4>
              <ImageUploader value={newImageUrl} onChange={setNewImageUrl} label="Image URL or Upload" />
              <button
                type="submit"
                disabled={!newImageUrl}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs px-4 py-2 rounded-xl disabled:opacity-40"
              >
                Attach Image
              </button>
            </form>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {productImagesList.map((img) => (
                <div key={img.id} className="relative rounded-xl overflow-hidden border border-white/10 group h-28 bg-slate-900">
                  <img src={img.image_url} alt="" className="w-full h-full object-cover" />
                  <button
                    onClick={() => handleDeleteProductImage(img.id)}
                    className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/70 text-rose-400 hover:bg-rose-600 hover:text-white transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </Modal>
      )}

      {/* Product Detail Modal */}
      {detailProduct && (
        <Modal
          isOpen={!!detailProduct}
          onClose={() => setDetailProduct(null)}
          title={`Product Overview — "${detailProduct.name}"`}
        >
          <div className="space-y-6 text-sm text-slate-300">
            {/* Top Overview */}
            <div className="flex flex-col sm:flex-row gap-5 p-4 rounded-2xl bg-slate-900 border border-white/10">
              <div className="w-full sm:w-36 h-36 rounded-xl bg-slate-950 border border-white/10 overflow-hidden shrink-0">
                <img
                  src={detailProduct.images?.[0]?.image_url || detailProduct.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60'}
                  alt={detailProduct.name}
                  className="w-full h-full object-cover"
                />
              </div>

              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2 flex-wrap text-xs">
                  <span className="bg-slate-950 font-mono text-cyan-300 px-2 py-0.5 rounded border border-white/10 font-bold">
                    SKU: {detailProduct.sku}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-semibold">
                    📁 {detailProduct.category_name || 'Uncategorized'}
                  </span>
                  {detailProduct.subcategory_name && (
                    <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-semibold">
                      ↳ {detailProduct.subcategory_name}
                    </span>
                  )}
                </div>

                <h3 className="text-xl font-extrabold text-white">{detailProduct.name}</h3>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                  {detailProduct.description || 'No description provided.'}
                </p>

                <div className="flex items-center gap-2 pt-1 text-xs text-amber-400">
                  <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                  <span className="font-bold text-white">{detailProduct.average_rating || '0.0'}</span>
                  <span className="text-slate-500">({detailProduct.reviews_count || 0} reviews)</span>
                  <span className="text-slate-600">|</span>
                  <span className="text-slate-400">Likes: {detailProduct.likes_count || 0}</span>
                </div>
              </div>
            </div>

            {/* Financial Card */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-xl bg-slate-950/80 border border-white/10">
              <div>
                <span className="text-[11px] text-slate-400 block">Currency</span>
                <strong className="text-white font-mono">{detailProduct.price_detail?.currency || 'USD'}</strong>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 block">Base Price</span>
                <strong className="text-white font-mono">${detailProduct.base_price || '0.00'}</strong>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 block">Effective Price</span>
                <strong className="text-emerald-400 font-mono font-extrabold">${detailProduct.dynamic_price || detailProduct.base_price || '0.00'}</strong>
              </div>
              <div>
                <span className="text-[11px] text-slate-400 block">Active Promotion</span>
                {detailProduct.active_discount ? (
                  <span className="text-xs font-bold text-pink-400 block truncate">{detailProduct.active_discount.title}</span>
                ) : (
                  <span className="text-xs text-slate-500 italic block">None</span>
                )}
              </div>
            </div>

            {/* Variants */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-indigo-300 uppercase tracking-wider">
                Product Variants ({detailProduct.variants?.length || 0})
              </h4>
              {!detailProduct.variants || detailProduct.variants.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-2">No variants created for this product.</p>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {detailProduct.variants.map((v) => (
                    <div key={v.id} className="p-3 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-between text-xs">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-cyan-300 bg-slate-950 px-2 py-0.5 rounded border border-white/10">
                            {v.sku}
                          </span>
                          <span className="text-slate-400">Stock: <strong className="text-white">{v.stock}</strong></span>
                        </div>
                        {v.attribute_values_detail && v.attribute_values_detail.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {v.attribute_values_detail.map((av) => (
                              <span key={av.id} className="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30 text-[11px] text-indigo-200">
                                {av.attribute_name}: <strong>{av.value}</strong>
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <span className="font-extrabold text-white font-mono text-sm">${v.effective_price || v.price || detailProduct.base_price}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Attached Gallery */}
            {detailProduct.images && detailProduct.images.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Gallery Media ({detailProduct.images.length})
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {detailProduct.images.map((img) => (
                    <div key={img.id} className="h-20 rounded-xl overflow-hidden border border-white/10 bg-slate-950">
                      <img src={img.image_url} alt="" className="w-full h-full object-cover" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDeleteProduct}
        title="Delete Product"
        message="Are you sure you want to delete this product?"
      />
    </div>
  );
};
