import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { employeesAPI } from '../api/employees'
import { authAPI } from '../api/auth'
import { Users, Plus, X } from 'lucide-react'
import { getErrorMessage } from '../utils/errorHandler'
import './Employees.css'

const normalizeEmployeesPayload = (payload) => {
  if (!payload) {
    return []
  }

  if (Array.isArray(payload)) {
    return payload
  }

  if (Array.isArray(payload.items)) {
    return payload.items
  }

  if (Array.isArray(payload.employees)) {
    return payload.employees
  }

  return []
}

const Employees = () => {
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    employee_id: '',
    user_id: '',
    full_name: '',
    department: '',
    position: '',
    salary: '',
    hire_date: '',
    phone: '',
    address: '',
    emergency_contact: ''
  })
  const queryClient = useQueryClient()

  const { data: employeesPayload, isLoading, isError, error } = useQuery({
    queryKey: ['employees'],
    queryFn: () => employeesAPI.getAll(),
    onError: (err) => {
      console.error('[Employees] Failed to load employees:', err)
    },
  })

  const employees = normalizeEmployeesPayload(employeesPayload)

  const { data: currentUser } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authAPI.getCurrentUser(),
  })

  const createEmployeeMutation = useMutation({
    mutationFn: (employeeData) => employeesAPI.create(employeeData),
    onSuccess: () => {
      queryClient.invalidateQueries(['employees'])
      setShowModal(false)
      setFormData({
        employee_id: '',
        user_id: '',
        full_name: '',
        department: '',
        position: '',
        salary: '',
        hire_date: '',
        phone: '',
        address: '',
        emergency_contact: ''
      })
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validate required fields
    if (!formData.employee_id || !formData.employee_id.trim()) {
      alert('Please enter an employee ID')
      return
    }
    
    if (!formData.user_id || formData.user_id === '') {
      alert('Please enter a user ID')
      return
    }
    
    const userId = parseInt(formData.user_id)
    if (isNaN(userId) || userId <= 0) {
      alert('Please enter a valid user ID')
      return
    }
    
    // Build employee data with required fields
    const employeeData = {
      employee_id: formData.employee_id.trim(),
      user_id: userId
    }
    
    // Add optional fields only if they have values (don't send empty strings or null)
    const dept = formData.department?.trim()
    if (dept && dept !== '') {
      employeeData.department = dept
    }
    
    const pos = formData.position?.trim()
    if (pos && pos !== '') {
      employeeData.position = pos
    }
    
    if (formData.salary && formData.salary !== '') {
      const salary = parseFloat(formData.salary)
      if (!isNaN(salary) && salary >= 0) {
        employeeData.salary = salary
      }
    }
    
    if (formData.hire_date && formData.hire_date !== '') {
      // Convert date string to ISO format for backend
      // Date input type="date" returns YYYY-MM-DD format
      try {
        // If it's already in YYYY-MM-DD format (from date input), use it directly
        if (/^\d{4}-\d{2}-\d{2}$/.test(formData.hire_date)) {
          const dateObj = new Date(formData.hire_date + 'T00:00:00')
          if (!isNaN(dateObj.getTime())) {
            employeeData.hire_date = dateObj.toISOString()
          }
        } else {
          // Try to parse other formats (DD-MM-YYYY)
          const parts = formData.hire_date.split(/[-\/]/)
          if (parts.length === 3) {
            // Try DD-MM-YYYY format first
            const day = parts[0].padStart(2, '0')
            const month = parts[1].padStart(2, '0')
            const year = parts[2]
            const isoDate = `${year}-${month}-${day}T00:00:00`
            const parsedDate = new Date(isoDate)
            if (!isNaN(parsedDate.getTime())) {
              employeeData.hire_date = parsedDate.toISOString()
            }
          }
        }
      } catch (error) {
        console.error('Error parsing date:', error)
        // Skip date if parsing fails - it's optional
      }
    }
    
    const phone = formData.phone?.trim()
    if (phone && phone !== '') {
      employeeData.phone = phone
    }
    
    const address = formData.address?.trim()
    if (address && address !== '') {
      employeeData.address = address
    }
    
    const emergency = formData.emergency_contact?.trim()
    if (emergency && emergency !== '') {
      employeeData.emergency_contact = emergency
    }
    
    console.log('Sending employee data:', employeeData)
    createEmployeeMutation.mutate(employeeData)
  }

  useEffect(() => {
    if (import.meta.env.DEV && employeesPayload !== undefined) {
      console.log('[Employees] Employees list response:', employeesPayload)
    }
  }, [employeesPayload])

  useEffect(() => {
    if (import.meta.env.DEV) {
      console.log('[Employees] Employees rows:', employees)
    }
  }, [employees])

  return (
    <div className="employees-page">
      <div className="page-header">
        <div>
          <h1>Employee Management</h1>
          <p>Manage your team and track employee information</p>
        </div>
        <button className="btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={20} />
          Add Employee
        </button>
      </div>

      {isLoading ? (
        <div className="loading">Loading employees...</div>
      ) : isError ? (
        <div className="error-message">
          {getErrorMessage(error) || 'Failed to load employees.'}
        </div>
      ) : (
        <div className="employees-grid">
          {employees && employees.length > 0 ? (
            employees.map((employee) => (
              <div key={employee.id} className="employee-card">
                <div className="employee-avatar">
                  <Users size={24} />
                </div>
                <div className="employee-info">
                  <h3>Employee ID: {employee.employee_id}</h3>
                  <p className="employee-name">{employee.full_name || 'No name'}</p>
                  <p className="employee-position">{employee.position || 'N/A'}</p>
                  <p className="employee-department">{employee.department || 'N/A'}</p>
                  {employee.phone && <p className="employee-phone">Phone: {employee.phone}</p>}
                  <span className={`status-badge ${employee.status}`}>
                    {employee.status}
                  </span>
                </div>
              </div>
            ))
          ) : (
            <div className="no-data">No employees found</div>
          )}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New Employee</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label htmlFor="employee_id">Employee ID *</label>
                <input
                  id="employee_id"
                  type="text"
                  placeholder="Enter employee ID"
                  value={formData.employee_id}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="user_id">User ID *</label>
                <input
                  id="user_id"
                  type="number"
                  placeholder={currentUser ? `Current user ID: ${currentUser.id}` : 'Enter user ID'}
                  value={formData.user_id}
                  onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                  required
                />
                {currentUser && (
                  <small>Tip: Use {currentUser.id} for current user</small>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="department">Department</label>
                <input
                  id="department"
                  type="text"
                  placeholder="Department (optional)"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="position">Position</label>
                <input
                  id="position"
                  type="text"
                  placeholder="Position (optional)"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="salary">Salary</label>
                <input
                  id="salary"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Salary (optional)"
                  value={formData.salary}
                  onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="hire_date">Hire Date</label>
                <input
                  id="hire_date"
                  type="date"
                  placeholder="dd-mm-yyyy"
                  value={formData.hire_date}
                  onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="phone">Phone</label>
                <input
                  id="phone"
                  type="text"
                  placeholder="Phone (optional)"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="address">Address</label>
                <textarea
                  id="address"
                  placeholder="Address (optional)"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows="2"
                />
              </div>
              <div className="form-group">
                <label htmlFor="emergency_contact">Emergency Contact</label>
                <input
                  id="emergency_contact"
                  type="text"
                  placeholder="Emergency contact (optional)"
                  value={formData.emergency_contact}
                  onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                />
              </div>
              {createEmployeeMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(createEmployeeMutation.error) || 'Failed to create employee'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createEmployeeMutation.isLoading}>
                  {createEmployeeMutation.isLoading ? 'Creating...' : 'Add Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Employees








