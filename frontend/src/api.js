import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://lost-and-found-2o5g.onrender.com',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const API_BASE = api.defaults.baseURL;

export const errMsg = (ex, fallback = 'An unexpected error occurred') => {
  const d = ex.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d) && d.length > 0) return d[0]?.msg || fallback;
  return fallback;
};

export const getImageUrl = (path) => {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${API_BASE}${path}`;
};

export default api;
