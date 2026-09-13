import React from 'react';
import { Link } from 'react-router-dom';

export const CategoryCard = ({ title, linkText = 'Shop now', linkUrl = '#', items = [] }) => {
  return (
    <div className="amz-card p-5 flex flex-col h-[420px] bg-white z-10 overflow-hidden">
      <h2 className="text-xl font-bold mb-3 line-clamp-1 text-[#0F1111] shrink-0">{title}</h2>

      {items.length === 1 ? (
        <div className="min-h-0 flex-1 mb-3 flex items-center justify-center bg-white p-2 cursor-pointer hover:opacity-80 transition-opacity">
          <Link to={items[0].linkUrl || linkUrl} className="w-full h-full flex items-center justify-center">
            <img
              src={items[0].image}
              alt={items[0].label}
              className="max-h-full max-w-full object-contain"
            />
          </Link>
        </div>
      ) : items.length > 1 ? (
        <div className="min-h-0 flex-1 grid grid-cols-2 grid-rows-2 gap-3 mb-3">
          {items.slice(0, 4).map((item, idx) => (
            <Link to={item.linkUrl || linkUrl} key={idx} className="flex flex-col cursor-pointer group overflow-hidden">
              <div className="flex-1 min-h-0 bg-white flex items-center justify-center group-hover:opacity-80 transition-opacity mb-1">
                <img
                  src={item.image}
                  alt={item.label}
                  className="max-h-full max-w-full object-contain"
                />
              </div>
              <span className="text-xs text-amazon-text-primary line-clamp-1 shrink-0">{item.label}</span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="min-h-0 flex-1 bg-slate-50 flex items-center justify-center mb-3 text-[#565959] text-sm">
          No items available
        </div>
      )}

      <Link to={linkUrl} className="text-amazon-link-teal hover:text-amazon-orange hover:underline text-sm font-medium shrink-0">
        {linkText}
      </Link>
    </div>
  );
};
