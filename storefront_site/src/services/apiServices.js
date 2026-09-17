import api from './api';

// --- AUTH & IDENTITY SERVICE ---
export const authService = {
  login: (credentials) => api.post('/auth/token/', credentials),
  register: (userData) => api.post('/auth/register/', userData),
  refreshToken: (refresh) => api.post('/auth/token/refresh/', { refresh }),
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.put('/auth/profile/', data),
  patchProfile: (data) => api.patch('/auth/profile/', data),
  
  // Addresses
  getAddresses: (params = {}) => api.get('/auth/addresses/', { params }),
  createAddress: (data) => api.post('/auth/addresses/', data),
  updateAddress: (id, data) => api.put(`/auth/addresses/${id}/`, data),
  patchAddress: (id, data) => api.patch(`/auth/addresses/${id}/`, data),
  deleteAddress: (id) => api.delete(`/auth/addresses/${id}/`),
  
  // Notifications
  getNotifications: (params = {}) => api.get('/notifications/', { params }),
  markNotificationRead: (id) => api.post(`/notifications/${id}/mark_read/`),
  deleteNotification: (id) => api.delete(`/notifications/${id}/`),

  // Activity Logs
  getActivityLogs: (params = {}) => api.get('/auth/activity/', { params }),
  
  // Tenant Management
  getTenants: (params = {}) => api.get('/auth/tenant/list/', { params: { scope: 'active', ...params } }),

  createTenant: (data) => api.post('/auth/tenant/create/', data),
  configureTenantSubscription: (tenantId, data) => api.put(`/auth/admin/tenants/${tenantId}/configure-subscription/`, data),
};

export const notificationService = {
  getNotifications: (params = {}) => api.get('/notifications/', { params }),
  markNotificationRead: (id) => api.post(`/notifications/${id}/mark_read/`),
  markAllRead: () => api.post('/notifications/mark_all_read/'),
  getUnreadCount: (params = {}) => api.get('/notifications/unread_count/'),
  deleteNotification: (id) => api.delete(`/notifications/${id}/`),
};

// --- CATALOG SERVICE ---
export const catalogService = {
  // Products (Storefront public read vs Admin portal CRUD)
  getProducts: (params = {}) => api.get('/catalog/storefront/products/', { params }),
  getProduct: (id) => api.get(`/catalog/storefront/products/${id}/`),
  createProduct: (data) => api.post('/catalog/products/', data),
  updateProduct: (id, data) => api.put(`/catalog/products/${id}/`, data),
  patchProduct: (id, data) => api.patch(`/catalog/products/${id}/`, data),
  deleteProduct: (id) => api.delete(`/catalog/products/${id}/`),
  toggleLikeProduct: (id) => api.post(`/catalog/products/${id}/like/`),
  getDeals: (params = {}) => api.get('/catalog/products/deals/', { params }),
  getBestsellers: (params = {}) => api.get('/catalog/products/bestsellers/', { params }),
  getNewArrivals: (params = {}) => api.get('/catalog/products/new-arrivals/', { params }),
  
  // Categories
  getCategories: (params = {}) => api.get('/catalog/storefront/categories/', { params }),
  createCategory: (data) => api.post('/catalog/categories/', data),
  updateCategory: (id, data) => api.put(`/catalog/categories/${id}/`, data),
  deleteCategory: (id) => api.delete(`/catalog/categories/${id}/`),
  
  // Discounts
  getDiscounts: (params = {}) => api.get('/catalog/discounts/', { params }),
  createDiscount: (data) => api.post('/catalog/discounts/', data),
  updateDiscount: (id, data) => api.put(`/catalog/discounts/${id}/`, data),
  deleteDiscount: (id) => api.delete(`/catalog/discounts/${id}/`),
  
  // Attributes & Values
  getAttributes: (params = {}) => api.get('/catalog/attributes/', { params }),
  createAttribute: (data) => api.post('/catalog/attributes/', data),
  deleteAttribute: (id) => api.delete(`/catalog/attributes/${id}/`),
  
  getAttributeValues: (params = {}) => api.get('/catalog/attribute-values/', { params }),
  createAttributeValue: (data) => api.post('/catalog/attribute-values/', data),
  deleteAttributeValue: (id) => api.delete(`/catalog/attribute-values/${id}/`),
  
  // Variants
  getVariants: (params = {}) => api.get('/catalog/variants/', { params }),
  createVariant: (data) => api.post('/catalog/variants/', data),
  updateVariant: (id, data) => api.put(`/catalog/variants/${id}/`, data),
  deleteVariant: (id) => api.delete(`/catalog/variants/${id}/`),
  
  // Images
  getProductImages: (params = {}) => api.get('/catalog/images/', { params }),
  createProductImage: (data) => api.post('/catalog/images/', data),
  deleteProductImage: (id) => api.delete(`/catalog/images/${id}/`),
  
  // Reviews
  getReviews: (params = {}) => api.get('/catalog/reviews/', { params }),
  createReview: (data) => api.post('/catalog/reviews/', data),
  updateReview: (id, data) => api.put(`/catalog/reviews/${id}/`, data),
  deleteReview: (id) => api.delete(`/catalog/reviews/${id}/`),
  
  // Coupons
  getCoupons: (params = {}) => api.get('/catalog/coupons/', { params }),
  createCoupon: (data) => api.post('/catalog/coupons/', data),
  updateCoupon: (id, data) => api.put(`/catalog/coupons/${id}/`, data),
  deleteCoupon: (id) => api.delete(`/catalog/coupons/${id}/`),
  validateCoupon: (code, order_subtotal = 0) => api.post('/catalog/coupons/validate/', { code, order_subtotal }),
};

