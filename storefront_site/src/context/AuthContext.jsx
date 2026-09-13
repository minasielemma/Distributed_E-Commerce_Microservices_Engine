import React, { createContext, useState, useEffect } from 'react';
import api from '../services/api';
import { authService } from '../services/apiServices';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [activeTenantId, setActiveTenantId] = useState(localStorage.getItem('active_tenant_id') || '');
  const [loading, setLoading] = useState(true);

  const parseJwt = (t) => {
    try {
      if (!t) return {};
      const base64Url = t.split('.')[1];
      if (!base64Url) return {};
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch (e) {
      return {};
    }
  };

  const fetchProfile = async () => {
    const decodedToken = parseJwt(token);
    try {
      const res = await authService.getProfile();
      const profile = res.data || {};
      const canonicalUserId = decodedToken.user_id || profile.user_id || profile.id;
      setUser({
        ...decodedToken,
        ...profile,
        user_id: canonicalUserId,
        id: canonicalUserId,
        pk: canonicalUserId,
      });
    } catch (err) {
      // Only logout if explicitly unauthorized (expired/invalid token)
      if (err?.response?.status === 401) {
        logout();
      }
      // For network errors or other issues, keep the user logged in
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      const decodedToken = parseJwt(token);
      setUser((prev) => prev || (decodedToken ? { ...decodedToken, user_id: decodedToken.user_id, id: decodedToken.user_id } : null));
      fetchProfile();
    } else {
      setLoading(false);
    }

    const handleUnauthorized = () => {
      const currentPath = window.location.pathname + window.location.search + window.location.hash;
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        localStorage.setItem('redirect_after_login', currentPath);
      }
      logout();
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
        window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
      }
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [token]);

  const login = async (username, password) => {
    const res = await authService.login({ username, password });
    const accessToken = res.data.access;
    const refreshToken = res.data.refresh;
    
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
    
    setToken(accessToken);
    await fetchProfile();
    return res.data;
  };

  const register = async (username, email, password) => {
    const res = await authService.register({ username, email, password });
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setToken(null);
    setUser(null);
  };

  const setTenant = (id) => {
    setActiveTenantId(id);
    if (id) {
      localStorage.setItem('active_tenant_id', id);
    } else {
      localStorage.removeItem('active_tenant_id');
    }
  };

  const updateProfile = async (profileData) => {
    const res = await authService.updateProfile(profileData);
    setUser(res.data);
    return res.data;
  };

  return (
    <AuthContext.Provider value={{ user, token, activeTenantId, login, register, logout, setTenant, updateProfile, fetchProfile, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
