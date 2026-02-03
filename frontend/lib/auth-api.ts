/**
 * Authentication API client for LLM Council
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  email: string;
  email_verified: boolean;
  display_name: string | null;
  avatar_url: string | null;
  preferences: Record<string, any>;
  is_active: boolean;
  has_password: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  display_name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface UpdateProfileData {
  display_name?: string;
  avatar_url?: string;
  preferences?: Record<string, any>;
}

/**
 * Register a new user
 */
export async function register(data: RegisterData): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

/**
 * Login with email and password
 */
export async function login(data: LoginData): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }

  return response.json();
}

/**
 * Request a magic link for passwordless login
 */
export async function requestMagicLink(email: string): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/magic-link`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send magic link');
  }

  return response.json();
}

/**
 * Verify a magic link token
 */
export async function verifyMagicLink(token: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/verify/${token}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Invalid or expired link');
  }

  return response.json();
}

/**
 * Refresh access token using refresh token
 */
export async function refreshToken(refresh_token: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Token refresh failed');
  }

  return response.json();
}

/**
 * Get current user profile
 */
export async function getCurrentUser(accessToken: string): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get user');
  }

  return response.json();
}

/**
 * Update current user profile
 */
export async function updateProfile(
  accessToken: string,
  data: UpdateProfileData
): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update profile');
  }

  return response.json();
}

/**
 * Set or update password
 */
export async function setPassword(
  accessToken: string,
  password: string
): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/me/password`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to set password');
  }

  return response.json();
}

/**
 * Resend verification email
 */
export async function resendVerification(accessToken: string): Promise<MessageResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to resend verification');
  }

  return response.json();
}
