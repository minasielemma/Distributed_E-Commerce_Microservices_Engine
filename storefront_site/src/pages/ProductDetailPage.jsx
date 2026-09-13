import React, { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { catalogService, recommendationService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { CartContext } from '../context/CartContext';
import { useToast } from '../context/ToastContext';
import { Modal, StarRating } from '../components/common/UIComponents';
import { BuyBox } from '../components/BuyBox';
import { ProductCarousel } from '../components/ProductCarousel';
import { ArrowLeft, MessageSquare, Plus, Heart } from 'lucide-react';

export const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [variants, setVariants] = useState([]);
  const [images, setImages] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [selectedVariant, setSelectedVariant] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [liked, setLiked] = useState(false);
  const [likesCount, setLikesCount] = useState(0);

  // Review modal
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  const { addToCart, addToWishlist } = useContext(CartContext);
  const { showSuccess, showError } = useToast();
  const [isAddingWishlist, setIsAddingWishlist] = useState(false);

  const [copurchaseProducts, setCopurchaseProducts] = useState([]);
  const [similarProducts, setSimilarProducts] = useState([]);
  const [recsLoading, setRecsLoading] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
    fetchProductDetails();
    // Track view in recommendation service (Option A)
    recommendationService.trackView(id).catch(() => {});
  }, [id]);

  const handleAddToWishlist = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      showError("Please sign in to save products to your wishlist.");
      return;
    }
    setIsAddingWishlist(true);
    try {
      await addToWishlist(product);
      showSuccess(`Saved "${product.name}" to your wishlist`);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setIsAddingWishlist(false);
    }
  };

  const fetchProductDetails = async () => {
    setLoading(true);
    try {
      const pRes = await catalogService.getProduct(id);
      setProduct(pRes.data);
      setLiked(pRes.data.is_liked || false);
      setLikesCount(pRes.data.likes_count || 0);

      const [vRes, imgRes, revRes] = await Promise.all([
        catalogService.getVariants({ product_id: id }).catch(() => ({ data: [] })),
        catalogService.getProductImages({ product_id: id }).catch(() => ({ data: [] })),
        catalogService.getReviews({ product_id: id }).catch(() => ({ data: [] })),
      ]);

      const getResults = (res) => (res.data?.results ? res.data.results : (res.data || []));

      const variantsData = getResults(vRes);
      const imagesData = getResults(imgRes);
      const reviewsData = getResults(revRes);

      setVariants(variantsData);
      setImages(imagesData);
      setReviews(reviewsData);

      if (variantsData.length > 0) {
        setSelectedVariant(variantsData[0]);
      }
      if (imagesData.length > 0) {
        setSelectedImage(imagesData[0].image_url);
      }

      // Fetch recommendations
      setRecsLoading(true);
      Promise.all([
        recommendationService.getCopurchase(id).catch(() => ({ data: { results: [] } })),
        recommendationService.getSimilar(id).catch(() => ({ data: { results: [] } })),
      ]).then(([coRes, simRes]) => {
        setCopurchaseProducts(coRes.data?.results || []);
        setSimilarProducts(simRes.data?.results || []);
      }).finally(() => setRecsLoading(false));

    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const getVariantLabel = (v) => {
    if (v.attribute_values_detail && v.attribute_values_detail.length > 0) {
      return v.attribute_values_detail.map((a) => a.value || a.attribute_value || a.name).join(' / ');
    }
    const skuParts = (v.sku || '').split('-');
    if (skuParts.length > 2) return skuParts.slice(-1)[0];
    return v.sku || v.name || `Option ${v.id.substring(0, 4)}`;
  };

  const handleAddToCart = async () => {
    setIsAdding(true);
    try {
      const variantPrice = selectedVariant
        ? Number(selectedVariant.price || selectedVariant.effective_price || 0) || null
        : null;
      const variantImage = selectedVariant
        ? (selectedVariant.image_url || selectedVariant.images?.[0]?.image_url || null)
        : null;
      const productWithImage = variantImage
        ? { ...product, image_url: variantImage, images: [{ image_url: variantImage }] }
        : product;
      await addToCart(productWithImage, quantity, selectedVariant?.id || null, selectedVariant ? getVariantLabel(selectedVariant) : '', variantPrice);
      showSuccess(`Added ${quantity} × "${product.name}"${ selectedVariant ? ` (${getVariantLabel(selectedVariant)})` : ''} to cart`);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setIsAdding(false);
    }
  };

  const handleBuyNow = async () => {
    await handleAddToCart();
    navigate('/cart');
  };

  const handleToggleLike = async () => {
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
      await catalogService.toggleLikeProduct(id);
      showSuccess(newLiked ? "Added to your liked products!" : "Removed from your liked products.");
    } catch (err) {
      setLiked(!newLiked);
      setLikesCount(likesCount);
      showError(getErrorMessage(err));
    }
  };

  const handleCreateReview = async (e) => {
    e.preventDefault();
    setReviewSubmitting(true);
    try {
      await catalogService.createReview({
        product: id,
        rating: reviewRating,
        review_text: reviewComment,
      });
      showSuccess('Thank you! Your review has been published.');
      setReviewModalOpen(false);
      setReviewComment('');
      fetchProductDetails();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setReviewSubmitting(false);
    }
  };

  if (loading) return (
    <div className="w-full bg-white min-h-screen p-4 md:p-6 animate-pulse max-w-[1500px] mx-auto mt-4">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-4 h-[400px] bg-slate-100 rounded"></div>
        <div className="lg:col-span-5 space-y-4">
          <div className="h-8 bg-slate-100 rounded w-3/4"></div>
          <div className="h-4 bg-slate-100 rounded w-1/2"></div>
          <div className="h-10 bg-slate-100 rounded w-1/4 mt-8"></div>
        </div>
        <div className="lg:col-span-3 h-[300px] bg-slate-100 rounded border border-[#D5D9D9]"></div>
      </div>
    </div>
  );
  if (!product) return <div className="p-16 text-center text-amazon-text-secondary min-h-screen bg-white">Product not found.</div>;

  const basePrice = Number(product.dynamic_price || product.base_price || product.price || 0);
  const displayPrice = selectedVariant ? Number(selectedVariant.price || selectedVariant.effective_price || basePrice) : basePrice;

  return (
    <div className="w-full bg-white min-h-screen pb-16">
      {/* Breadcrumb / Top Bar */}
      <div className="border-b border-[#D5D9D9] bg-white px-4 py-2 flex items-center text-sm text-amazon-text-secondary sticky top-[60px] z-30">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 hover:text-amazon-orange hover:underline text-amazon-link-teal">
          <ArrowLeft size={16} /> Back to results
        </button>
      </div>

      <div className="max-w-[1500px] mx-auto p-4 md:p-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* LEFT: Images (3 columns wide) */}
          <div className="lg:col-span-4 flex flex-col md:flex-row gap-4">
             {/* Thumbnail sidebar (hidden on mobile, shown on md+) */}
             {images.length > 1 && (
               <div className="hidden md:flex flex-col gap-2 shrink-0">
                  {images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedImage(img.image_url)}
                      className={`w-12 h-12 rounded border p-1 shrink-0 ${
                        selectedImage === img.image_url ? 'border-amazon-orange shadow-[0_0_3px_rgba(228,121,17,0.5)]' : 'border-[#D5D9D9] hover:border-amazon-text-secondary'
                      }`}
                    >
                      <img 
                        src={img.image_url} 
                        alt="" 
                        className="w-full h-full object-contain" 
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    </button>
                  ))}
               </div>
             )}
             
             {/* Main Image */}
             <div className="flex-1 bg-white rounded-lg flex items-center justify-center p-4">
                {selectedImage ? (
                  <img 
                    src={selectedImage} 
                    alt={product.name} 
                    className="w-full h-auto max-h-[500px] object-contain" 
                  />
                ) : (
                  <div className="w-full h-[400px] bg-slate-50 flex items-center justify-center text-amazon-text-secondary border border-dashed border-[#D5D9D9] rounded">
                    No image available
                  </div>
                )}
             </div>

             {/* Mobile Thumbnails */}
             {images.length > 1 && (
               <div className="flex md:hidden gap-2 overflow-x-auto pb-2">
                  {images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedImage(img.image_url)}
                      className={`w-12 h-12 rounded border p-1 shrink-0 ${
                        selectedImage === img.image_url ? 'border-amazon-orange shadow-[0_0_3px_rgba(228,121,17,0.5)]' : 'border-[#D5D9D9]'
                      }`}
                    >
                      <img 
                        src={img.image_url} 
                        alt="" 
                        className="w-full h-full object-contain" 
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    </button>
                  ))}
               </div>
             )}
          </div>

          {/* CENTER: Product Details (5 columns wide) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="border-b border-[#D5D9D9] pb-4">
              <h1 className="text-2xl font-bold text-amazon-text-primary leading-tight mb-2">
                {product.name}
              </h1>
              
              <div className="flex items-center justify-between flex-wrap gap-2 text-sm">
                <div className="flex items-center gap-4">
                  <span className="text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
                    Visit the {product.tenant_name || 'Apex'} Store
                  </span>
                  <div className="flex items-center gap-1">
                    <StarRating rating={Math.round(product.average_rating || 0)} size="w-4 h-4" />
                    <span className="text-amazon-link-teal hover:text-amazon-orange hover:underline cursor-pointer">
                      {product.reviews_count || reviews.length} ratings
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleToggleLike}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#D5D9D9] hover:border-red-400 bg-white text-xs font-medium text-slate-700 hover:text-red-500 transition-colors shadow-sm cursor-pointer"
                  title={liked ? "Unlike product" : "Like product"}
                >
                  <Heart className={`w-4 h-4 ${liked ? 'fill-red-500 text-red-500' : 'text-slate-400'}`} />
                  <span>{liked ? 'Liked' : 'Like'}</span>
                  {likesCount > 0 && <span className="font-bold text-slate-900">({likesCount})</span>}
                </button>
              </div>
            </div>

            {/* Price block */}
            <div className="py-2">
              <div className="flex items-start text-3xl text-amazon-text-primary">
                <span className="text-sm font-medium mt-1">$</span>
                <span className="font-semibold">{Math.floor(displayPrice)}</span>
                <span className="text-sm font-medium mt-1">{(Number(displayPrice) % 1).toFixed(2).substring(2)}</span>
              </div>
              <div className="text-sm text-amazon-text-secondary mt-1">
                <span>FREE Returns</span>
              </div>
            </div>

            {/* Variants Selector */}
            {variants.length > 0 && (
              <div className="space-y-3 py-2 border-t border-[#D5D9D9] pt-4">
                <div className="text-sm flex items-center gap-2">
                  <span className="text-amazon-text-secondary">Option:</span>{' '}
                  <span className="font-bold">{selectedVariant ? getVariantLabel(selectedVariant) : ''}</span>
                  {selectedVariant && Number(selectedVariant.price) !== basePrice && (
                    <span className="text-xs text-[#565959] ml-1">
                      — ${Number(selectedVariant.price).toLocaleString()}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {variants.map((v) => {
                    const isSelected = selectedVariant?.id === v.id;
                    const vImg = v.image_url || v.images?.[0]?.image_url || images.find((i) => i.variant === v.id)?.image_url;
                    const label = getVariantLabel(v);
                    const vPrice = Number(v.price || v.effective_price || 0);

                    return (
                      <button
                        key={v.id}
                        onClick={() => {
                          setSelectedVariant(v);
                          if (vImg) setSelectedImage(vImg);
                        }}
                        className={`flex items-center gap-2 p-1.5 border rounded transition-all ${
                          isSelected
                            ? 'border-amazon-orange shadow-[0_0_4px_rgba(228,121,17,0.4)] bg-orange-50'
                            : 'border-[#D5D9D9] hover:border-[#888] bg-white'
                        } ${v.stock === 0 ? 'opacity-40 cursor-not-allowed' : ''}`}
                        disabled={v.stock === 0}
                        title={v.stock === 0 ? 'Out of stock' : `${label} — $${vPrice.toLocaleString()}`}
                      >
                        {vImg && (
                          <div className="w-10 h-10 shrink-0 bg-white border border-[#eee] rounded">
                            <img src={vImg} alt={label} className="w-full h-full object-contain" onError={(e) => { e.target.style.display='none'; }} />
                          </div>
                        )}
                        <div className="flex flex-col items-start px-1">
                          <span className="text-xs font-medium">{label}</span>
                          {vPrice > 0 && vPrice !== basePrice && (
                            <span className="text-[10px] text-[#565959]">${vPrice.toLocaleString()}</span>
                          )}
                          {v.stock === 0 && <span className="text-[9px] text-red-500">Out of stock</span>}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Description list */}
            <div className="border-t border-[#D5D9D9] pt-4">
              <h3 className="font-bold text-amazon-text-primary mb-2 text-base">About this item</h3>
              <ul className="list-disc pl-5 text-sm text-amazon-text-primary space-y-1.5 leading-relaxed">
                {typeof product.description === 'string' ? (
                  product.description.split('\n').filter(Boolean).map((line, i) => (
                    <li key={i}>{line}</li>
                  ))
                ) : (
                  <>
                    <li>High quality product from {product.tenant_name || 'our store'}.</li>
                    <li>Built with premium materials for durability and performance.</li>
                    <li>Backed by our satisfaction guarantee.</li>
                  </>
                )}
              </ul>
            </div>
          </div>

          {/* RIGHT: Buy Box (3 columns wide) */}
          <div className="lg:col-span-3">
             <BuyBox 
               product={{...product, price: displayPrice, stock: selectedVariant ? selectedVariant.stock : product.stock}}
               quantity={quantity}
               setQuantity={setQuantity}
               onAddToCart={handleAddToCart}
               onBuyNow={handleBuyNow}
               onAddToWishlist={handleAddToWishlist}
               isAdding={isAdding}
               isAddingWishlist={isAddingWishlist}
             />
          </div>
        </div>

        {/* Recommendation Carousels */}
        {copurchaseProducts.length > 0 && (
          <div className="mt-12">
            <ProductCarousel
              title="Frequently Bought Together"
              products={copurchaseProducts}
              isLoading={recsLoading}
            />
          </div>
        )}

        {similarProducts.length > 0 && (
          <div className="mt-8">
            <ProductCarousel
              title="Similar Products You May Like"
              products={similarProducts}
              isLoading={recsLoading}
            />
          </div>
        )}

        {/* Reviews Section */}
        <div className="mt-16 border-t border-[#D5D9D9] pt-8 max-w-4xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-amazon-text-primary">Customer reviews</h2>
            <button onClick={() => setReviewModalOpen(true)} className="btn-secondary text-sm">
              Write a customer review
            </button>
          </div>

          {reviews.length === 0 ? (
            <div className="bg-slate-50 p-6 rounded text-center border border-[#D5D9D9]">
              <p className="text-amazon-text-secondary">No customer reviews yet.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {reviews.map((rev) => {
                const reviewerName = typeof rev.user_name === 'string' ? rev.user_name : (typeof rev.user === 'object' ? (rev.user?.first_name || rev.user?.username) : rev.user) || 'Customer';
                return (
                <div key={rev.id} className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-amazon-text-primary font-bold">
                      {reviewerName[0]?.toUpperCase() || 'C'}
                    </div>
                    <span className="text-sm font-medium text-amazon-text-primary">{reviewerName}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <StarRating rating={rev.rating} size="w-4 h-4" />
                    {rev.title && <span className="text-sm font-bold text-amazon-text-primary">{rev.title}</span>}
                  </div>

                  <div className="text-sm text-amazon-text-secondary">
                    Reviewed on {new Date(rev.created_at || Date.now()).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                  </div>

                  {rev.is_verified_purchase && (
                    <div className="text-xs font-bold text-amazon-orange">Verified Purchase</div>
                  )}

                  <p className="text-sm text-amazon-text-primary leading-relaxed mt-2">
                    {rev.review_text || rev.comment}
                  </p>
                </div>
              )})}
            </div>
          )}
        </div>
      </div>

      {/* Write Review Modal */}
      <Modal
        isOpen={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Create Review"
      >
        <form onSubmit={handleCreateReview} className="space-y-4 p-4">
          <div>
            <label className="block text-sm font-bold text-amazon-text-primary mb-2">Overall rating</label>
            <StarRating
              rating={reviewRating}
              interactive
              onRatingChange={(r) => setReviewRating(r)}
              size="w-8 h-8"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-amazon-text-primary mb-1">Add a written review</label>
            <textarea
              rows={4}
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              placeholder="What did you like or dislike? What did you use this product for?"
              required
              className="w-full border border-[#D5D9D9] rounded p-3 text-sm text-amazon-text-primary focus:outline-none focus:border-amazon-orange focus:ring-1 focus:ring-amazon-orange shadow-inner"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-[#D5D9D9]">
            <button type="button" onClick={() => setReviewModalOpen(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={reviewSubmitting} className="btn-primary">
              {reviewSubmitting ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
