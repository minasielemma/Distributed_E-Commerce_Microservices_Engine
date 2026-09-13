import React, { useContext, useState, useEffect } from 'react';
import { CartContext } from '../context/CartContext';
import { orderService, authService, catalogService, cartService, recommendationService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { ProductCarousel } from '../components/ProductCarousel';
import { ShoppingBag, Tag, MapPin, CheckCircle, PlusCircle } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const EMPTY_ADDRESS = {
  full_name: '', address_line_1: '', address_line_2: '',
  city: '', state: '', postal_code: '', country: 'US', phone_number: '',
};

export const CartPage = () => {
  const { cart, removeFromCart, refreshCart, updateQuantity } = useContext(CartContext);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [couponCode, setCouponCode] = useState('');
  const [discountAmount, setDiscountAmount] = useState(0);
  const [appliedCoupon, setAppliedCoupon] = useState(null);
  const [couponLoading, setCouponLoading] = useState(false);

  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState('');
  const [manualAddress, setManualAddress] = useState({ ...EMPTY_ADDRESS });
  const [useManual, setUseManual] = useState(false);

  const [cartRecommendations, setCartRecommendations] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);

  const { showSuccess, showError } = useToast();
  const navigate = useNavigate();

  const items = cart?.items || [];
  const subtotal = items.reduce((acc, i) => acc + (parseFloat(i.price || 0) * (i.quantity || 1)), 0);
  const totalItemsCount = items.reduce((acc, i) => acc + (i.quantity || 1), 0);
  const finalTotal = Math.max(0, subtotal - discountAmount).toFixed(2);

  useEffect(() => {
    authService.getAddresses()
      .then((res) => {
        const addrs = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
        setAddresses(addrs);
        const defaultAddr = addrs.find((a) => a.is_default) || addrs[0];
        if (defaultAddr) setSelectedAddressId(defaultAddr.id);
        if (addrs.length === 0) setUseManual(true);
      })
      .catch(() => setUseManual(true));
  }, []);

  useEffect(() => {
    if (items.length > 0) {
      setRecsLoading(true);
      const firstProdId = items[0].product_id;
      recommendationService.getCopurchase(firstProdId, { limit: 10 })
        .then((res) => setCartRecommendations(res.data?.results || []))
        .catch(() => {})
        .finally(() => setRecsLoading(false));
    } else {
      recommendationService.getPersonalized({ limit: 10 })
        .then((res) => setCartRecommendations(res.data?.results || []))
        .catch(() => {});
    }
  }, [items]);

  const handleApplyCoupon = async (e) => {
    e.preventDefault();
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    try {
      const res = await catalogService.validateCoupon(couponCode, subtotal);
      if (res.data?.valid) {
        setDiscountAmount(Number(res.data.discount_amount || 0));
        setAppliedCoupon(couponCode);
        showSuccess(`Coupon '${couponCode}' applied! Saved $${res.data.discount_amount}`);
      } else {
        showError(res.data?.message || 'Invalid coupon code');
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setCouponLoading(false);
    }
  };

  const getShippingAddress = () => {
    if (useManual) {
      return {
        full_name: manualAddress.full_name,
        address_line_1: manualAddress.address_line_1,
        address_line_2: manualAddress.address_line_2 || '',
        city: manualAddress.city,
        state: manualAddress.state || '',
        postal_code: manualAddress.postal_code || '',
        country: manualAddress.country,
        phone_number: manualAddress.phone_number || '',
      };
    }
    const sa = addresses.find((a) => String(a.id) === String(selectedAddressId));
    if (!sa) return null;
    return {
      full_name: sa.full_name || sa.title || 'Customer',
      address_line_1: sa.address_line_1 || sa.street || '',
      address_line_2: sa.address_line_2 || '',
      city: sa.city || '',
      state: sa.state || '',
      postal_code: sa.postal_code || '',
      country: sa.country || 'US',
      phone_number: sa.phone_number || '',
    };
  };

  const handleCheckout = async () => {
    if (items.length === 0) return;

    const shippingAddress = getShippingAddress();
    if (!shippingAddress) {
      showError('Please select or enter a shipping address before checkout.');
      return;
    }

    // Validate required fields
    const missing = ['full_name', 'address_line_1', 'city', 'country'].filter(
      (f) => !String(shippingAddress[f] || '').trim()
    );
    if (missing.length > 0) {
      showError(`Shipping address is missing: ${missing.join(', ')}. Please complete your address.`);
      return;
    }

    setCheckoutLoading(true);
    try {
      const orderPayload = {
        items: items.map((item) => ({
          product_id: item.product_id,
          variant_id: item.variant_id || null,
          variant_sku: item.variant_name || '',
          product_name: item.product_name || `Product #${item.product_id}`,
          unit_price: Number(item.price || 0),
          quantity: item.quantity || 1,
          tenant_id: item.tenant_id || item.product?.tenant_id || null,
        })),
        discount_code: appliedCoupon || '',
        shipping_address: shippingAddress,
        billing_address: shippingAddress,
        shipping_cost: 0,
        tax_amount: 0,
      };

      const orderRes = await orderService.createOrder(orderPayload);
      const orderId = orderRes.data?.order?.id || orderRes.data?.id || orderRes.data?.order_id;

      showSuccess(`Order #${String(orderId).substring(0, 8)} created! Initiating payment...`);

      // Initiate Polar payment
      const payRes = await orderService.payOrder(orderId).catch(() => null);

      await refreshCart();

      if (payRes?.data?.checkout_url) {
        window.location.href = payRes.data.checkout_url;
      } else if (payRes?.data?.payment?.checkout_url) {
        window.location.href = payRes.data.payment.checkout_url;
      } else {
        showSuccess(`Order #${String(orderId).substring(0, 8)} placed successfully!`);
        navigate(`/checkout/success?order_id=${orderId}`);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setCheckoutLoading(false);
    }
  };

  const canCheckout = items.length > 0 && !checkoutLoading && (
    useManual
      ? !!(manualAddress.full_name && manualAddress.address_line_1 && manualAddress.city && manualAddress.country)
      : !!selectedAddressId
  );

  return (
    <div className="w-full bg-[#E3E6E6] min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-amazon-text-primary">
      <div className="max-w-[1500px] mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* Left Column: Cart Items */}
          <div className="lg:col-span-9 bg-white p-6 md:p-8">
            <div className="border-b border-[#D5D9D9] pb-2 mb-4 flex justify-between items-end">
              <h1 className="text-[28px] font-normal leading-tight">Shopping Cart</h1>
              <span className="text-sm text-amazon-text-secondary hidden sm:inline">Price</span>
            </div>

            {items.length === 0 ? (
              <div className="py-8 space-y-4">
                <p className="text-lg">Your cart is empty.</p>
                <Link to="/" className="text-amazon-link-teal hover:text-amazon-orange hover:underline">
                  Shop today's deals
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {items.map((item) => (
                  <div key={item.id} className="flex flex-col sm:flex-row gap-4 py-4 border-b border-[#D5D9D9] last:border-b-0">
                    {/* Item Image */}
                    <div className="w-full sm:w-[180px] shrink-0">
                      <Link to={`/products/${item.product_id}`}>
                        {item.image_url ? (
                          <img
                            src={item.image_url}
                            alt={item.product_name}
                            className="w-full h-auto max-h-[180px] object-contain"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <div className="w-full h-[180px] bg-slate-50 flex items-center justify-center text-amazon-text-secondary border border-dashed border-[#D5D9D9]">
                            <ShoppingBag className="w-12 h-12 opacity-20" />
                          </div>
                        )}
                      </Link>
                    </div>

                    {/* Item Details */}
                    <div className="flex-1 space-y-1">
                      <div className="flex justify-between items-start gap-4">
                        <Link to={`/products/${item.product_id}`} className="text-lg font-medium text-amazon-link-teal hover:text-amazon-orange hover:underline line-clamp-2">
                          {item.product_name || `Product SKU: ${item.product_id}`}
                        </Link>
                        <div className="font-bold text-lg sm:hidden">
                          ${Number(item.price || 0).toFixed(2)}
                        </div>
                      </div>

                      <div className="text-sm text-amazon-stock-green">In Stock</div>

                      <div className="flex items-center gap-1 text-xs">
                        <input type="checkbox" className="mr-1" />
                        This is a gift <span className="text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline">Learn more</span>
                      </div>

                      {item.variant_id && (
                        <div className="text-sm text-amazon-text-secondary">
                          <span className="font-bold">Variant:</span> {item.variant_name || item.variant_id}
                        </div>
                      )}

                      <div className="flex items-center gap-4 pt-3">
                        <div className="flex items-center shadow-sm rounded-lg border border-[#D5D9D9] bg-[#F0F2F2] hover:bg-[#E3E6E6] px-2 py-1">
                          <label className="text-sm mr-2 cursor-pointer">Qty:</label>
                          <select
                            value={item.quantity}
                            onChange={(e) => updateQuantity && updateQuantity(item.id, Number(e.target.value))}
                            className="bg-transparent outline-none cursor-pointer text-sm"
                          >
                            {[...Array(10).keys()].map(n => (
                              <option key={n+1} value={n+1}>{n+1}</option>
                            ))}
                          </select>
                        </div>

                        <div className="h-4 w-[1px] bg-[#D5D9D9]"></div>

                        <button
                          onClick={() => removeFromCart(item.id)}
                          className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline"
                        >
                          Delete
                        </button>

                        <div className="h-4 w-[1px] bg-[#D5D9D9]"></div>

                        <button
                          onClick={async () => {
                            try {
                              await cartService.addItemToWishlist(item.product_id, `Saved for later`);
                              await removeFromCart(item.id);
                              showSuccess(`Saved "${item.product_name || 'item'}" for later`);
                            } catch (err) {
                              showError(getErrorMessage(err) || 'Failed to save item for later');
                            }
                          }}
                          className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline"
                        >
                          Save for later
                        </button>
                      </div>
                    </div>

                    {/* Price Column (desktop) */}
                    <div className="hidden sm:block text-right w-[100px] shrink-0 font-bold text-lg">
                      ${Number(item.price || 0).toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {items.length > 0 && (
              <div className="text-right pt-4 text-lg">
                <span>Subtotal ({totalItemsCount} item{totalItemsCount !== 1 && 's'}): </span>
                <span className="font-bold">${subtotal.toFixed(2)}</span>
              </div>
            )}
          </div>

          {/* Right Column: Checkout Box */}
          <div className="lg:col-span-3 space-y-4">
            <div className="bg-white p-4">
              <div className="flex items-start gap-2 mb-4 text-sm text-amazon-stock-green">
                <CheckCircle className="w-5 h-5 shrink-0 mt-0.5 text-amazon-stock-green" />
                <span>
                  Your order qualifies for FREE Shipping. <span className="text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline">See details</span>
                </span>
              </div>

              <div className="text-lg mb-1">
                <span>Subtotal ({totalItemsCount} item{totalItemsCount !== 1 && 's'}): </span>
                <span className="font-bold">${subtotal.toFixed(2)}</span>
              </div>

              {discountAmount > 0 && (
                <div className="text-sm text-amazon-stock-green mb-2">
                  Discount applied: -${discountAmount.toFixed(2)}
                </div>
              )}

              {discountAmount > 0 && (
                <div className="text-base font-bold mb-4">
                  Total: ${finalTotal}
                </div>
              )}

              <div className="flex items-center gap-2 mb-4 text-sm">
                <input type="checkbox" className="w-4 h-4 cursor-pointer" />
                <label>This order contains a gift</label>
              </div>

              <button
                onClick={handleCheckout}
                disabled={!canCheckout}
                className="btn-buy-now w-full py-2 shadow-sm rounded-lg mb-4 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {checkoutLoading ? 'Processing...' : 'Proceed to checkout'}
              </button>

              {/* Shipping Address Section */}
              <div className="space-y-2 pt-2 border-t border-[#D5D9D9]">
                <div className="flex items-center justify-between mt-2">
                  <label className="text-xs flex items-center gap-1 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-amazon-text-secondary" />
                    Deliver to
                  </label>
                  {addresses.length > 0 && (
                    <button
                      onClick={() => setUseManual(!useManual)}
                      className="text-xs text-amazon-link-teal hover:text-amazon-orange hover:underline flex items-center gap-1"
                    >
                      <PlusCircle className="w-3 h-3" />
                      {useManual ? 'Use saved' : 'New address'}
                    </button>
                  )}
                </div>

                {!useManual && addresses.length > 0 ? (
                  <select
                    value={selectedAddressId}
                    onChange={(e) => setSelectedAddressId(e.target.value)}
                    className="w-full border border-[#D5D9D9] rounded bg-[#F0F2F2] px-2 py-1 text-xs focus:outline-none focus:border-amazon-orange"
                  >
                    <option value="">-- Select address --</option>
                    {addresses.map((a) => (
                      <option key={a.id} value={String(a.id)}>
                        {a.title || 'Address'}: {a.address_line_1 || a.street}, {a.city}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="space-y-1.5">
                    {[
                      { key: 'full_name', label: 'Full Name *', type: 'text' },
                      { key: 'address_line_1', label: 'Address Line 1 *', type: 'text' },
                      { key: 'address_line_2', label: 'Address Line 2', type: 'text' },
                      { key: 'city', label: 'City *', type: 'text' },
                      { key: 'state', label: 'State / Province', type: 'text' },
                      { key: 'postal_code', label: 'Postal Code', type: 'text' },
                      { key: 'country', label: 'Country *', type: 'text' },
                      { key: 'phone_number', label: 'Phone', type: 'tel' },
                    ].map(({ key, label, type }) => (
                      <input
                        key={key}
                        type={type}
                        value={manualAddress[key]}
                        onChange={(e) => setManualAddress(prev => ({ ...prev, [key]: e.target.value }))}
                        placeholder={label}
                        className="w-full border border-[#D5D9D9] rounded px-2 py-1 text-xs focus:outline-none focus:border-amazon-orange"
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Coupon Code Input */}
              <form onSubmit={handleApplyCoupon} className="flex gap-2 mt-4">
                <input
                  type="text"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  placeholder="Gift Cards & promotional codes"
                  className="flex-1 border border-[#D5D9D9] rounded px-2 py-1 text-xs focus:outline-none focus:border-amazon-orange shadow-inner"
                />
                <button
                  type="submit"
                  disabled={couponLoading || !couponCode.trim()}
                  className="bg-white border border-[#D5D9D9] hover:bg-[#F0F2F2] rounded text-xs px-3 py-1 disabled:opacity-40 shadow-sm transition-colors"
                >
                  {couponLoading ? '...' : 'Apply'}
                </button>
              </form>
            </div>

            {cartRecommendations.length > 0 && (
              <div className="mt-4">
                <ProductCarousel
                  title="Customers who bought items in your cart also bought"
                  products={cartRecommendations}
                  isLoading={recsLoading}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
