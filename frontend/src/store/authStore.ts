import { create } from 'zustand';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface AuthUser {
  id: string;
  username: string;
  callsign: string;
  role: 'admin' | 'operator' | 'observer';
  node_id: string | null;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  authRequired: boolean;
  loading: boolean;
  error: string | null;

  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem('myc3_token'),
  isAuthenticated: false,
  authRequired: false,
  loading: true,
  error: null,

  login: async (username: string, password: string) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(err.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      localStorage.setItem('myc3_token', data.token);
      set({
        user: data.user,
        token: data.token,
        isAuthenticated: true,
        loading: false,
        error: null,
      });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : 'Login failed',
      });
      throw err;
    }
  },

  logout: async () => {
    const { token } = get();
    try {
      if (token) {
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch {
      // Ignore logout errors
    }
    localStorage.removeItem('myc3_token');
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      error: null,
    });
  },

  refreshToken: async () => {
    const { token } = get();
    if (!token) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.token) {
          localStorage.setItem('myc3_token', data.token);
          set({ token: data.token });
        }
      }
    } catch {
      // Ignore refresh errors
    }
  },

  checkAuth: async () => {
    const { token } = get();
    set({ loading: true });

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/me`, { headers });

      if (!response.ok) {
        // H10: Only treat 401/403 as auth failure, not server errors
        if (response.status === 401 || response.status === 403) {
          localStorage.removeItem('myc3_token');
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            authRequired: true,
            loading: false,
          });
          return;
        }
        // 5xx or other errors: keep token, don't force logout
        set({ loading: false });
        return;
      }

      const data = await response.json();
      set({
        authRequired: data.auth_required,
        isAuthenticated: data.authenticated,
        user: data.user,
        loading: false,
      });
    } catch {
      // Backend unreachable — don't force auth
      set({ loading: false, authRequired: false });
    }
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
