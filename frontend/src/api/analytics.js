import apiClient from './client'

export const analyticsAPI = {
  getDashboard: async () => {
    const response = await apiClient.get('/api/analytics/dashboard')
    return response.data
  },

  getSalesTrend: async (days = 30, groupBy = 'day') => {
    const response = await apiClient.get('/api/analytics/sales/trend', {
      params: { days, group_by: groupBy },
    })
    return response.data
  },

  getInventoryAnalysis: async () => {
    const response = await apiClient.get('/api/analytics/inventory/analysis')
    return response.data
  },

  getEmployeePerformance: async (days = 30) => {
    const response = await apiClient.get('/api/analytics/employee/performance', {
      params: { days },
    })
    return response.data
  },
}