// --- CART & WISHLIST SERVICE ---
export const cartService = {
  // Carts
  getCarts: (params = {}) => api.get('/cart/carts/', { params }),
  addItemToCart: (product_id, quantity = 1, price = 0, variant_id = null, product_name = '', image_url = '', variant_name = '') => 
    api.post('/cart/carts/add-item/', { product_id, quantity, price, variant_id, product_name, image_url, variant_name }),
  removeItemFromCart: (item_id) => 
    api.post('/cart/carts/remove-item/', { item_id }),
  updateItemQuantity: (item_id, quantity) => 
    api.post('/cart/carts/update-item/', { item_id, quantity }),
  applyCoupon: (coupon_code) => 
    api.post('/cart/carts/apply-coupon/', { coupon_code }),
  
  // Wishlists
  getWishlists: (params = {}) => api.get('/cart/wishlists/', { params }),
  addItemToWishlist: (product_id, note = '', product_name = '', image_url = '', price = 0) => 
    api.post('/cart/wishlists/add-item/', { product_id, note, product_name, image_url, price }),
  removeItemFromWishlist: (item_id) => 
    api.post('/cart/wishlists/remove-item/', { item_id }),
  
  // Item Requests
  getItemRequests: (params = {}) => api.get('/cart/item-requests/', { params }),
  createItemRequest: (data) => api.post('/cart/item-requests/', data),
  updateItemRequest: (id, data) => api.put(`/cart/item-requests/${id}/`, data),
  deleteItemRequest: (id) => api.delete(`/cart/item-requests/${id}/`),
};

// --- ORDER SERVICE ---
export const orderService = {
  createOrder: (orderData) => api.post('/orders/create/', orderData),
  payOrder: (orderId) => api.post(`/orders/${orderId}/pay/`),
  cancelOrder: (orderId) => api.post(`/orders/${orderId}/cancel/`),
  getOrders: (params = {}) => api.get('/orders/list/', { params }),
  getOrder: (id) => api.get(`/orders/${id}/`),
  getOutboxEvents: (params = {}) => api.get('/orders/outbox/', { params }),
  getShipments: (orderId) => api.get(`/orders/${orderId}/shipments/`),
  getShipmentHistory: (entityId) => api.get(`/orders/shipments/${entityId}/history/`),
  trackPackage: (trackingCode) => api.get(`/orders/track/${trackingCode}/`),
};

// --- CHAT SERVICE ---
export const chatService = {
  getRooms: (params = {}) => api.get('/chat/rooms/', { params }),
  getRoom: (id) => api.get(`/chat/rooms/${id}/`),
  createRoom: (data) => api.post('/chat/rooms/', data),
  addParticipant: (roomId, data) => api.post(`/chat/rooms/${roomId}/participants/`, data),
  removeParticipant: (roomId, userId) => api.delete(`/chat/rooms/${roomId}/participants/${userId}/`),
  sendMessage: (roomId, messageData) => api.post(`/chat/rooms/${roomId}/messages/`, messageData),
  getMessages: (roomId, params = {}) => api.get(`/chat/rooms/${roomId}/messages/`, { params }),
  getSecureFileDownloadUrl: (roomId, fileId) => `/api/chat/rooms/${roomId}/files/${fileId}/download/`,
  downloadRoomFile: (roomId, fileId) => api.get(`/chat/rooms/${roomId}/files/${fileId}/download/`, { responseType: 'blob' }),
  getUnreadCount: () => api.get('/chat/rooms/unread_count/'),
  markRead: (roomId, data = {}) => api.post(`/chat/rooms/${roomId}/mark_read/`, data),
  markDelivered: (roomId, data = {}) => api.post(`/chat/rooms/${roomId}/mark_delivered/`, data),
  toggleReaction: (roomId, data) => api.post(`/chat/rooms/${roomId}/react/`, data),
  // Backward compatibility aliases
  getConversations: (params = {}) => api.get('/chat/rooms/', { params }),
  getConversation: (id) => api.get(`/chat/rooms/${id}/`),
  createConversation: (data) => api.post('/chat/rooms/', data),
};

