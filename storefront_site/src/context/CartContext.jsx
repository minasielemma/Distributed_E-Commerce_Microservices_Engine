import React, { createContext, useState, useEffect, useContext } from 'react';
import { cartService } from '../services/apiServices';
import { AuthContext } from './AuthContext';

export const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const { token } = useContext(AuthContext);
  const [cart, setCart] = useState(null);
  const [wishlist, setWishlist] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      fetchCartAndWishlist();
    } else {
      setCart(null);
      setWishlist(null);
    }
  }, [token]);

  const fetchCartAndWishlist = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const cartRes = await cartService.getCarts().catch(() => null);
      const carts = cartRes?.data?.results || cartRes?.data;
      if (carts && carts.length > 0) {
        setCart(carts[0]);
      } else {
        setCart({ items: [] });
      }

      const wlRes = await cartService.getWishlists().catch(() => null);
      const wishlists = wlRes?.data?.results || wlRes?.data;
      if (wishlists && wishlists.length > 0) {
        setWishlist(wishlists[0]);
      } else {
        setWishlist({ items: [] });
      }
    } catch (err) {
      console.error('Error fetching cart/wishlist:', err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product, quantity = 1, variant_id = null, variant_name = '', price = null) => {
    const resolvedPrice = price ?? product.dynamic_price ?? product.base_price ?? product.price ?? 0;
    const image_url = product.images?.[0]?.image_url || product.image_url || '';
    const res = await cartService.addItemToCart(product.id, quantity, resolvedPrice, variant_id, product.name, image_url, variant_name);
    await fetchCartAndWishlist();
    return res.data;
  };

  const removeFromCart = async (itemId) => {
    const res = await cartService.removeItemFromCart(itemId);
    await fetchCartAndWishlist();
    return res.data;
  };

  const updateQuantity = async (itemId, quantity) => {
    const res = await cartService.updateItemQuantity(itemId, quantity);
    await fetchCartAndWishlist();
    return res.data;
  };

  const applyCartCoupon = async (couponCode) => {
    const res = await cartService.applyCoupon(couponCode);
    await fetchCartAndWishlist();
    return res.data;
  };

  const addToWishlist = async (product, note = '') => {
    if (!token) {
      throw new Error("Please sign in to save products to your wishlist.");
    }
    const product_name = product.name || `Product ${product.id}`;
    const image_url = product.images?.[0]?.image_url || product.image_url || '';
    const price = product.dynamic_price || product.base_price || product.price || 0;
    const res = await cartService.addItemToWishlist(product.id, note || `Saved ${product_name}`, product_name, image_url, price);
    await fetchCartAndWishlist();
    return res.data;
  };

  const removeFromWishlist = async (itemId) => {
    const res = await cartService.removeItemFromWishlist(itemId);
    await fetchCartAndWishlist();
    return res.data;
  };

  const cartItemCount = (cart?.items || []).reduce((acc, item) => acc + (item.quantity || 1), 0);
  const wishlistCount = (wishlist?.items || []).length;

  return (
    <CartContext.Provider
      value={{
        cart,
        wishlist,
        cartItemCount,
        wishlistCount,
        addToCart,
        removeFromCart,
        updateQuantity,
        applyCartCoupon,
        addToWishlist,
        removeFromWishlist,
        refreshCart: fetchCartAndWishlist,
        loading,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};
