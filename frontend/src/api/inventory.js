import apiClient from './client'

export const inventoryAPI = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/api/inventory/', { params })
    // Response: { items, total, page, page_size }
    return response.data
  },

  getById: async (id) => {
    const response = await apiClient.get(`/api/inventory/${id}`)
    return response.data
  },

  create: async (itemData) => {
    const response = await apiClient.post('/api/inventory/', itemData)
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

  delete: async (itemOrId) => {
    const id = typeof itemOrId === 'object' && itemOrId !== null
      ? itemOrId.id ?? itemOrId.inventory_id ?? itemOrId.product_id
      : itemOrId

    if (id === undefined || id === null || id === '') {
      throw new Error('Cannot delete product: missing inventory id')
    }

    try {
      const response = await apiClient.delete(`/api/inventory/${id}`)
      return response.data
    } catch (error) {
      // Some environments enforce trailing slash on path routes.
      if (error?.response?.status === 404) {
        const response = await apiClient.delete(`/api/inventory/${id}/`)
        return response.data
      }
      throw error
    }
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








