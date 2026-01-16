import apiClient from './client'

export const authAPI = {
  login: async (username, password) => {
    const response = await apiClient.post('/api/auth/login', {
      username,
      password,
    })
    return response.data
  },

  register: async (userData) => {
    const response = await apiClient.post('/api/auth/register', userData)
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/api/auth/me')
    return response.data
  },

  updateProfile: async (profileData) => {
    const response = await apiClient.put('/api/auth/me', profileData)
    return response.data
  },

  changePassword: async (passwordData) => {
    const response = await apiClient.post('/api/auth/change-password', passwordData)
    return response.data
  },

  // Admin functions
  getUsers: async () => {
    const response = await apiClient.get('/api/auth/users')
    return response.data
  },

  getUser: async (userId) => {
    const response = await apiClient.get(`/api/auth/users/${userId}`)
    return response.data
  },

  updateUser: async (userId, userData) => {
    const response = await apiClient.put(`/api/auth/users/${userId}`, userData)
    return response.data
  },

  deleteUser: async (userId) => {
    const response = await apiClient.delete(`/api/auth/users/${userId}`)
    return response.data
  },
}








