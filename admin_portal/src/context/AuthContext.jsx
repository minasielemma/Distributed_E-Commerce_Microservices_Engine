import React, { createContext, useState, useEffect, useMemo } from 'react';
import { authService } from '../services/apiServices';

export const AuthContext = createContext();

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

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [activeTenant, setActiveTenant] = useState(JSON.parse(localStorage.getItem('active_tenant_data') || 'null'));
  const [loading, setLoading] = useState(true);

  const decodedToken = useMemo(() => parseJwt(token), [token]);

  const isPlatformAdmin = useMemo(() => {
    if (!token) return false;
    const role = decodedToken.role || '';
    return (
      decodedToken.is_platform_admin === true ||
      decodedToken.is_staff === true ||
      decodedToken.is_superuser === true ||
      role.toUpperCase() === 'PLATFORM_ADMIN'
    );
  }, [token, decodedToken]);

  const userRole = useMemo(() => {
    if (isPlatformAdmin) return 'PLATFORM_ADMIN';
    return decodedToken.role || 'STORE_OWNER';
  }, [isPlatformAdmin, decodedToken]);

  const isStoreOwner = useMemo(() => !isPlatformAdmin, [isPlatformAdmin]);

  const fetchProfile = async () => {
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
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      setUser((prev) => prev || (decodedToken ? { ...decodedToken, user_id: decodedToken.user_id, id: decodedToken.user_id } : null));
      fetchProfile();
    } else {
      setLoading(false);
    }

    const handleUnauthorized = () => {
      logout();
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

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_tenant_id');
    localStorage.removeItem('active_tenant_data');
    setToken(null);
    setUser(null);
    setActiveTenant(null);
  };

  const selectTenant = (tenant) => {
    setActiveTenant(tenant);
    if (tenant) {
      localStorage.setItem('active_tenant_id', tenant.id);
      localStorage.setItem('active_tenant_data', JSON.stringify(tenant));
    } else {
      localStorage.removeItem('active_tenant_id');
      localStorage.removeItem('active_tenant_data');
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      activeTenant,
      login,
      logout,
      selectTenant,
      fetchProfile,
      loading,
      isPlatformAdmin,
      isStoreOwner,
      userRole,
      decodedToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};

