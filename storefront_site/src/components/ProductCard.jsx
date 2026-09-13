import React, { useState } from 'react';
import { Star, AlertCircle, ShoppingCart, Heart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useToast } from '../context/ToastContext';
import { catalogService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';

export const ProductCard = ({ product, onAddToCart, onToggleWishlist, isWishlisted = false }) => {
  const { showSuccess, showError } = useToast();
  const [imageError, setImageError] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [liked, setLiked] = useState(product.is_liked || false);
  const [likesCount, setLikesCount] = useState(product.likes_count || 0);

  const basePrice = parseFloat(product.base_price || product.price_detail?.base_price || 0);
  
  // Calculate discount if available
  let finalPrice = basePrice;
  let hasDiscount = false;
  let discountPercent = 0;

  const activeDiscount = product.discounts?.[0] || product.price_detail?.active_discount;
  if (activeDiscount) {
    hasDiscount = true;
    if (activeDiscount.discount_type === 'PERCENTAGE') {
      discountPercent = Math.round(activeDiscount.discount_value);
      finalPrice = basePrice * (1 - discountPercent / 100);
    } else if (activeDiscount.discount_type === 'FIXED') {
      finalPrice = Math.max(0, basePrice - parseFloat(activeDiscount.discount_value));
      discountPercent = Math.round(((basePrice - finalPrice) / basePrice) * 100);
    }
  }

  let stockQty = 0;
  if (typeof product.stock === 'number') {
    stockQty = product.stock;
  } else if (product.inventory_item?.quantity_available !== undefined) {
    stockQty = product.inventory_item.quantity_available;
  } else if (product.variants && product.variants.length > 0) {
    stockQty = product.variants.reduce((sum, v) => sum + (typeof v.stock === 'number' ? v.stock : 0), 0);
  } else {
    stockQty = 0;
  }

  const isOutOfStock = stockQty <= 0;
  const isLowStock = stockQty > 0 && stockQty <= 5;

  const imageUrl = product.image_url || product.images?.[0]?.image_url || '';

  const hasVariants = product.variants && product.variants.length > 0;

  const handleCartClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (isOutOfStock) {
      showError("This product is currently out of stock.");
      return;
    }
    if (isAdding) return;
    setIsAdding(true);
    try {
      await onAddToCart(product, hasVariants);
    } finally {
      setIsAdding(false);
    }
  };

  const handleLikeClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    const token = localStorage.getItem('access_token');
    if (!token) {
      showError("Please log in to like products.");
      return;
    }
    const newLiked = !liked;
    const newCount = newLiked ? likesCount + 1 : Math.max(0, likesCount - 1);
    setLiked(newLiked);
    setLikesCount(newCount);
    try {
      await catalogService.toggleLikeProduct(product.id);
      showSuccess(newLiked ? "Added to your liked products!" : "Removed from your liked products.");
    } catch (err) {
      setLiked(!newLiked);
      setLikesCount(likesCount);
      showError(getErrorMessage(err));
    }
  };

  return (
    <div className="group relative bg-white border border-[#D5D9D9] rounded-sm overflow-hidden flex flex-col h-full hover:shadow-md transition-shadow">
      {/* Image Container */}
      <div className="relative w-full aspect-square bg-[#F7F7F7] p-4 flex items-center justify-center">
        {/* Like Heart Button */}
        <button
          onClick={handleLikeClick}
          className="absolute top-2 right-2 z-10 p-1.5 rounded-full bg-white/80 hover:bg-white text-slate-600 hover:text-red-500 shadow-sm border border-slate-200 transition-all flex items-center gap-1 text-xs px-2"
          title={liked ? "Unlike" : "Like"}
        >
          <Heart className={`w-4 h-4 transition-colors ${liked ? 'fill-red-500 text-red-500' : 'text-slate-400'}`} />
          {likesCount > 0 && <span className="font-semibold text-slate-700">{likesCount}</span>}
        </button>

        {imageUrl && !imageError ? (
          <Link to={`/products/${product.id}`} className="w-full h-full flex items-center justify-center">
            <img
              src={imageUrl}
              alt={product.name}
              onError={() => setImageError(true)}
              className="max-w-full max-h-full object-contain mix-blend-multiply group-hover:scale-105 transition-transform"
              loading="lazy"
            />
          </Link>
        ) : (
          <div className="flex flex-col items-center justify-center text-slate-500 w-full h-full">
            <span className="text-xs font-medium text-slate-500">No Image</span>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="p-3 flex flex-col flex-1 justify-between">
        <div>
          {/* Product Title */}
          <Link to={`/products/${product.id}`} className="hover:text-amazon-orange transition-colors">
            <h3 className="text-sm font-medium text-[#0F1111] line-clamp-2 leading-snug mb-1" title={product.name}>
              {product.name}
            </h3>
          </Link>

          {/* Rating */}
          <div className="flex items-center gap-1 mb-1">
            <div className="flex items-center">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={`w-4 h-4 ${
                    i < Math.floor(product.rating || 4.5) ? 'fill-[#FFA41C] text-[#FFA41C]' : 'text-slate-300 fill-slate-300'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
              {product.reviews_count || 12}
            </span>
          </div>
          
          {/* Sales volume or past month viewed (Optional Amazon pattern) */}
          <div className="text-xs text-amazon-text-secondary mb-2">
            1K+ bought in past month
          </div>
        </div>

        {/* Pricing & Add to Cart Action */}
        <div className="mt-auto">
          {hasDiscount ? (
            <div className="flex items-baseline gap-1 mb-1">
              <span className="text-xl font-medium text-[#CC0C39]">-{discountPercent}%</span>
              <div className="flex items-start">
                <span className="text-xs align-top mt-1">$</span>
                <span className="text-2xl font-normal">{Math.floor(finalPrice)}</span>
                <span className="text-xs align-top mt-1">{(finalPrice % 1).toFixed(2).substring(2)}</span>
              </div>
            </div>
          ) : (
             <div className="flex items-start mb-1">
                <span className="text-xs align-top mt-1">$</span>
                <span className="text-2xl font-normal">{Math.floor(finalPrice)}</span>
                <span className="text-xs align-top mt-1">{(finalPrice % 1).toFixed(2).substring(2)}</span>
            </div>
          )}
          
          {hasDiscount && (
             <div className="text-xs text-amazon-text-secondary mb-2">
               List: <span className="line-through">${basePrice.toFixed(2)}</span>
             </div>
          )}

          <div className="text-xs text-amazon-text-secondary mb-2">
            Delivery <span className="font-bold">Tomorrow</span>
            <br />
            Ships to select location
          </div>
          
          {isLowStock && !isOutOfStock && (
             <div className="text-xs text-[#B12704] font-medium mb-2">
               Only {stockQty} left in stock - order soon.
             </div>
          )}

          <button
            onClick={handleCartClick}
            disabled={isAdding}
            className={`w-full py-1.5 rounded-full font-medium text-sm transition-all shadow-sm ${
              isOutOfStock
                ? 'bg-slate-200 text-slate-500 border border-[#D5D9D9]'
                : 'btn-cart'
            }`}
          >
            {isAdding ? 'Adding...' : isOutOfStock ? 'Out of stock' : hasVariants ? 'See options' : 'Add to cart'}
          </button>
        </div>
      </div>
    </div>
  );
};
