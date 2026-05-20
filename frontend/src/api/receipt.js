import apiClient from './client'

export const receiptAPI = {
    // Preview extracted receipt items (OCR + parse only)
    previewReceipt: async(file, receiptType = null, options = {}) => {
        const formData = new FormData()
        formData.append('file', file)
        if (receiptType) {
            formData.append('receipt_type', receiptType)
        }

        const response = await apiClient.post('/api/receipts/preview-receipt', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: options.timeout ?? 90000,
            signal: options.signal,
        })
        return response.data
    },

    // Upload and process receipt
    uploadReceipt: async(file, receiptType = null, conversion = null, options = {}) => {
        const formData = new FormData()
        formData.append('file', file)
        if (receiptType) {
            formData.append('receipt_type', receiptType)
        }
        if (conversion?.sourceCurrency) {
            formData.append('source_currency', conversion.sourceCurrency)
        }
        if (conversion?.targetCurrency) {
            formData.append('target_currency', conversion.targetCurrency)
        }
        if (typeof conversion?.exchangeRate === 'number' && Number.isFinite(conversion.exchangeRate)) {
            formData.append('exchange_rate', String(conversion.exchangeRate))
        }

        const response = await apiClient.post('/api/receipts/upload-receipt', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            timeout: options.timeout ?? 180000,
            signal: options.signal,
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

    // Get receipt analytics
    getAnalytics: async(params = {}) => {
        const response = await apiClient.get('/api/receipts/analytics', { params })
        return response.data
    },

    // Export receipts
    exportReceipts: async(params = {}) => {
        const response = await apiClient.get('/api/receipts/export', {
            params,
            responseType: params.format === 'json' ? 'json' : 'blob',
        })
        return response.data
    },
}