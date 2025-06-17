import { create } from 'zustand';
// Using @/services alias now that tsconfig is updated
import { loginUser } from '@/services/authService';

// Define interfaces for credentials (can be moved to a types file)
interface LoginCredentials {
  username?: string;
  password?: string;
}

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  // Adding loading/error states for async login
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  // Optional: function to set token directly if loaded from elsewhere (e.g. localStorage)
  // setToken: (token: string | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  token: null,
  isLoading: false,
  error: null,
  login: async (credentials: LoginCredentials) => {
    set({ isLoading: true, error: null });
    try {
      const response = await loginUser(credentials);
      set({
        isAuthenticated: true,
        token: response.access_token,
        isLoading: false,
        error: null
      });
      // Optional: Store token in localStorage for persistence
      // localStorage.setItem('authToken', response.access_token);
      // You might also want to update the apiClient's default headers here if it's not handled by an interceptor
      // that reactively reads from this store.
    } catch (err) {
      let errorMessage = 'Login failed. Please check your credentials.';
      if (err instanceof Error) {
        // You might want to parse specific error responses from the API
        // errorMessage = err.message;
      }
      set({
        isAuthenticated: false,
        token: null,
        isLoading: false,
        error: errorMessage
      });
      // Optional: Remove token from localStorage on failure
      // localStorage.removeItem('authToken');
    }
  },
  logout: () => {
    set({ isAuthenticated: false, token: null, error: null });
    // Optional: Remove token from localStorage
    // localStorage.removeItem('authToken');
    // And clear apiClient headers if set directly
  },
  // setToken: (token: string | null) => {
  //   set({ isAuthenticated: !!token, token });
  // }
}));

// Optional: Initialize auth state from localStorage
// const initialToken = localStorage.getItem('authToken');
// if (initialToken) {
//   useAuthStore.getState().setToken(initialToken);
// }
