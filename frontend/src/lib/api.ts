import axios from 'axios';
import { useAuthStore } from '../store/useAuthStore';

// Get API URL from env, default to local docker/backend address
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // important for refresh cookies
});

// Add a request interceptor to inject the token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor to handle 401s and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Prevent infinite loops if refresh endpoint itself fails with 401
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/refresh') {
      originalRequest._retry = true;
      
      try {
        // Assume the backend uses HTTP-only cookies for refresh
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true });
        
        const newToken = data.access_token;
        const user = useAuthStore.getState().user;
        
        // Update the token in our auth store
        useAuthStore.getState().setAuth(newToken, user!);
        
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, log the user out
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
