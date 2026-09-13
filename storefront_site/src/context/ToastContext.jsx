import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showSuccess = useCallback((msg, duration) => addToast(msg, 'success', duration), [addToast]);
  const showError = useCallback((msg, duration) => addToast(msg, 'error', duration), [addToast]);
  const showInfo = useCallback((msg, duration) => addToast(msg, 'info', duration), [addToast]);

  return (
    <ToastContext.Provider value={{ addToast, removeToast, showSuccess, showError, showInfo }}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-md w-full px-4 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-center gap-3 p-4 rounded-lg shadow-lg border transition-all duration-300 animate-slide-up bg-white ${
              toast.type === 'success'
                ? 'border-amazon-stock-green text-[#0F1111]'
                : toast.type === 'error'
                ? 'border-amazon-deal-red text-[#0F1111]'
                : 'border-amazon-prime-blue text-[#0F1111]'
            }`}
          >
            {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-amazon-stock-green shrink-0" />}
            {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-amazon-deal-red shrink-0" />}
            {toast.type === 'info' && <Info className="w-5 h-5 text-amazon-prime-blue shrink-0" />}
            
            <p className="text-sm font-medium flex-1 break-words">{toast.message}</p>
            
            <button
              onClick={() => removeToast(toast.id)}
              className="text-slate-400 hover:text-black transition-colors shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
