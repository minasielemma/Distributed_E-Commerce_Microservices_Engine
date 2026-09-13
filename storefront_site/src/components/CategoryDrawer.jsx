import React, { useState } from 'react';
import { Menu, X, User } from 'lucide-react';
import { Link } from 'react-router-dom';

export const CategoryDrawer = ({ isOpen, onClose, token }) => {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/70 z-[60] transition-opacity"
          onClick={onClose}
        ></div>
      )}

      {/* Drawer */}
      <div 
        className={`fixed inset-y-0 left-0 w-[80%] max-w-[365px] bg-white z-[70] transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } overflow-y-auto`}
      >
        <div className="bg-amazon-nav-blue text-white p-4 flex items-center justify-between">
          <Link to="/profile" className="flex items-center gap-2 font-bold text-lg" onClick={onClose}>
            <User className="w-7 h-7 bg-white/20 p-1 rounded-full" />
            {token ? 'Hello, User' : 'Hello, sign in'}
          </Link>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="py-2">
          <div className="border-b border-gray-200 py-3">
            <h3 className="px-5 text-lg font-bold text-amazon-text-primary mb-2">Trending</h3>
            <Link to="/bestsellers" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Best Sellers</Link>
            <Link to="/new-arrivals" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>New Releases</Link>
            <Link to="/deals" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Movers & Shakers</Link>
          </div>

          <div className="border-b border-gray-200 py-3">
            <h3 className="px-5 text-lg font-bold text-amazon-text-primary mb-2">Shop By Department</h3>
            <Link to="/category/electronics" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Electronics</Link>
            <Link to="/category/computers" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Computers</Link>
            <Link to="/category/home" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Smart Home</Link>
            <Link to="/category/fashion" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Fashion</Link>
            <Link to="/categories" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary flex items-center justify-between" onClick={onClose}>
              See All <span className="text-gray-400">›</span>
            </Link>
          </div>

          <div className="py-3">
            <h3 className="px-5 text-lg font-bold text-amazon-text-primary mb-2">Help & Settings</h3>
            <Link to="/profile" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Your Account</Link>
            <Link to="/orders" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Returns & Orders</Link>
            <Link to="/chat" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Customer Service</Link>
            {token ? (
              <div className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary cursor-pointer" onClick={onClose}>Sign Out</div>
            ) : (
              <Link to="/login" className="block px-5 py-3 hover:bg-gray-100 text-sm text-amazon-text-secondary" onClick={onClose}>Sign In</Link>
            )}
          </div>
        </div>
      </div>
    </>
  );
};
