import apiClient from './client'

export const inventoryAPI = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/api/inventory', { params })
    return response.data
  },

  getById: async (id) => {
    const response = await apiClient.get(`/api/inventory/${id}`)
    return response.data
  },

  create: async (itemData) => {
    const response = await apiClient.post('/api/inventory', itemData)
    return response.data
  },

  update: async (id, itemData) => {
    const response = await apiClient.put(`/api/inventory/${id}`, itemData)
    return response.data
  },

  restock: async (id, quantity, notes) => {
    const response = await apiClient.post(`/api/inventory/${id}/restock`, null, {
      params: { quantity, notes },
    })
    return response.data
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/api/inventory/${id}`)
    return response.data
  },

  exportCSV: async () => {
    const response = await apiClient.get('/api/inventory/export/csv', {
      responseType: 'blob'
    })
    return response.data
  },

  exportExcel: async () => {
    const response = await apiClient.get('/api/inventory/export/excel', {
      responseType: 'blob'
    })
    return response.data
  }
}








