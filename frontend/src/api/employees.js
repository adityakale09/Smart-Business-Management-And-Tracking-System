import apiClient from './client'

export const employeesAPI = {
    getAll: async(params = {}) => {
        const response = await apiClient.get('/api/employees/', { params })
        return response.data
    },

    getById: async(id) => {
        const response = await apiClient.get(`/api/employees/${id}`)
        return response.data
    },

    create: async(employeeData) => {
        const response = await apiClient.post('/api/employees/', employeeData)
        return response.data
    },

    update: async(id, employeeData) => {
        const response = await apiClient.put(`/api/employees/${id}`, employeeData)
        return response.data
    },

    getAttendance: async(employeeId, params = {}) => {
        const response = await apiClient.get(`/api/employees/attendance/${employeeId}`, { params })
        return response.data
    },

    createAttendance: async(attendanceData) => {
        const response = await apiClient.post('/api/employees/attendance', attendanceData)
        return response.data
    },
}