import axios from 'axios';

// Attempt to get the auth store state directly for the interceptor.
// This has limitations: it won't be reactive if the token changes after the client is initialized.
// A better approach might involve a request queue or re-creating the client/interceptor on auth changes,
// or having a way to inject the token more dynamically.
// For now, this is a common basic setup.
// import { useAuthStore } from '../store/authStore'; // Assuming relative path from src/api to src/store

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add interceptors for request (e.g., adding auth token)
apiClient.interceptors.request.use(config => {
  // Dynamically import and get state, or ensure store is initialized before client.
  // This is a simplified example. For a robust solution, consider how the store is accessed.
  // If useAuthStore is used here, it might cause issues if this file is imported before store is fully set up,
  // or if it leads to circular dependencies.
  // A common pattern is to set the token header in a dedicated function or when making the actual call.

  // const token = useAuthStore.getState().token; // Example: if token is in Zustand
  // if (token) {
  //   config.headers.Authorization = `Bearer ${token}`;
  // }
  return config;
});

export default apiClient;
