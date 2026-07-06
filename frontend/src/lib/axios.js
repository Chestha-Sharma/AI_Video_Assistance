import axios from 'axios'

const prodBaseURL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api` 
  : '/api';

export const axiosInstance = axios.create({
  baseURL: prodBaseURL,
})