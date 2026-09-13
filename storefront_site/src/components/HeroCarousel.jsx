import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const HeroCarousel = ({ products = [] }) => {
  const [current, setCurrent] = useState(0);

  // If we don't have enough products, we can't show a carousel
  const validProducts = products.filter(p => p.images && p.images.length > 0);

  useEffect(() => {
    if (validProducts.length <= 1) return;
    const timer = setInterval(() => {
      setCurrent((prev) => (prev + 1) % validProducts.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [validProducts.length]);

  if (validProducts.length === 0) {
    return <div className="w-full h-[150px] bg-[#E3E6E6]"></div>; // spacer
  }

  const prev = () => setCurrent(current === 0 ? validProducts.length - 1 : current - 1);
  const next = () => setCurrent((current + 1) % validProducts.length);

  return (
    <div className="relative w-full min-h-[360px] sm:min-h-[400px] md:h-[440px] lg:h-[520px] overflow-hidden bg-gradient-to-r from-[#232F3E] to-[#131921]">
      <div 
        className="flex transition-transform duration-500 ease-in-out h-full"
        style={{ transform: `translateX(-${current * 100}%)` }}
      >
        {validProducts.map((product, i) => {
          const imgUrl = product.images[0]?.image_url;
          return (
            <div key={product.id} className="w-full flex-shrink-0 relative h-full flex items-center justify-center">
              {/* Product Layout for Banner */}
              <div className="flex flex-col md:flex-row items-center justify-center w-full max-w-6xl mx-auto px-8 sm:px-12 gap-4 sm:gap-6 md:gap-8 z-10 pt-4 pb-12 sm:pb-20 lg:pb-32">
                <div className="flex-1 text-white space-y-2 sm:space-y-4 text-center md:text-left">
                   <span className="bg-amazon-orange text-[#111] text-[10px] sm:text-xs font-bold px-2 py-0.5 sm:py-1 uppercase rounded-sm inline-block">
                      Featured Deal
                   </span>
                   <h2 className="text-xl sm:text-3xl md:text-4xl lg:text-5xl font-extrabold line-clamp-2">{product.name}</h2>
                   <p className="text-base sm:text-lg md:text-xl text-gray-300 font-medium">${Number(product.base_price).toFixed(2)}</p>
                   <div>
                     <Link to={`/products/${product.id}`} className="bg-amazon-cta-secondary hover:bg-amazon-cta-secondaryHover text-[#0F1111] font-bold py-1.5 sm:py-2 px-4 sm:px-6 text-xs sm:text-sm rounded-full inline-block mt-1 sm:mt-2 shadow">
                        Shop Now
                     </Link>
                   </div>
                </div>
                <div className="flex-1 flex justify-center items-center h-32 sm:h-44 md:h-64 lg:h-80">
                   <img 
                      src={imgUrl} 
                      alt={product.name} 
                      className="max-h-full max-w-full object-contain drop-shadow-2xl rounded"
                   />
                </div>
              </div>

              {/* Bottom Gradient for merging into background */}
              <div className="absolute bottom-0 left-0 right-0 h-32 sm:h-48 bg-gradient-to-t from-[#E3E6E6] to-transparent z-0 pointer-events-none"></div>
            </div>
          );
        })}
      </div>
      
      {validProducts.length > 1 && (
        <>
          <button 
            onClick={prev}
            className="absolute top-1/4 left-0 h-32 w-12 flex items-center justify-center border-2 border-transparent hover:border-[#008296] focus:border-[#008296] hover:bg-white/10 rounded-sm mx-2 group z-30"
          >
            <ChevronLeft className="w-8 h-8 text-white opacity-50 group-hover:opacity-100" />
          </button>
          <button 
            onClick={next}
            className="absolute top-1/4 right-0 h-32 w-12 flex items-center justify-center border-2 border-transparent hover:border-[#008296] focus:border-[#008296] hover:bg-white/10 rounded-sm mx-2 group z-30"
          >
            <ChevronRight className="w-8 h-8 text-white opacity-50 group-hover:opacity-100" />
          </button>
        </>
      )}
    </div>
  );
};
