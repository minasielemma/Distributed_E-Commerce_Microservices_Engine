import { useState, useEffect, useCallback, useRef } from 'react';
import { usePagination } from './usePagination';

export const useListQuery = (fetchFn, { initialParams = {}, initialPageSize = 10, syncUrl = true } = {}) => {
  const pagination = usePagination({ initialPageSize, syncUrl });
  const { page, pageSize, updatePaginationState, setPage } = pagination;

  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [params, setParams] = useState(initialParams);

  const fetchFnRef = useRef(fetchFn);
  useEffect(() => {
    fetchFnRef.current = fetchFn;
  }, [fetchFn]);

  const loadData = useCallback(async (overrideParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = {
        page,
        page_size: pageSize,
        ...params,
        ...overrideParams,
      };
      const res = await fetchFnRef.current(queryParams);
      const resData = res?.data;
      if (resData) {
        if (Array.isArray(resData)) {
          setData(resData);
          updatePaginationState(resData);
        } else if (resData.results && Array.isArray(resData.results)) {
          setData(resData.results);
          updatePaginationState(resData);
        } else {
          setData([]);
          updatePaginationState({ count: 0, results: [] });
        }
      } else {
        setData([]);
        updatePaginationState({ count: 0, results: [] });
      }
    } catch (err) {
      console.error('useListQuery error:', err);
      setError(err?.response?.data?.detail || err?.message || 'Failed to fetch data');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, params, updatePaginationState]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const updateFilters = useCallback((newFilters) => {
    setParams((prev) => ({ ...prev, ...newFilters }));
    setPage(1);
  }, [setPage]);

  const refetch = useCallback(() => {
    return loadData();
  }, [loadData]);

  return {
    data,
    loading,
    error,
    pagination,
    params,
    setParams,
    updateFilters,
    refetch,
  };
};
