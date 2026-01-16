import apiClient from './client'

export const receiptAPI = {
    // Upload and process receipt
    uploadReceipt: async(file, receiptType = null) => {
        const formData = new FormData()
        formData.append('file', file)
        if (receiptType) {
            formData.append('receipt_type', receiptType)
        }

        const response = await apiClient.post('/api/receipts/upload-receipt', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
        return response.data
    },

    // Get all receipts
    getReceipts: async(params = {}) => {
        const response = await apiClient.get('/api/receipts/receipts', { params })
        return response.data
    },

    // Get a specific receipt
    getReceipt: async(receiptId) => {
        const response = await apiClient.get(`/api/receipts/receipts/${receiptId}`)
        return response.data
    },

    // Get inventory (updated from receipts)
    getInventory: async(params = {}) => {
        const response = await apiClient.get('/api/receipts/inventory', { params })
        return response.data
    },

    // Update receipt
    updateReceipt: async(receiptId, formData) => {
        const response = await apiClient.put(`/api/receipts/receipts/${receiptId}`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
        return response.data
    },

    // Delete receipt
    deleteReceipt: async(receiptId) => {
        const response = await apiClient.delete(`/api/receipts/receipts/${receiptId}`)
        return response.data
    },

    // Seed database
    seedDatabase: async() => {
        const response = await apiClient.post('/api/seed-database')
        return response.data
    },
}