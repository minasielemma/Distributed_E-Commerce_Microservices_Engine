import React, { useState, useEffect, useContext, useCallback } from 'react';
import { catalogService, recommendationService, authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { CartContext } from '../context/CartContext';
import { AuthContext } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { EmptyState, Pagination } from '../components/common/UIComponents';
import { ProductCard } from '../components/ProductCard';
import { HeroCarousel } from '../components/HeroCarousel';
import { ProductCarousel } from '../components/ProductCarousel';
import { CategoryCard } from '../components/CategoryCard';
import { usePagination } from '../hooks/usePagination';
import { Search, Filter, ArrowUpDown, X, PackageX, Menu, Store } from 'lucide-react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';

export const StorefrontHome = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user, token, activeTenantId, setTenant } = useContext(AuthContext);

  // State from URL or defaults
  const [selectedCategory, setSelectedCategory] = useState(() => searchParams.get('category') || '');
  const [selectedSubcategory, setSelectedSubcategory] = useState(() => searchParams.get('subcategory') || '');
  const [search, setSearch] = useState(() => searchParams.get('search') || '');
  const [ordering, setOrdering] = useState(() => searchParams.get('ordering') || '-created_at');
  const [minPrice, setMinPrice] = useState(() => searchParams.get('min_price') || '');
  const [maxPrice, setMaxPrice] = useState(() => searchParams.get('max_price') || '');
  const [isAvailable, setIsAvailable] = useState(() => searchParams.get('available') === 'true');
  const [collection, setCollection] = useState(() => searchParams.get('collection') || '');
  const [selectedShop, setSelectedShop] = useState(() => searchParams.get('shop') || searchParams.get('tenant_id') || '');

  useEffect(() => {
    setSelectedCategory(searchParams.get('category') || '');
    setSelectedSubcategory(searchParams.get('subcategory') || '');
    setSearch(searchParams.get('search') || '');
    setOrdering(searchParams.get('ordering') || '-created_at');
    setMinPrice(searchParams.get('min_price') || '');
    setMaxPrice(searchParams.get('max_price') || '');
    setIsAvailable(searchParams.get('available') === 'true');
    setCollection(searchParams.get('collection') || '');
    setSelectedShop(searchParams.get('shop') || searchParams.get('tenant_id') || '');
  }, [searchParams]);


  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [subcategoriesMap, setSubcategoriesMap] = useState({});
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);

  // Scalable Filter Search & Pagination States
  const [shopSearchInput, setShopSearchInput] = useState('');
  const [isSearchingShops, setIsSearchingShops] = useState(false);
  const [shopPage, setShopPage] = useState(1);
  const [hasMoreShops, setHasMoreShops] = useState(true);

  const [categorySearchInput, setCategorySearchInput] = useState('');
  const [categorySearchResults, setCategorySearchResults] = useState([]);
  const [isSearchingCategories, setIsSearchingCategories] = useState(false);
  const [categoryPage, setCategoryPage] = useState(1);
  const [hasMoreCategories, setHasMoreCategories] = useState(true);

  // Home specific sections
  const [bestsellers, setBestsellers] = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [deals, setDeals] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [loadingSections, setLoadingSections] = useState(true);

  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  // Close mobile filter sidebar on filter/search URL updates
  useEffect(() => {
    setMobileFilterOpen(false);
  }, [searchParams]);

  // Lock body scroll & handle Escape key when mobile filter drawer is open
  useEffect(() => {
    if (mobileFilterOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setMobileFilterOpen(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileFilterOpen]);

  const { addToCart, addToWishlist, wishlist } = useContext(CartContext);
  const { showSuccess, showError } = useToast();
  const navigate = useNavigate();

  const pagination = usePagination({ initialPage: 1, initialPageSize: 12, syncUrl: true });

  const wishlistedIds = new Set((wishlist?.items || []).map(item => String(item.product?.id || item.product_id)));

  const hasActiveFilters = Boolean(selectedCategory || selectedSubcategory || search || minPrice || maxPrice || isAvailable || collection || selectedShop);


  // Initial Root Categories Load
  useEffect(() => {
    fetchCategories();
  }, []);

  // Load shops (Default recommended/trending or search results with pagination)
  const loadShops = useCallback(async (page = 1, searchQuery = '', append = false) => {
    setIsSearchingShops(true);
    try {
      if (!searchQuery.trim() && page === 1) {
        // Try fetching personalized / trending recommendations first
        try {
          const recRes = await recommendationService.getRecommendedShops({ limit: 10 });
          const recResults = recRes.data?.results || [];
          if (recResults.length > 0) {
            const tenantRes = await authService.getTenants({ page: 1, page_size: 10 });
            const allTenants = Array.isArray(tenantRes.data) ? tenantRes.data : (tenantRes.data?.results || []);
            setTenants(allTenants);
            setHasMoreShops(Boolean(tenantRes.data?.next));
            setShopPage(1);
            return;
          }
        } catch (e) {
          console.warn("Recommendation fallback to default tenants fetch", e);
        }
      }

      // Standard Paginated Search Request
      const params = { page, page_size: 10 };
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await authService.getTenants(params);
      const rawData = res.data;
      const tenantList = Array.isArray(rawData) ? rawData : (rawData?.results || []);
      const nextExists = Boolean(rawData?.next);

      if (append) {
        setTenants((prev) => [...prev, ...tenantList]);
      } else {
        setTenants(tenantList);
      }
      setHasMoreShops(nextExists);
      setShopPage(page);
    } catch (err) {
      console.error('Failed to load tenants:', err);
    } finally {
      setIsSearchingShops(false);
    }
  }, []);

  // Debounced effect for Shop Search Input
  useEffect(() => {
    const timer = setTimeout(() => {
      loadShops(1, shopSearchInput, false);
    }, 300);
    return () => clearTimeout(timer);
  }, [shopSearchInput, loadShops]);

  // Handle Shop Scroll for Infinite Pagination
  const handleShopScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - scrollTop - clientHeight < 20 && hasMoreShops && !isSearchingShops) {
      loadShops(shopPage + 1, shopSearchInput, true);
    }
  };

  // Load Categories (Paginated Search)
  const loadCategorySearch = useCallback(async (page = 1, searchQuery = '', append = false) => {
    if (!searchQuery.trim()) {
      setCategorySearchResults([]);
      setHasMoreCategories(false);
      return;
    }
    setIsSearchingCategories(true);
    try {
      const res = await catalogService.getCategories({ search: searchQuery.trim(), page, page_size: 10 });
      const rawData = res.data;
      const cats = Array.isArray(rawData) ? rawData : (rawData?.results || []);
      const nextExists = Boolean(rawData?.next);

      if (append) {
        setCategorySearchResults((prev) => [...prev, ...cats]);
      } else {
        setCategorySearchResults(cats);
      }
      setHasMoreCategories(nextExists);
      setCategoryPage(page);
    } catch (err) {
      console.error('Failed to search categories:', err);
    } finally {
      setIsSearchingCategories(false);
    }
  }, []);

  // Debounced effect for Category Search Input
  useEffect(() => {
    const timer = setTimeout(() => {
      loadCategorySearch(1, categorySearchInput, false);
    }, 300);
    return () => clearTimeout(timer);
  }, [categorySearchInput, loadCategorySearch]);

  // Handle Category Scroll for Infinite Pagination
  const handleCategoryScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollHeight - scrollTop - clientHeight < 20 && hasMoreCategories && !isSearchingCategories) {
      loadCategorySearch(categoryPage + 1, categorySearchInput, true);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await catalogService.getCategories({ is_main: true, limit: 15 });
      const cats = Array.isArray(res.data) ? res.data : (res.data?.results || []);
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const fetchProducts = useCallback(async () => {
    if (!hasActiveFilters) return;
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
      if (isAvailable) params.is_available = 'true';
      if (selectedShop) params.tenant_id = selectedShop;

      let res;
      if (collection === 'deals') {
        res = await catalogService.getDeals(params);
      } else if (collection === 'bestsellers') {
        res = await catalogService.getBestsellers(params);
      } else if (collection === 'new_arrivals') {
        res = await catalogService.getNewArrivals(params);
      } else if (collection === 'recommended') {
        res = await recommendationService.getPersonalized({ limit: params.page_size || 20, ...(selectedShop ? { tenant_id: selectedShop } : {}) });
      } else {
        res = await catalogService.getProducts(params);
      }
      
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
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, selectedCategory, selectedSubcategory, search, ordering, minPrice, maxPrice, isAvailable, collection, selectedShop, hasActiveFilters]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    if (!hasActiveFilters) {
      const loadSections = async () => {
        setLoadingSections(true);
        try {
          const params = { page_size: 15 };
          if (selectedShop) params.tenant_id = selectedShop;

          const [bsRes, naRes, dealsRes, recRes] = await Promise.all([
            catalogService.getBestsellers(params),
            catalogService.getNewArrivals(params),
            catalogService.getDeals(params),
            recommendationService.getPersonalized({ limit: 15, ...(selectedShop ? { tenant_id: selectedShop } : {}) }).catch(() => ({ data: { results: [] } }))
          ]);
          setBestsellers(Array.isArray(bsRes.data) ? bsRes.data : bsRes.data?.results || []);
          setNewArrivals(Array.isArray(naRes.data) ? naRes.data : naRes.data?.results || []);
          setDeals(Array.isArray(dealsRes.data) ? dealsRes.data : dealsRes.data?.results || []);
          setRecommended(recRes.data?.results || []);
        } catch (err) {
          console.error("Failed to load home sections", err);
        } finally {
          setLoadingSections(false);
        }
      };
      loadSections();
    }
  }, [hasActiveFilters, selectedShop]);

  // Sync state changes to URL
  const updateFilters = (newFilters) => {
    pagination.resetPage();
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      Object.entries(newFilters).forEach(([key, val]) => {
        if (val !== undefined && val !== '' && val !== false) {
          next.set(key, String(val));
        } else {
          next.delete(key);
        }
      });
      next.set('page', '1');
      return next;
    }, { replace: true });
  };

  const handleCategoryChange = async (catId) => {
    setSelectedCategory(catId);
    setSelectedSubcategory('');
    updateFilters({ category: catId, subcategory: '', search, ordering, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: selectedShop });

    if (catId && !subcategoriesMap[catId]) {
      try {
        const res = await catalogService.getCategories({ parent: catId });
        const subs = Array.isArray(res.data) ? res.data : (res.data?.results || []);
        setSubcategoriesMap((prev) => ({ ...prev, [catId]: subs }));
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleShopChange = (shopId) => {
    setSelectedShop(shopId);
    setTenant(shopId);
    updateFilters({ category: selectedCategory, subcategory: selectedSubcategory, search, ordering, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: shopId });
  };

  const handleClearFilters = () => {
    setSelectedCategory('');
    setSelectedSubcategory('');
    setSearch('');
    setOrdering('-created_at');
    setMinPrice('');
    setMaxPrice('');
    setIsAvailable(false);
    setCollection('');
    setSelectedShop('');
    setTenant('');
    pagination.resetPage();
    setSearchParams({}, { replace: true });
  };

  const handleAddToCart = async (product, hasVariants) => {
    if (hasVariants) {
      navigate(`/products/${product.id}`);
      return;
    }
    try {
      await addToCart(product);
      showSuccess(`Added "${product.name}" to cart`);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const handleToggleWishlist = async (product) => {
    try {
      await addToWishlist(product);
      showSuccess(`Saved "${product.name}" to wishlist`);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  };

  const activeSubcategories = selectedCategory ? (subcategoriesMap[selectedCategory] || []) : [];

  const COLLECTION_TITLES = {
    all: 'All Products',
    deals: 'Top Deals',
    bestsellers: 'Best Sellers',
    new_arrivals: 'New Arrivals',
    recommended: 'Recommended for You',
  };

  const renderHomeLayout = () => {
    // Helper to extract product info for a category card item
    const getProductItem = (prod) => ({
      image: prod?.images?.[0]?.image_url || 'https://via.placeholder.com/200?text=No+Image',
      label: prod?.name || 'Product',
      linkUrl: `/products/${prod?.id}`
    });

    const dealsForCards = deals.slice(0, 4).map(getProductItem);
    const bestsellersForCards = bestsellers.slice(0, 4).map(getProductItem);
    const arrivalsForCards = newArrivals.slice(0, 4).map(getProductItem);
    const singleFeatured = deals.length > 4 ? [getProductItem(deals[4])] : [];

    return (
      <div className="w-full bg-[#E3E6E6] min-h-screen">
        <HeroCarousel products={deals.slice(0, 5)} isLoading={loadingSections} />
        
        <div className="max-w-[1500px] mx-auto px-4 sm:px-6 relative -mt-4 sm:-mt-16 lg:-mt-32 z-20 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <CategoryCard 
              title="Top Deals"
              linkText="Shop all deals"
              linkUrl="/?collection=deals"
              items={dealsForCards}
            />
            <CategoryCard 
              title="Best Sellers"
              linkText="See more best sellers"
              linkUrl="/?collection=bestsellers"
              items={bestsellersForCards}
            />
             <CategoryCard 
              title="New Arrivals"
              linkText="Shop new releases"
              linkUrl="/?collection=new_arrivals"
              items={arrivalsForCards}
            />
            {singleFeatured.length > 0 ? (
              <CategoryCard 
                title="Featured Deal"
                linkText="Shop now"
                linkUrl={singleFeatured[0].linkUrl}
                items={singleFeatured}
              />
            ) : !token ? (
               <div className="amz-card p-5 flex flex-col h-[420px] bg-white z-10 items-center justify-center text-center">
                  <h2 className="text-xl font-bold mb-2">Sign in for the best experience</h2>
                  <Link to="/login" className="bg-[#FFD814] border border-[#FCD200] rounded-lg px-8 py-1.5 shadow-sm hover:bg-[#F7CA00] w-full max-w-[200px] font-medium text-sm mb-2 text-[#0F1111]">
                    Sign in securely
                  </Link>
                  <Link to="/register" className="text-xs text-amazon-link-teal hover:text-amazon-orange hover:underline">
                    New to ApexStore? Start here.
                  </Link>
               </div>
            ) : (
               <div className="amz-card p-5 flex flex-col h-[420px] bg-white z-10 items-center justify-center text-center">
                  <h2 className="text-xl font-bold mb-2">Welcome back{user ? `, ${user.username || user.first_name || 'User'}` : ''}!</h2>
                  <p className="text-sm text-gray-600 mb-4">Discover more items recommended for you.</p>
                  <Link to="/profile" className="text-amazon-link-teal hover:text-amazon-orange hover:underline">
                    Go to your profile
                  </Link>
               </div>
            )}
          </div>

          {recommended.length > 0 && (
            <ProductCarousel title="Recommended for You" seeMoreLink="/?collection=recommended" products={recommended} isLoading={loadingSections} />
          )}
          <ProductCarousel title="Exciting Deals" seeMoreLink="/?collection=deals" products={deals} isLoading={loadingSections} />
          <ProductCarousel title="Best Sellers" seeMoreLink="/?collection=bestsellers" products={bestsellers} isLoading={loadingSections} />
          <ProductCarousel title="New Arrivals" seeMoreLink="/?collection=new_arrivals" products={newArrivals} isLoading={loadingSections} />
        </div>
      </div>
    );
  };

  const renderSearchLayout = () => {
    return (
      <div className="w-full bg-white min-h-screen">
        {/* Collection Header Banner */}
        {collection && (
          <div className="bg-[#F7FAFA] border-b border-[#D5D9D9] px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-[#0F1111]">{COLLECTION_TITLES[collection] || collection}</h1>
              <p className="text-sm text-amazon-text-secondary">Explore all products in this collection</p>
            </div>
            <button
              onClick={() => updateFilters({ collection: '' })}
              className="text-sm font-medium text-amazon-link-teal hover:text-amazon-orange hover:underline flex items-center gap-1"
            >
              <X size={16} /> Clear collection
            </button>
          </div>
        )}

        {/* Advanced Filter & Sorting Toolbar */}
        <div className="border-b border-[#D5D9D9] shadow-sm px-4 py-2 flex flex-wrap items-center justify-between gap-4 text-sm bg-white">
          <div className="flex items-center gap-4">
            <span className="font-bold text-amazon-text-primary">
              {pagination.totalItems > 0 ? `1-${Math.min(pagination.pageSize, pagination.totalItems)} of over ${pagination.totalItems} results` : '0 results'}
            </span>
            {collection && !search && (
              <span className="text-amazon-text-secondary">for <span className="font-bold text-amazon-text-primary text-amazon-orange">{COLLECTION_TITLES[collection] || collection}</span></span>
            )}
            {search && <span className="text-amazon-text-secondary">for <span className="font-bold text-amazon-text-primary text-amazon-orange">"{search}"</span></span>}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Sort Dropdown */}
            <div className="flex items-center gap-2 bg-[#F0F2F2] border border-[#D5D9D9] rounded-lg px-2 py-1 shadow-sm hover:bg-[#E3E6E6]">
              <span className="text-xs text-amazon-text-secondary">Sort by:</span>
              <select
                className="bg-transparent text-xs text-amazon-text-primary font-bold focus:outline-none cursor-pointer"
                value={ordering}
                onChange={(e) => {
                  setOrdering(e.target.value);
                  updateFilters({ category: selectedCategory, subcategory: selectedSubcategory, search, ordering: e.target.value, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: selectedShop });
                }}
              >
                <option value="-created_at">Featured</option>
                <option value="price_asc">Price: Low to High</option>
                <option value="price_desc">Price: High to Low</option>
                <option value="name_asc">Name: A to Z</option>
                <option value="name_desc">Name: Z to A</option>
              </select>
            </div>

            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="flex items-center gap-1 text-xs text-amazon-link-teal hover:text-amazon-orange hover:underline"
              >
                <X size={14} /> Clear filters
              </button>
            )}
          </div>
        </div>

        {/* Mobile Filter Button */}
        <div className="md:hidden flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-[#D5D9D9]">
          <button 
            type="button"
            onClick={() => setMobileFilterOpen(!mobileFilterOpen)}
            className="flex items-center gap-2 text-sm font-bold text-amazon-text-primary px-3 py-1.5 bg-white border border-gray-300 rounded shadow-sm"
          >
            <Filter size={16} /> Filters {hasActiveFilters && <span className="w-2 h-2 rounded-full bg-amazon-orange" />}
          </button>
        </div>

        {/* Mobile Filter Backdrop Overlay */}
        {mobileFilterOpen && (
          <div 
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
            onClick={() => setMobileFilterOpen(false)}
          />
        )}

        <div className="max-w-[1800px] mx-auto flex relative">
          {/* Left Sidebar - Filters */}
          <div className={`w-[280px] md:w-[240px] shrink-0 bg-white z-40 p-4 border-r border-[#D5D9D9] min-h-screen ${mobileFilterOpen ? 'fixed top-0 left-0 h-full overflow-y-auto shadow-2xl z-50' : 'hidden md:block md:static md:shadow-none'}`}>
            <div className="md:hidden flex justify-between items-center mb-4 pb-2 border-b border-gray-200">
              <span className="font-bold text-base text-amazon-text-primary">Refine Search</span>
              <button onClick={() => setMobileFilterOpen(false)} className="p-1 rounded text-gray-500 hover:text-black">
                <X size={20} />
              </button>
            </div>

            {/* Shop / Merchant Filter with Debounced Autocomplete */}
            <div className="mb-6">
              <h3 className="font-bold text-amazon-text-primary mb-2 flex items-center justify-between">
                <span className="flex items-center gap-1 text-sm"><Store size={16} /> Shop / Merchant</span>
                {selectedShop && (
                  <button 
                    onClick={() => handleShopChange('')}
                    className="text-xs text-amazon-link-teal hover:underline flex items-center gap-0.5 font-normal"
                  >
                    Clear
                  </button>
                )}
              </h3>

              <div className="relative mb-2">
                <input
                  type="text"
                  placeholder="Search 100k+ shops..."
                  value={shopSearchInput}
                  onChange={(e) => setShopSearchInput(e.target.value)}
                  className="w-full px-2 py-1 pr-6 text-xs border border-[#D5D9D9] rounded focus:border-amazon-orange focus:outline-none"
                />
                {shopSearchInput ? (
                  <button onClick={() => setShopSearchInput('')} className="absolute right-1.5 top-1.5 text-gray-400 hover:text-gray-600">
                    <X size={12} />
                  </button>
                ) : (
                  <Search size={12} className="absolute right-1.5 top-1.5 text-gray-400 pointer-events-none" />
                )}
              </div>

              <ul onScroll={handleShopScroll} className="text-sm space-y-1 max-h-44 overflow-y-auto">
                <li>
                  <button
                    onClick={() => handleShopChange('')}
                    className={`text-left w-full hover:text-amazon-orange text-xs ${!selectedShop ? 'font-bold text-amazon-text-primary' : 'text-amazon-text-secondary'}`}
                  >
                    All Shops
                  </button>
                </li>
                {isSearchingShops && tenants.length === 0 ? (
                  <li className="text-xs text-gray-400 py-1">Searching shops...</li>
                ) : tenants.length === 0 ? (
                  <li className="text-xs text-gray-400 py-1">No matching shops</li>
                ) : (
                  <>
                    {tenants.map((shop) => (
                      <li key={shop.id}>
                        <button
                          onClick={() => handleShopChange(shop.id)}
                          className={`text-left w-full truncate hover:text-amazon-orange text-xs ${String(selectedShop) === String(shop.id) ? 'font-bold text-amazon-orange' : 'text-amazon-text-secondary'}`}
                          title={shop.name}
                        >
                          {shop.name}
                        </button>
                      </li>
                    ))}
                    {isSearchingShops && (
                      <li className="text-[10px] text-gray-400 py-0.5 text-center">Loading more shops...</li>
                    )}
                  </>
                )}
              </ul>
            </div>

            {/* Department & Category Filter with Instant Search & Drilldown */}
            <div className="mb-6">
              <h3 className="font-bold text-amazon-text-primary mb-2 flex items-center justify-between">
                <span className="text-sm">Department</span>
                {selectedCategory && (
                  <button 
                    onClick={() => handleCategoryChange('')}
                    className="text-xs text-amazon-link-teal hover:underline flex items-center gap-0.5 font-normal"
                  >
                    Clear
                  </button>
                )}
              </h3>

              <div className="relative mb-2">
                <input
                  type="text"
                  placeholder="Search categories..."
                  value={categorySearchInput}
                  onChange={(e) => setCategorySearchInput(e.target.value)}
                  className="w-full px-2 py-1 pr-6 text-xs border border-[#D5D9D9] rounded focus:border-amazon-orange focus:outline-none"
                />
                {categorySearchInput ? (
                  <button onClick={() => setCategorySearchInput('')} className="absolute right-1.5 top-1.5 text-gray-400 hover:text-gray-600">
                    <X size={12} />
                  </button>
                ) : (
                  <Search size={12} className="absolute right-1.5 top-1.5 text-gray-400 pointer-events-none" />
                )}
              </div>

              {categorySearchInput ? (
                /* Category Global Search Results */
                <ul onScroll={handleCategoryScroll} className="text-sm space-y-1 max-h-52 overflow-y-auto">
                  {isSearchingCategories && categorySearchResults.length === 0 ? (
                    <li className="text-xs text-gray-400 py-1">Searching categories...</li>
                  ) : categorySearchResults.length === 0 ? (
                    <li className="text-xs text-gray-400 py-1">No matching categories found</li>
                  ) : (
                    <>
                      {categorySearchResults.map((cat) => (
                        <li key={cat.id}>
                          <button
                            onClick={() => {
                              if (cat.parent_id || cat.parent) {
                                const parentId = cat.parent_id || (typeof cat.parent === 'object' ? cat.parent?.id : cat.parent);
                                setSelectedCategory(parentId);
                                setSelectedSubcategory(cat.id);
                                updateFilters({ category: parentId, subcategory: cat.id, search, ordering, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: selectedShop });
                              } else {
                                handleCategoryChange(cat.id);
                              }
                            }}
                            className={`text-left w-full truncate hover:text-amazon-orange text-xs ${String(selectedCategory) === String(cat.id) || String(selectedSubcategory) === String(cat.id) ? 'font-bold text-amazon-orange' : 'text-amazon-text-secondary'}`}
                            title={cat.name}
                          >
                            {cat.name} {cat.parent_name ? <span className="text-[10px] text-gray-400">({cat.parent_name})</span> : ''}
                          </button>
                        </li>
                      ))}
                      {isSearchingCategories && (
                        <li className="text-[10px] text-gray-400 py-0.5 text-center">Loading more categories...</li>
                      )}
                    </>
                  )}
                </ul>
              ) : (
                /* Root Departments List */
                <ul className="text-sm space-y-1 max-h-52 overflow-y-auto">
                  <li>
                    <button
                      onClick={() => handleCategoryChange('')}
                      className={`text-left w-full hover:text-amazon-orange text-xs ${!selectedCategory ? 'font-bold text-amazon-text-primary' : 'text-amazon-text-secondary'}`}
                    >
                      Any Department
                    </button>
                  </li>
                  {categories.map((cat) => (
                    <li key={cat.id}>
                      <button
                        onClick={() => handleCategoryChange(cat.id)}
                        className={`text-left w-full truncate hover:text-amazon-orange text-xs ${String(selectedCategory) === String(cat.id) ? 'font-bold text-amazon-orange' : 'text-amazon-text-secondary'}`}
                        title={cat.name}
                      >
                        {cat.name}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Subcategory Drilldown List when Department is active */}
            {!categorySearchInput && selectedCategory && activeSubcategories.length > 0 && (
              <div className="mb-6">
                <h3 className="font-bold text-amazon-text-primary mb-2 text-xs">Subcategory</h3>
                <ul className="text-sm space-y-1 pl-2 border-l-2 border-amazon-orange max-h-44 overflow-y-auto">
                  <li>
                    <button
                      onClick={() => {
                        setSelectedSubcategory('');
                        updateFilters({ category: selectedCategory, subcategory: '', search, ordering, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: selectedShop });
                      }}
                      className={`text-left w-full hover:text-amazon-orange text-xs ${!selectedSubcategory ? 'font-bold text-amazon-text-primary' : 'text-amazon-text-secondary'}`}
                    >
                      All Subcategories
                    </button>
                  </li>
                  {activeSubcategories.map((sub) => (
                    <li key={sub.id}>
                      <button
                        onClick={() => {
                          setSelectedSubcategory(sub.id);
                          updateFilters({ category: selectedCategory, subcategory: sub.id, search, ordering, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: selectedShop });
                        }}
                        className={`text-left w-full truncate hover:text-amazon-orange text-xs ${String(selectedSubcategory) === String(sub.id) ? 'font-bold text-amazon-orange' : 'text-amazon-text-secondary'}`}
                        title={sub.name}
                      >
                        {sub.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mb-6">
              <h3 className="font-bold text-amazon-text-primary mb-2">Price</h3>
              <div className="flex items-center gap-2 text-sm mb-2">
                <input
                  type="number"
                  placeholder="Min"
                  className="w-16 px-2 py-1 border border-[#D5D9D9] rounded shadow-sm focus:outline-none focus:border-amazon-orange focus:ring-1 focus:ring-amazon-orange"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                />
                <input
                  type="number"
                  placeholder="Max"
                  className="w-16 px-2 py-1 border border-[#D5D9D9] rounded shadow-sm focus:outline-none focus:border-amazon-orange focus:ring-1 focus:ring-amazon-orange"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                />
                <button 
                  className="btn-secondary px-2 py-1 text-xs shadow-sm"
                  onClick={() => updateFilters({ category: selectedCategory, subcategory: selectedSubcategory, search, ordering, min_price: minPrice, max_price: maxPrice, available: isAvailable, collection, shop: selectedShop })}
                >
                  Go
                </button>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="font-bold text-amazon-text-primary mb-2">Availability</h3>
              <label className="flex items-center gap-2 text-sm text-amazon-text-primary cursor-pointer hover:text-amazon-orange">
                <input
                  type="checkbox"
                  checked={isAvailable}
                  onChange={(e) => {
                    setIsAvailable(e.target.checked);
                    updateFilters({ category: selectedCategory, subcategory: selectedSubcategory, search, ordering, min_price: minPrice, max_price: maxPrice, available: e.target.checked, collection, shop: selectedShop });
                  }}
                  className="w-4 h-4 text-amazon-orange focus:ring-amazon-orange border-gray-300 rounded"
                />
                In Stock Only
              </label>
            </div>
          </div>

          {/* Right Content - Product Grid */}
          <div className="flex-1 p-4 md:p-6 bg-white">
            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {Array.from({ length: pagination.pageSize }).map((_, i) => (
                  <div key={i} className="amz-card p-4 animate-pulse space-y-4 h-[400px]">
                    <div className="w-full h-48 bg-slate-100 rounded"></div>
                    <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                    <div className="h-4 bg-slate-200 rounded w-1/2"></div>
                  </div>
                ))}
              </div>
            ) : products.length === 0 ? (
              <div className="py-20 text-center">
                <h3 className="text-xl font-bold mb-2">No results for {search ? `"${search}"` : 'these filters'}</h3>
                <p className="text-amazon-text-secondary mb-4">Try checking your spelling or use more general terms</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {products.map((product) => (
                    <ProductCard
                      key={product.id}
                      product={product}
                      onAddToCart={handleAddToCart}
                      onToggleWishlist={handleToggleWishlist}
                      isWishlisted={wishlistedIds.has(String(product.id))}
                    />
                  ))}
                </div>

                <div className="mt-8 border-t border-[#D5D9D9] pt-4">
                  <Pagination
                    currentPage={pagination.page}
                    totalPages={pagination.totalPages}
                    totalItems={pagination.totalItems}
                    pageSize={pagination.pageSize}
                    onPageChange={pagination.handlePageChange}
                    onPageSizeChange={pagination.handlePageSizeChange}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  };

  return hasActiveFilters ? renderSearchLayout() : renderHomeLayout();
};
