import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { CountdownTimer } from './CountdownTimer';

export const ProductCarousel = ({ title, products, isLoading, seeMoreLink }) => {
  const scrollRef = useRef(null);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const { scrollLeft, clientWidth } = scrollRef.current;
      const scrollTo = direction === 'left' ? scrollLeft - clientWidth + 100 : scrollLeft + clientWidth - 100;
      scrollRef.current.scrollTo({ left: scrollTo, behavior: 'smooth' });
    }
  };

  if (isLoading) {
    return (
      <div className="amz-card p-4 my-4 h-[350px] animate-pulse">
        <div className="h-6 bg-slate-200 w-1/4 mb-4 rounded"></div>
        <div className="flex gap-4">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="min-w-[200px] h-[250px] bg-slate-100 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!products || products.length === 0) return null;

  return (
    <div className="amz-card p-5 my-4 relative group">
      <h2 className="text-xl font-bold mb-4 flex items-center justify-between">
        <span>{title}</span>
        {seeMoreLink && (
          <Link to={seeMoreLink} className="text-sm font-normal text-amazon-link-teal hover:text-amazon-orange hover:underline">
            See more
          </Link>
        )}
      </h2>
      
      <div className="relative">
        <button 
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 -ml-2 z-10 bg-white/90 shadow-md border border-slate-200 rounded-md p-2 hover:bg-slate-50 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>

        <div 
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto scrollbar-hide py-2 snap-x"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {products.map(product => {
            const baseP = parseFloat(product.base_price || product.price || 0);
            const activeDisc = product.active_discount || product.discounts?.[0] || product.price_detail?.active_discount;
            let dynP = product.dynamic_price ? parseFloat(product.dynamic_price) : baseP;
            let hasDiscount = false;
            let discountLabel = '';

            if (activeDisc) {
              hasDiscount = true;
              const val = parseFloat(activeDisc.discount_value || 0);
              if (activeDisc.discount_type === 'PERCENTAGE') {
                const pct = Math.round(val);
                discountLabel = `-${pct}% OFF`;
                if (!product.dynamic_price) dynP = baseP * (1 - pct / 100);
              } else if (activeDisc.discount_type === 'FIXED' || activeDisc.discount_type === 'FIXED_AMOUNT') {
                discountLabel = `Save $${val.toFixed(2)}`;
                if (!product.dynamic_price) dynP = Math.max(0, baseP - val);
              }
            } else if (dynP < baseP) {
              hasDiscount = true;
              const pct = Math.round(((baseP - dynP) / baseP) * 100);
              discountLabel = `-${pct}% OFF`;
            } else if (product.discount_percent > 0) {
              hasDiscount = true;
              discountLabel = `-${product.discount_percent}% OFF`;
            }

            const imgUrl = product.image_url || product.images?.[0]?.image_url || 'https://via.placeholder.com/200?text=No+Image';

            return (
              <Link 
                key={product.id} 
                to={`/products/${product.id}`}
                className="min-w-[200px] max-w-[200px] flex-shrink-0 flex flex-col snap-start hover:opacity-90 transition-opacity group/card"
              >
                <div className="h-[180px] w-full bg-[#F7F7F7] p-2 flex items-center justify-center mb-2 relative rounded overflow-hidden">
                  <img 
                    src={imgUrl} 
                    alt={product.name}
                    className="max-h-full max-w-full object-contain mix-blend-multiply group-hover/card:scale-105 transition-transform"
                  />
                  {hasDiscount && (
                    <span className="absolute top-2 left-2 bg-[#CC0C39] text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-sm">
                      {discountLabel}
                    </span>
                  )}
                </div>

                {activeDisc?.end_time && (
                  <div className="mb-1">
                    <CountdownTimer endTime={activeDisc.end_time} className="text-[10px] py-0 px-1" />
                  </div>
                )}

                <span className="text-sm font-medium text-amazon-text-primary group-hover/card:text-amazon-orange line-clamp-2 leading-snug mb-1">
                  {product.name}
                </span>

                <div className="flex items-baseline gap-2 mt-auto">
                  <span className="text-base font-bold text-[#0F1111]">${dynP.toFixed(2)}</span>
                  {hasDiscount && baseP > dynP && (
                    <span className="text-xs text-amazon-text-secondary line-through">${baseP.toFixed(2)}</span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>

        <button 
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 -mr-2 z-10 bg-white/90 shadow-md border border-slate-200 rounded-md p-2 hover:bg-slate-50 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
};

