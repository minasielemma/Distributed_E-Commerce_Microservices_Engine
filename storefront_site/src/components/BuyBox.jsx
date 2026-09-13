import React from 'react';
import { Lock, MapPin } from 'lucide-react';
import { Badge } from './common/UIComponents';

export const BuyBox = ({ product, quantity, setQuantity, onAddToCart, onBuyNow, onAddToWishlist, isAdding, isAddingWishlist }) => {
  const price = parseFloat(product.price);
  const stock = product.stock || 0;
  
  return (
    <div className="border border-[#D5D9D9] rounded-lg p-4 bg-white shadow-sm flex flex-col">
      <div className="text-2xl font-normal mb-2">
        <span className="text-sm align-top">$</span>
        {Math.floor(price)}
        <span className="text-sm align-top">{(price % 1).toFixed(2).substring(2)}</span>
      </div>
      
      <div className="text-sm text-amazon-text-secondary mb-3">
        <span>FREE Returns</span>
      </div>

      <div className="text-sm mb-4">
        <div className="flex items-start gap-1">
          <MapPin className="w-4 h-4 text-amazon-text-secondary mt-0.5 shrink-0" />
          <span className="text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
            Deliver to {product.tenant_name || 'Select address'}
          </span>
        </div>
      </div>

      <div className={`mb-4 text-lg font-medium ${stock > 0 ? 'text-amazon-stock-green' : 'text-amazon-deal-red'}`}>
        {stock > 0 ? 'In Stock' : 'Currently unavailable.'}
      </div>

      {stock > 0 && (
        <>
          <div className="mb-4">
            <label className="text-sm mr-2 shadow-sm rounded-lg border border-[#D5D9D9] bg-[#F0F2F2] hover:bg-[#E3E6E6] px-2 py-1 cursor-pointer">
              Qty: 
              <select 
                value={quantity} 
                onChange={e => setQuantity(Number(e.target.value))}
                className="bg-transparent outline-none ml-1 cursor-pointer"
              >
                {[...Array(Math.min(10, stock)).keys()].map(n => (
                  <option key={n+1} value={n+1}>{n+1}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="flex flex-col gap-2 mb-4">
            <button 
              onClick={onAddToCart}
              disabled={isAdding}
              className="btn-cart w-full text-sm rounded-full py-2 shadow-sm"
            >
              {isAdding ? 'Adding...' : 'Add to Cart'}
            </button>
            <button 
              onClick={onBuyNow}
              disabled={isAdding}
              className="btn-buy-now w-full text-sm rounded-full py-2 shadow-sm"
            >
              Buy Now
            </button>
          </div>
        </>
      )}

      <div className="flex items-center gap-2 text-amazon-text-secondary text-sm mb-4">
        <Lock className="w-4 h-4" />
        <span className="text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
          Secure transaction
        </span>
      </div>

      <div className="text-xs text-amazon-text-secondary space-y-1 border-b border-[#D5D9D9] pb-4 mb-4">
        <div className="grid grid-cols-[80px_1fr] gap-2">
          <span>Ships from</span>
          <span>Apex.com</span>
        </div>
        <div className="grid grid-cols-[80px_1fr] gap-2">
          <span>Sold by</span>
          <span className="text-amazon-link-teal">{product.tenant_name || 'Apex Store'}</span>
        </div>
        <div className="grid grid-cols-[80px_1fr] gap-2">
          <span>Returns</span>
          <span className="text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
            Eligible for Return, Refund or Replacement within 30 days of receipt
          </span>
        </div>
      </div>
      
      {/* Add to List button */}
      <button 
        onClick={onAddToWishlist}
        disabled={isAddingWishlist}
        className="btn-secondary w-full text-sm mt-auto shadow-sm py-2 flex items-center justify-center gap-2"
      >
        {isAddingWishlist ? 'Saving...' : 'Add to List'}
      </button>
    </div>
  );
};