// --- PAYMENT SERVICE ---
export const paymentService = {
  createCheckout: (checkoutData) => api.post('/payments/checkout/', checkoutData),
  getPayments: (params = {}) => api.get('/payments/list/', { params }),
  getPayment: (id) => api.get(`/payments/${id}/`),
};

// --- INVENTORY SERVICE ---
export const inventoryService = {
  // Warehouses
  getWarehouses: (params = {}) => api.get('/inventory/warehouses/', { params }),
  createWarehouse: (data) => api.post('/inventory/warehouses/', data),
  updateWarehouse: (id, data) => api.put(`/inventory/warehouses/${id}/`, data),
  deleteWarehouse: (id) => api.delete(`/inventory/warehouses/${id}/`),
  
  // Inventory Items
  getInventoryItems: (params = {}) => api.get('/inventory/items/', { params }),
  createInventoryItem: (data) => api.post('/inventory/items/', data),
  updateInventoryItem: (id, data) => api.put(`/inventory/items/${id}/`, data),
  deleteInventoryItem: (id) => api.delete(`/inventory/items/${id}/`),
  
  // Stock actions
  addStock: (product_id, quantity, reference_id = '') =>
    api.post('/inventory/items/add-stock/', { product_id, quantity, reference_id }),
  reserveStock: (product_id, quantity, reference_id) => 
    api.post('/inventory/reserve/', { product_id, quantity, reference_id }),
  releaseStock: (product_id, quantity, reference_id) => 
    api.post('/inventory/release/', { product_id, quantity, reference_id }),
  commitStock: (product_id, quantity, reference_id) => 
    api.post('/inventory/commit/', { product_id, quantity, reference_id }),
  getMovements: (params = {}) => api.get('/inventory/movements/', { params }),
};

// --- FINANCE SERVICE ---
export const financeService = {
  // Accounts
  getAccounts: (params = {}) => api.get('/finance/accounts/', { params }),
  createAccount: (data) => api.post('/finance/accounts/', data),
  updateAccount: (id, data) => api.put(`/finance/accounts/${id}/`, data),
  deleteAccount: (id) => api.delete(`/finance/accounts/${id}/`),
  
  // Journal Entries
  getJournalEntries: (params = {}) => api.get('/finance/journal-entries/', { params }),
  createJournalEntry: (data) => api.post('/finance/journal-entries/', data),
  
  // Invoices
  getInvoices: (params = {}) => api.get('/finance/invoices/', { params }),
  getUserInvoices: (customerId) => api.get('/finance/invoices/', { params: customerId ? { customer_id: customerId } : {} }),
  createInvoice: (data) => api.post('/finance/invoices/', data),
  getInvoice: (id) => api.get(`/finance/invoices/${id}/`),
  
  // Ledger & Payouts
  getLedgerSummary: () => api.get('/finance/ledger/'),
  requestPayout: (data) => api.post('/finance/payout/', data),
  getTrialBalance: () => api.get('/finance/trial-balance/'),
};

// --- MEDIA SERVICE ---
export const mediaService = {
  uploadFile: (formData) => api.post('/media/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getFiles: (params = {}) => api.get('/media/files/', { params }),
  getFile: (id) => api.get(`/media/files/${id}/`),
  deleteFile: (id) => api.delete(`/media/files/${id}/`),
  downloadFile: (id) => api.get(`/media/files/${id}/download/`, { responseType: 'blob' }),
  shareFile: (id, shareData) => api.post(`/media/files/${id}/share/`, shareData),
};

// --- RECOMMENDATION SERVICE ---
export const recommendationService = {
  getPersonalized: (params = {}) => api.get('/recommendations/personalized/', { params }),
  getCopurchase: (productId, params = {}) => api.get('/recommendations/copurchase/', { params: { product_id: productId, ...params } }),
  getSimilar: (productId, params = {}) => api.get('/recommendations/similar/', { params: { product_id: productId, ...params } }),
  getTrending: (params = {}) => api.get('/recommendations/trending/', { params }),
  getRecommendedShops: (params = {}) => api.get('/recommendations/merchants/', { params }),
  getRecommendedCategories: (params = {}) => api.get('/recommendations/categories/', { params }),
  trackView: (productId, tenantId = null) => api.post('/recommendations/track-view/', { product_id: productId, tenant_id: tenantId }),
};
