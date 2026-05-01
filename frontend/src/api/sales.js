import apiClient from './client'

export const salesAPI = {
  getAll: async (params = {}) => {
    const response = await apiClient.get('/api/sales/', { params })
    // Response: { items, total, page, page_size }
    return response.data
  },

  getById: async (id) => {
    const response = await apiClient.get(`/api/sales/${id}`)
    return response.data
  },

  create: async (saleData) => {
    const response = await apiClient.post('/api/sales/', saleData)
    return response.data
  },

  getSummary: async (days = 30) => {
    const response = await apiClient.get('/api/sales/stats/summary', {
      params: { days },
    })
    return response.data
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/api/sales/${id}`)
    return response.data
  },

  exportCSV: async () => {
    const response = await apiClient.get('/api/sales/export/csv', {
      responseType: 'blob'
    })
    return response.data
  },

  exportExcel: async () => {
    const response = await apiClient.get('/api/sales/export/excel', {
      responseType: 'blob'
    })
    return response.data
  },

  downloadInvoice: async (saleId) => {
    const response = await apiClient.get(`/api/sales/${saleId}/invoice`, {
      responseType: 'blob'
    })
    return response.data
  }
}








