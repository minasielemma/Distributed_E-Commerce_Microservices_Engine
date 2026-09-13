import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

export const usePagination = ({ initialPage = 1, initialPageSize = 10, syncUrl = true } = {}) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const getUrlParam = (key, fallback) => {
    if (!syncUrl) return fallback;
    const val = searchParams.get(key);
    return val ? Number(val) || fallback : fallback;
  };

  const [page, setPage] = useState(() => getUrlParam('page', initialPage));
  const [pageSize, setPageSize] = useState(() => getUrlParam('page_size', initialPageSize));
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const updatePaginationState = useCallback((paginatedData) => {
    if (!paginatedData) return;
    if (Array.isArray(paginatedData)) {
      setTotalItems(paginatedData.length);
      setTotalPages(1);
      setPage(1);
      return;
    }
    const count = typeof paginatedData.count === 'number' ? paginatedData.count : 0;
    setTotalItems(count);
    const size = paginatedData.page_size || pageSize || 10;
    const computedPages = paginatedData.total_pages || (size > 0 ? Math.ceil(count / size) : 1);
    setTotalPages(computedPages || 1);
    if (typeof paginatedData.current_page === 'number') {
      setPage(paginatedData.current_page);
    }
  }, [pageSize]);

  const handlePageChange = useCallback((newPage) => {
    const validPage = Math.max(1, Math.min(newPage, totalPages || 1));
    setPage(validPage);
    if (syncUrl) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', String(validPage));
        return next;
      }, { replace: true });
    }
  }, [totalPages, syncUrl, setSearchParams]);

  const handlePageSizeChange = useCallback((newPageSize) => {
    const size = Number(newPageSize) || 10;
    setPageSize(size);
    setPage(1);
    if (syncUrl) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', '1');
        next.set('page_size', String(size));
        return next;
      }, { replace: true });
    }
  }, [syncUrl, setSearchParams]);

  const resetPage = useCallback(() => {
    setPage(1);
    if (syncUrl) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', '1');
        return next;
      }, { replace: true });
    }
  }, [syncUrl, setSearchParams]);

  return {
    page,
    pageSize,
    totalItems,
    totalPages,
    updatePaginationState,
    handlePageChange,
    handlePageSizeChange,
    resetPage,
    setPage,
  };
};
