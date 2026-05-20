import apiClient from './client'

const organizationsAPI = {
  /**
   * List all organizations (super_admin only).
   */
  listOrganizations: async () => {
    const response = await apiClient.get('/api/organizations')
    return response.data
  },

  /**
   * Get a single organization by ID (super_admin only).
   */
  getOrganization: async (orgId) => {
    const response = await apiClient.get(`/api/organizations/${orgId}`)
    return response.data
  },

  /**
   * Create a new organization with automatic admin provisioning (super_admin only).
   */
  createOrganization: async (orgData) => {
    const response = await apiClient.post('/api/organizations', orgData)
    return response.data
  },

  /**
   * Update an organization's metadata (super_admin only).
   */
  updateOrganization: async (orgId, updateData) => {
    const response = await apiClient.put(`/api/organizations/${orgId}`, updateData)
    return response.data
  },
}

export default organizationsAPI
