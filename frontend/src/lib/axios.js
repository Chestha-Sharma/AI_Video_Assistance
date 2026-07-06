import axios from 'axios'

// In dev, Vite proxies /api -> http://localhost:8000 (see vite.config.js)
// In prod, point VITE_API_URL at your deployed Flask backend.
export const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})
