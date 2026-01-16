import apiClient from './client'

export const aiAPI = {
  forecastSales: async (daysAhead = 30) => {
    const response = await apiClient.post('/api/ai/forecast/sales', null, {
      params: { days_ahead: daysAhead },
    })
    return response.data
  },

  getReorderSuggestions: async () => {
    const response = await apiClient.post('/api/ai/automate/reorder-suggestions')
    return response.data
  },

  getTaskSuggestions: async () => {
    const response = await apiClient.post('/api/ai/automate/task-suggestions')
    return response.data
  },
}








