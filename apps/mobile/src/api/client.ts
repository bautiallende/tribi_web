import * as SecureStore from 'expo-secure-store';
import Constants from 'expo-constants';

const API_BASE = Constants.expoConfig?.extra?.apiBase || 'http://localhost:8000';
const TOKEN_KEY = 'tribi_jwt_token';

// Token management
export const storeToken = async (token: string): Promise<void> => {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
};

export const getToken = async (): Promise<string | null> => {
  return await SecureStore.getItemAsync(TOKEN_KEY);
};

export const clearToken = async (): Promise<void> => {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
};

// API client helper
interface FetchOptions extends RequestInit {
  requiresAuth?: boolean;
}

export const apiClient = async <T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> => {
  const { requiresAuth = false, headers = {}, ...rest } = options;
  
  const requestHeaders: HeadersInit = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (requiresAuth) {
    const token = await getToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  const url = `${API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...rest,
      headers: requestHeaders,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Network error');
  }
};

// Auth API
export const authAPI = {
  requestCode: async (email: string) => {
    return apiClient<{ message: string }>('/api/auth/request-code', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },

  verify: async (email: string, code: string) => {
    const response = await apiClient<{ 
      token: string; 
      user: { id: number; email: string; name?: string } 
    }>(
      '/api/auth/verify',
      {
        method: 'POST',
        body: JSON.stringify({ email, code }),
      }
    );
    // Store token - ensure it's a string
    if (response.token && typeof response.token === 'string') {
      await storeToken(response.token);
    }
    return response;
  },
};

// Countries API
export const countriesAPI = {
  getAll: async () => {
    return apiClient<Array<{ id: number; iso2: string; name: string }>>('/api/countries');
  },
};

// Plans API
export const plansAPI = {
  getByCountry: async (iso2: string) => {
    return apiClient<Array<{
      id: number;
      name: string;
      data_gb: string;
      duration_days: number;
      price_usd: string;
      description: string;
      is_unlimited: boolean;
      country_id: number;
    }>>(`/api/plans?country=${iso2}`);
  },
};

// Orders API
export const ordersAPI = {
  create: async (planId: number) => {
    return apiClient<{
      id: number;
      plan_id: number;
      user_id: number;
      status: string;
      amount_usd: string;
      created_at: string;
    }>('/api/orders', {
      method: 'POST',
      requiresAuth: true,
      body: JSON.stringify({ plan_id: planId }),
    });
  },

  getMyOrders: async () => {
    return apiClient<Array<{
      id: number;
      plan_id: number;
      status: string;
      amount_usd: string;
      created_at: string;
      plan: {
        name: string;
        data_gb: string;
        duration_days: number;
        country: {
          name: string;
          iso2: string;
        };
      };
      esim: {
        activation_code: string;
        qr_code_url: string;
        status: string;
      } | null;
    }>>('/api/orders/mine', {
      requiresAuth: true,
    });
  },
};

// Payments API
export const paymentsAPI = {
  createPayment: async (orderId: number, provider: string = 'MOCK') => {
    return apiClient<{
      id: number;
      order_id: number;
      provider: string;
      status: string;
      amount_usd: string;
      external_payment_id: string | null;
    }>('/api/payments/create', {
      method: 'POST',
      requiresAuth: true,
      body: JSON.stringify({ order_id: orderId, provider }),
    });
  },
};

// eSIM API
export const esimAPI = {
  activate: async (orderId: number) => {
    return apiClient<{
      activation_code: string;
      qr_code_url: string;
      instructions: string;
    }>('/api/esims/activate', {
      method: 'POST',
      requiresAuth: true,
      body: JSON.stringify({ order_id: orderId }),
    });
  },
};
