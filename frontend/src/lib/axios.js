import axios from 'axios'

// Production mein VITE_API_URL ke sath '/api' lagana zaroori hai
const prodBaseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api` 
  : '/api';

export const axiosInstance = axios.create({
  baseURL: prodBaseURL,
})