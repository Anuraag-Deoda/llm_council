'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  User,
  AuthResponse,
  login as apiLogin,
  register as apiRegister,
  requestMagicLink as apiRequestMagicLink,
  verifyMagicLink as apiVerifyMagicLink,
  refreshToken as apiRefreshToken,
  getCurrentUser,
  updateProfile as apiUpdateProfile,
  UpdateProfileData,
} from './auth-api';

// Token storage keys
const ACCESS_TOKEN_KEY = 'llm_council_access_token';
const REFRESH_TOKEN_KEY = 'llm_council_refresh_token';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  requestMagicLink: (email: string) => Promise<void>;
  verifyMagicLink: (token: string) => Promise<void>;
  logout: () => void;
  updateProfile: (data: UpdateProfileData) => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper to safely access localStorage
function getStoredToken(key: string): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(key);
}

function setStoredToken(key: string, value: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(key, value);
}

function removeStoredToken(key: string): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(key);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshTokenValue, setRefreshTokenValue] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Handle successful authentication
  const handleAuthSuccess = useCallback((response: AuthResponse) => {
    setAccessToken(response.access_token);
    setRefreshTokenValue(response.refresh_token);
    setUser(response.user);
    setStoredToken(ACCESS_TOKEN_KEY, response.access_token);
    setStoredToken(REFRESH_TOKEN_KEY, response.refresh_token);
  }, []);

  // Clear auth state
  const clearAuth = useCallback(() => {
    setUser(null);
    setAccessToken(null);
    setRefreshTokenValue(null);
    removeStoredToken(ACCESS_TOKEN_KEY);
    removeStoredToken(REFRESH_TOKEN_KEY);
  }, []);

  // Refresh the access token
  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    const storedRefreshToken = getStoredToken(REFRESH_TOKEN_KEY);
    if (!storedRefreshToken) return null;

    try {
      const response = await apiRefreshToken(storedRefreshToken);
      handleAuthSuccess(response);
      return response.access_token;
    } catch {
      clearAuth();
      return null;
    }
  }, [handleAuthSuccess, clearAuth]);

  // Initialize auth state from stored tokens
  useEffect(() => {
    async function initAuth() {
      const storedAccessToken = getStoredToken(ACCESS_TOKEN_KEY);

      if (storedAccessToken) {
        setAccessToken(storedAccessToken);

        try {
          // Try to get current user with stored token
          const userData = await getCurrentUser(storedAccessToken);
          setUser(userData);
        } catch {
          // Token might be expired, try refreshing
          const newToken = await refreshAccessToken();
          if (!newToken) {
            clearAuth();
          }
        }
      }

      setIsLoading(false);
    }

    initAuth();
  }, [refreshAccessToken, clearAuth]);

  // Login with email and password
  const login = useCallback(async (email: string, password: string) => {
    const response = await apiLogin({ email, password });
    handleAuthSuccess(response);
  }, [handleAuthSuccess]);

  // Register a new account
  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    const response = await apiRegister({ email, password, display_name: displayName });
    handleAuthSuccess(response);
  }, [handleAuthSuccess]);

  // Request a magic link
  const requestMagicLink = useCallback(async (email: string) => {
    await apiRequestMagicLink(email);
  }, []);

  // Verify a magic link
  const verifyMagicLink = useCallback(async (token: string) => {
    const response = await apiVerifyMagicLink(token);
    handleAuthSuccess(response);
  }, [handleAuthSuccess]);

  // Logout
  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  // Update user profile
  const updateProfile = useCallback(async (data: UpdateProfileData) => {
    if (!accessToken) throw new Error('Not authenticated');

    const updatedUser = await apiUpdateProfile(accessToken, data);
    setUser(updatedUser);
  }, [accessToken]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    if (!accessToken) return;

    try {
      const userData = await getCurrentUser(accessToken);
      setUser(userData);
    } catch {
      // Token might be expired, try refreshing
      await refreshAccessToken();
    }
  }, [accessToken, refreshAccessToken]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    accessToken,
    login,
    register,
    requestMagicLink,
    verifyMagicLink,
    logout,
    updateProfile,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Higher-order component for protected routes
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.FC<P> {
  return function WithAuthComponent(props: P) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      );
    }

    if (!isAuthenticated) {
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}
