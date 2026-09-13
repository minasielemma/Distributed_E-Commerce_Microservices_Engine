import React, { useContext } from 'react';
import { CartContext } from '../context/CartContext';
import { useToast } from '../context/ToastContext';
import { Link } from 'react-router-dom';

export const WishlistPage = () => {
  const { wishlist, removeFromWishlist, addToCart } = useContext(CartContext);
  const { showSuccess, showError } = useToast();
  const items = wishlist?.items || [];

  const handleRemove = async (itemId) => {
    try {
      await removeFromWishlist(itemId);
      showSuccess('Item removed from wishlist');
    } catch (err) {
      showError('Failed to remove item from wishlist');
    }
  };

  const handleMoveToCart = async (item) => {
    try {
      await addToCart({ id: item.product_id, name: `Product #${item.product_id}`, price: 0 });
      await removeFromWishlist(item.id);
      showSuccess('Item moved to cart!');
    } catch (err) {
      showError('Failed to move item to cart');
    }
  };

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto">
        <h1 className="text-3xl font-normal mb-6">Your Lists</h1>

        {items.length === 0 ? (
          <div className="py-8">
            <p className="text-lg">Your Wish List is empty.</p>
            <p className="text-sm mt-2">
              <Link to="/?collection=all" className="text-amazon-link-teal hover:text-amazon-orange hover:underline font-medium">
                Continue shopping
              </Link>
            </p>
          </div>
        ) : (
          <div className="border border-[#D5D9D9] rounded bg-white overflow-hidden">
            <div className="bg-[#F0F2F2] p-4 border-b border-[#D5D9D9] flex justify-between items-center">
              <h2 className="font-bold text-lg">Wish List</h2>
              <span className="text-sm text-amazon-text-secondary">{items.length} items</span>
            </div>
            
            <div className="divide-y divide-[#D5D9D9]">
              {items.map((item) => (
                <div key={item.id} className="p-4 flex flex-col md:flex-row gap-6">
                  {/* Item Image */}
                  <div className="w-full md:w-[200px] shrink-0 bg-[#F0F2F2] h-[200px] flex items-center justify-center border border-[#D5D9D9]">
                     {item.image_url ? (
                        <img src={item.image_url} alt={`Product ${item.product_id}`} className="max-w-full max-h-full object-contain mix-blend-multiply" />
                     ) : (
                        <span className="text-amazon-text-secondary text-sm block px-4 text-center">No Image<br/>Product #{item.product_id}</span>
                     )}
                  </div>

                  {/* Item Details */}
                  <div className="flex-1 flex flex-col justify-between">
                    <div>
                      <Link to={`/products/${item.product_id}`} className="text-lg font-medium text-amazon-link-teal hover:text-amazon-orange hover:underline">
                        {item.product_name || `Product #${item.product_id}`}
                      </Link>
                      {item.price > 0 && (
                        <div className="text-base font-bold text-amazon-text-primary mt-1">${Number(item.price).toFixed(2)}</div>
                      )}
                      <div className="text-sm text-amazon-stock-green mt-1">In Stock</div>
                      {item.note && (
                        <div className="text-sm text-[#565959] mt-2 italic bg-[#F0F2F2] p-2 rounded inline-block">
                          Note: "{item.note}"
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-4 mt-4">
                      <button
                        onClick={() => handleMoveToCart(item)}
                        className="btn-buy-now text-sm py-1.5 px-4 shadow-sm rounded-full w-auto"
                      >
                        Add to Cart
                      </button>
                      <button
                        onClick={() => handleRemove(item.id)}
                        className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
