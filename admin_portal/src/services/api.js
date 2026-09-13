import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  const tenantId = localStorage.getItem('active_tenant_id');
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }
  config.headers['X-Portal-Type'] = 'admin';
  return config;
}, (error) => {
  return Promise.reject(error);
});


api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken && originalRequest.url !== '/auth/token/' && originalRequest.url !== '/auth/token/refresh/') {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          }).then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          }).catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const res = await axios.post(`${API_BASE}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          const { access } = res.data;
          localStorage.setItem('access_token', access);
          api.defaults.headers.common.Authorization = `Bearer ${access}`;
          processQueue(null, access);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch (refreshErr) {
          processQueue(refreshErr, null);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.dispatchEvent(new Event('auth:unauthorized'));
          return Promise.reject(refreshErr);
        } finally {
          isRefreshing = false;
        }
      }
    }
    return Promise.reject(error);
  }
);

export const getErrorMessage = (err) => {
  if (!err) return 'An unknown error occurred.';
  if (typeof err === 'string') {
    if (err.includes('<!DOCTYPE') || err.includes('<html')) {
      return 'Server error. Please try again later.';
    }
    return err;
  }

  if (err.response) {
    const status = err.response.status;
    const data = err.response.data;

    if (status === 404) return 'Requested resource or service endpoint was not found.';
    if (status === 401) return 'Session expired. Please log in again.';
    if (status === 403) return 'You do not have permission to access this resource.';
    if (status >= 500) return 'Internal server error. Please check server logs.';

    if (data) {
      if (typeof data === 'string') {
        if (data.includes('<!DOCTYPE') || data.includes('<html')) {
          return `Server returned status code ${status}.`;
        }
        return data;
      }
      if (data.detail) return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      if (data.error) return typeof data.error === 'string' ? data.error : JSON.stringify(data.error);
      if (data.message) return typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
      if (data.non_field_errors) return Array.isArray(data.non_field_errors) ? data.non_field_errors.join(', ') : String(data.non_field_errors);
      if (typeof data === 'object') {
        const messages = [];
        for (const [key, val] of Object.entries(data)) {
          const valStr = Array.isArray(val) ? val.join(', ') : typeof val === 'object' ? JSON.stringify(val) : String(val);
          messages.push(`${key}: ${valStr}`);
        }
        if (messages.length > 0) return messages.join(' | ');
      }
    }
  }

  return err.message || 'An error occurred while communicating with the server.';
};

export default api;

