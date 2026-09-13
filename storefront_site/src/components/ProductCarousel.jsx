import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

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
          {products.map(product => (
            <Link 
              key={product.id} 
              to={`/products/${product.id}`}
              className="min-w-[200px] max-w-[200px] flex-shrink-0 flex flex-col snap-start hover:opacity-80 transition-opacity"
            >
              <div className="h-[200px] w-full bg-[#F7F7F7] p-2 flex items-center justify-center mb-2">
                <img 
                  src={product.image_url || 'https://via.placeholder.com/200'} 
                  alt={product.name}
                  className="max-h-full max-w-full object-contain mix-blend-multiply"
                />
              </div>
              {product.discount_percent > 0 && (
                <div className="flex items-center gap-2 mb-1">
                  <span className="bg-[#CC0C39] text-white text-xs font-bold px-2 py-1 rounded-sm">
                    {product.discount_percent}% off
                  </span>
                  <span className="text-[#CC0C39] text-xs font-bold tracking-tight">Deal</span>
                </div>
              )}
              <span className="text-sm text-amazon-link-teal line-clamp-2 leading-snug">
                {product.name}
              </span>
            </Link>
          ))}
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
