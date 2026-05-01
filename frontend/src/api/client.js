import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'
const DEFAULT_TIMEOUT_MS = 45000

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      const offlineError = new Error('No internet connection. Please reconnect and try again.')
      offlineError.code = 'OFFLINE'
      offlineError.userMessage = 'You are offline. Reconnect to the internet and retry.'
      return Promise.reject(offlineError)
    }

    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      error.userMessage = 'Request timed out. Check your internet and try again.'
      return Promise.reject(error)
    }

    if (error.code === 'ERR_NETWORK') {
      error.userMessage = 'Network error. Please check your connection and retry.'
      return Promise.reject(error)
    }

    if (error.code === 'ERR_CANCELED') {
      error.userMessage = 'Request was cancelled.'
      return Promise.reject(error)
    }

    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export default apiClient








