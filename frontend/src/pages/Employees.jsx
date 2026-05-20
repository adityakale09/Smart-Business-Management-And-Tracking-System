import { useEffect, useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { employeesAPI } from '../api/employees'
import { authAPI } from '../api/auth'
import { Users, Plus, X, Search, Edit2, Trash2, ChevronDown, ChevronUp, Shield, AlertTriangle, User, Briefcase, DollarSign, Calendar, Phone, MapPin, FileText, UserCircle, BadgeCheck } from 'lucide-react'
import { getErrorMessage } from '../utils/errorHandler'
import './Employees.css'

const normalizeEmployeesPayload = (payload) => {
  if (!payload) return []
  if (Array.isArray(payload)) return payload
  if (Array.isArray(payload.items)) return payload.items
  if (Array.isArray(payload.employees)) return payload.employees
  return []
}

const DEPARTMENTS = [
  'Engineering',
  'Sales',
  'Marketing',
  'Human Resources',
  'Finance',
  'Operations',
  'Customer Support',
  'Design',
  'Legal',
  'Administration'
]

const EMPLOYEE_STATUSES = ['active', 'on_leave', 'terminated', 'suspended']

const STATUS_COLORS = {
  active: '#d1fae5',
  on_leave: '#fef3c7',
  terminated: '#fee2e2',
  suspended: '#fce4ec'
}

const STATUS_TEXT_COLORS = {
  active: '#065f46',
  on_leave: '#92400e',
  terminated: '#991b1b',
  suspended: '#c62828'
}

const initialFormState = {
  user_id: '',
  full_name: '',
  department: '',
  position: '',
  salary: '',
  hire_date: '',
  phone: '',
  address: '',
  emergency_contact: '',
  notes: ''
}

const Employees = () => {
  const queryClient = useQueryClient()

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null)
  const [showPasswordError, setShowPasswordError] = useState(false)

  // Form states
  const [formData, setFormData] = useState({ ...initialFormState })
  const [editFormData, setEditFormData] = useState({})
  const [passwordInput, setPasswordInput] = useState('')
  const [selectedEmployee, setSelectedEmployee] = useState(null)

  // Search & filter states
  const [searchQuery, setSearchQuery] = useState('')
  const [departmentFilter, setDepartmentFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  // Success message
  const [successMessage, setSuccessMessage] = useState('')

  // Fetch employees
  const { data: employeesPayload, isLoading, isError, error } = useQuery({
    queryKey: ['employees', searchQuery, departmentFilter, statusFilter],
    queryFn: () => employeesAPI.getAll({
      search: searchQuery || undefined,
      department: departmentFilter || undefined,
      status: statusFilter || undefined
    }),
  })

  const { data: currentUser } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authAPI.getCurrentUser(),
  })

  const { data: usersList } = useQuery({
    queryKey: ['users'],
    queryFn: () => authAPI.getUsers(),
    enabled: showAddModal || showEditModal,
  })

  const employees = useMemo(() => normalizeEmployeesPayload(employeesPayload), [employeesPayload])

  // Get unique departments from actual data
  const availableDepartments = useMemo(() => {
    const depts = new Set()
    employees.forEach(emp => {
      if (emp.department) depts.add(emp.department)
    })
    return [...new Set([...DEPARTMENTS, ...depts])].sort()
  }, [employees])

  // Create mutation
  const createEmployeeMutation = useMutation({
    mutationFn: (employeeData) => employeesAPI.create(employeeData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setShowAddModal(false)
      setFormData({ ...initialFormState })
      showTemporarySuccess('Employee created successfully!')
    },
  })

  // Update mutation
  const updateEmployeeMutation = useMutation({
    mutationFn: ({ id, data }) => employeesAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setShowEditModal(false)
      setShowDetailModal(false)
      setEditFormData({})
      setShowPasswordModal(false)
      setPasswordInput('')
      showTemporarySuccess('Employee updated successfully!')
    },
  })

  // Delete mutation
  const deleteEmployeeMutation = useMutation({
    mutationFn: (id) => employeesAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      setShowDeleteConfirm(null)
      setShowDetailModal(false)
      setSelectedEmployee(null)
      showTemporarySuccess('Employee deleted successfully!')
    },
  })

  // Verify password mutation
  const verifyPasswordMutation = useMutation({
    mutationFn: (password) => employeesAPI.verifyPassword(password),
    onSuccess: (data) => {
      if (data.verified) {
        setShowPasswordModal(false)
        setPasswordInput('')
        setShowPasswordError(false)
        // Populate edit form with current employee data
        if (selectedEmployee) {
          setEditFormData({
            full_name: selectedEmployee.full_name || '',
            department: selectedEmployee.department || '',
            position: selectedEmployee.position || '',
            salary: selectedEmployee.salary?.toString() || '',
            status: selectedEmployee.status || 'active',
            phone: selectedEmployee.phone || '',
            address: selectedEmployee.address || '',
            emergency_contact: selectedEmployee.emergency_contact || '',
            notes: selectedEmployee.notes || '',
            hire_date: selectedEmployee.hire_date
              ? selectedEmployee.hire_date.substring(0, 10)
              : ''
          })
        }
        setShowEditModal(true)
      } else {
        setShowPasswordError(true)
      }
    },
  })

  const showTemporarySuccess = (message) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  // Reset password verify state
  const handleRequestEdit = (employee) => {
    setSelectedEmployee(employee)
    setShowPasswordModal(true)
    setPasswordInput('')
    setShowPasswordError(false)
  }

  const handlePasswordSubmit = (e) => {
    e.preventDefault()
    if (!passwordInput.trim()) return
    verifyPasswordMutation.mutate(passwordInput)
  }

  // Create employee submit
  const handleCreateSubmit = (e) => {
    e.preventDefault()

    if (!formData.user_id || formData.user_id === '') {
      alert('Please enter a user ID')
      return
    }

    const userId = parseInt(formData.user_id)
    if (isNaN(userId) || userId <= 0) {
      alert('Please enter a valid user ID')
      return
    }

    const employeeData = {
      user_id: userId
    }

    // Add optional fields only if they have values
    if (formData.full_name?.trim()) employeeData.full_name = formData.full_name.trim()
    if (formData.department?.trim()) employeeData.department = formData.department.trim()
    if (formData.position?.trim()) employeeData.position = formData.position.trim()
    if (formData.salary && formData.salary !== '') {
      const salary = parseFloat(formData.salary)
      if (!isNaN(salary) && salary >= 0) employeeData.salary = salary
    }
    if (formData.hire_date && formData.hire_date !== '') {
      if (/^\d{4}-\d{2}-\d{2}$/.test(formData.hire_date)) {
        employeeData.hire_date = new Date(formData.hire_date + 'T00:00:00').toISOString()
      }
    }
    if (formData.phone?.trim()) employeeData.phone = formData.phone.trim()
    if (formData.address?.trim()) employeeData.address = formData.address.trim()
    if (formData.emergency_contact?.trim()) employeeData.emergency_contact = formData.emergency_contact.trim()
    if (formData.notes?.trim()) employeeData.notes = formData.notes.trim()

    createEmployeeMutation.mutate(employeeData)
  }

  // Edit employee submit
  const handleEditSubmit = (e) => {
    e.preventDefault()
    if (!selectedEmployee) return

    const updateData = {}
    for (const [key, value] of Object.entries(editFormData)) {
      if (value !== '' && value !== null && value !== undefined) {
        if (key === 'salary') {
          const parsed = parseFloat(value)
          if (!isNaN(parsed) && parsed >= 0) updateData[key] = parsed
        } else if (key === 'hire_date' && value) {
          if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
            updateData[key] = new Date(value + 'T00:00:00').toISOString()
          }
        } else {
          updateData[key] = value
        }
      }
    }

    updateEmployeeMutation.mutate({ id: selectedEmployee.id, data: updateData })
  }

  // Delete handler
  const handleDeleteConfirm = () => {
    if (!showDeleteConfirm) return
    deleteEmployeeMutation.mutate(showDeleteConfirm.id)
  }

  // Open detail modal
  const handleViewDetails = (employee) => {
    setSelectedEmployee(employee)
    setShowDetailModal(true)
  }

  // Close modals
  const closeAllModals = () => {
    setShowAddModal(false)
    setShowDetailModal(false)
    setShowEditModal(false)
    setShowPasswordModal(false)
    setShowDeleteConfirm(null)
    setShowPasswordError(false)
    setPasswordInput('')
  }

  // Format salary
  const formatSalary = (salary) => {
    if (salary === null || salary === undefined) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(salary)
  }

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return dateStr
    }
  }

  // Get user name for dropdown
  const getUserName = (userId) => {
    if (!usersList || !userId) return `User #${userId}`
    const user = usersList.find(u => u.id === parseInt(userId) || u.id === userId)
    return user ? `${user.full_name} (@${user.username})` : `User #${userId}`
  }

  useEffect(() => {
    if (import.meta.env.DEV && employeesPayload !== undefined) {
      console.log('[Employees] Employees list response:', employeesPayload)
    }
  }, [employeesPayload])

  return (
    <div className="employees-page">
      {/* Success notification */}
      {successMessage && (
        <div className="success-notification">
          <BadgeCheck size={20} />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="page-header">
        <div>
          <h1>Employee Management</h1>
          <p>Manage your team and track employee information</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
          <Plus size={20} />
          Add Employee
        </button>
      </div>

      {/* Search and Filters */}
      <div className="employees-toolbar">
        <div className="search-bar">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            placeholder="Search by name, ID, department, position..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <button
          className="btn-filter-toggle"
          onClick={() => setShowFilters(!showFilters)}
        >
          {showFilters ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          Filters
        </button>
      </div>

      {showFilters && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>Department</label>
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
            >
              <option value="">All Departments</option>
              {availableDepartments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label>Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              {EMPLOYEE_STATUSES.map(status => (
                <option key={status} value={status}>
                  {status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
          {(searchQuery || departmentFilter || statusFilter) && (
            <button
              className="btn-clear-filters"
              onClick={() => {
                setSearchQuery('')
                setDepartmentFilter('')
                setStatusFilter('')
              }}
            >
              Clear Filters
            </button>
          )}
        </div>
      )}

      {/* Employee count */}
      {!isLoading && !isError && (
        <div className="employees-count">
          {employees.length} employee{employees.length !== 1 ? 's' : ''} found
        </div>
      )}

      {/* Employee Cards */}
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
              <div
                key={employee.id}
                className="employee-card"
                onClick={() => handleViewDetails(employee)}
              >
                <div className="employee-card-header">
                  <div className="employee-avatar">
                    <Users size={24} />
                  </div>
                  <div className="employee-card-actions">
                    <button
                      className="btn-icon edit"
                      title="Edit employee"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleRequestEdit(employee)
                      }}
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      className="btn-icon delete"
                      title="Delete employee"
                      onClick={(e) => {
                        e.stopPropagation()
                        setShowDeleteConfirm(employee)
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <div className="employee-info">
                  <h3>{employee.full_name || 'No Name'}</h3>
                  <span className="employee-badge-id">{employee.employee_id}</span>
                  <p className="employee-position">{employee.position || 'N/A'}</p>
                  <p className="employee-department">{employee.department || 'N/A'}</p>
                  {employee.phone && <p className="employee-phone"><Phone size={14} /> {employee.phone}</p>}
                  <div className="employee-card-footer">
                    <span
                      className="status-badge"
                      style={{
                        background: STATUS_COLORS[employee.status] || '#e2e8f0',
                        color: STATUS_TEXT_COLORS[employee.status] || '#475569'
                      }}
                    >
                      {(employee.status || 'active').replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="no-data">
              <Users size={48} />
              <p>No employees found</p>
              {(searchQuery || departmentFilter || statusFilter) && (
                <p className="no-data-hint">Try adjusting your search or filters</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* ===== ADD EMPLOYEE MODAL ===== */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><Plus size={20} /> Add New Employee</h2>
              <button className="modal-close" onClick={() => setShowAddModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateSubmit} className="modal-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="add-user_id">User ID *</label>
                  <input
                    id="add-user_id"
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
                  <label htmlFor="add-full_name">Full Name</label>
                  <input
                    id="add-full_name"
                    type="text"
                    placeholder="Full name (optional)"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="add-department">Department</label>
                  <select
                    id="add-department"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  >
                    <option value="">Select department</option>
                    {DEPARTMENTS.map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="add-position">Position</label>
                  <input
                    id="add-position"
                    type="text"
                    placeholder="Position (optional)"
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="add-salary">Salary</label>
                  <input
                    id="add-salary"
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="Salary (optional)"
                    value={formData.salary}
                    onChange={(e) => setFormData({ ...formData, salary: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="add-hire_date">Hire Date</label>
                  <input
                    id="add-hire_date"
                    type="date"
                    value={formData.hire_date}
                    onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="add-phone">Phone</label>
                  <input
                    id="add-phone"
                    type="text"
                    placeholder="Phone (optional)"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="add-emergency_contact">Emergency Contact</label>
                  <input
                    id="add-emergency_contact"
                    type="text"
                    placeholder="Emergency contact (optional)"
                    value={formData.emergency_contact}
                    onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="add-address">Address</label>
                <textarea
                  id="add-address"
                  placeholder="Address (optional)"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  rows="2"
                />
              </div>
              <div className="form-group">
                <label htmlFor="add-notes">Notes</label>
                <textarea
                  id="add-notes"
                  placeholder="Additional notes (optional)"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows="2"
                />
              </div>
              {createEmployeeMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(createEmployeeMutation.error) || 'Failed to create employee'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createEmployeeMutation.isPending}>
                  {createEmployeeMutation.isPending ? 'Creating...' : 'Create Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===== EMPLOYEE DETAIL MODAL ===== */}
      {showDetailModal && selectedEmployee && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><User size={20} /> Employee Details</h2>
              <button className="modal-close" onClick={() => setShowDetailModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="employee-detail-content">
              <div className="detail-header">
                <div className="detail-avatar">
                  <Users size={40} />
                </div>
                <div className="detail-title">
                  <h3>{selectedEmployee.full_name || 'No Name'}</h3>
                  <span className="employee-badge-id">{selectedEmployee.employee_id}</span>
                  <span
                    className="status-badge"
                    style={{
                      background: STATUS_COLORS[selectedEmployee.status] || '#e2e8f0',
                      color: STATUS_TEXT_COLORS[selectedEmployee.status] || '#475569'
                    }}
                  >
                    {(selectedEmployee.status || 'active').replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div className="detail-sections">
                <div className="detail-section">
                  <h4><Briefcase size={16} /> Employment</h4>
                  <div className="detail-grid">
                    <div className="detail-field">
                      <label>Department</label>
                      <span>{selectedEmployee.department || 'N/A'}</span>
                    </div>
                    <div className="detail-field">
                      <label>Position</label>
                      <span>{selectedEmployee.position || 'N/A'}</span>
                    </div>
                    <div className="detail-field">
                      <label>Salary</label>
                      <span>{formatSalary(selectedEmployee.salary)}</span>
                    </div>
                    <div className="detail-field">
                      <label>Hire Date</label>
                      <span>{formatDate(selectedEmployee.hire_date)}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h4><Phone size={16} /> Contact</h4>
                  <div className="detail-grid">
                    <div className="detail-field">
                      <label>Phone</label>
                      <span>{selectedEmployee.phone || 'N/A'}</span>
                    </div>
                    <div className="detail-field">
                      <label>Address</label>
                      <span>{selectedEmployee.address || 'N/A'}</span>
                    </div>
                    <div className="detail-field">
                      <label>Emergency Contact</label>
                      <span>{selectedEmployee.emergency_contact || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h4><FileText size={16} /> Additional Info</h4>
                  <div className="detail-grid">
                    <div className="detail-field">
                      <label>Employee ID</label>
                      <span>{selectedEmployee.employee_id}</span>
                    </div>
                    <div className="detail-field">
                      <label>User ID</label>
                      <span>{selectedEmployee.user_id || 'N/A'}</span>
                    </div>
                    <div className="detail-field">
                      <label>Notes</label>
                      <span>{selectedEmployee.notes || 'No notes'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-timestamps">
                <span>Created: {formatDate(selectedEmployee.created_at)}</span>
                {selectedEmployee.updated_at && (
                  <span> | Updated: {formatDate(selectedEmployee.updated_at)}</span>
                )}
              </div>
            </div>
            <div className="modal-actions">
              <button
                type="button"
                className="btn-danger"
                onClick={() => {
                  setShowDetailModal(false)
                  setShowDeleteConfirm(selectedEmployee)
                }}
              >
                <Trash2 size={16} /> Delete
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  setShowDetailModal(false)
                  handleRequestEdit(selectedEmployee)
                }}
              >
                <Edit2 size={16} /> Edit Employee
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== PASSWORD VERIFICATION MODAL ===== */}
      {showPasswordModal && (
        <div className="modal-overlay" onClick={() => { setShowPasswordModal(false); setShowPasswordError(false); }}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><Shield size={20} /> Verify Password</h2>
              <button className="modal-close" onClick={() => { setShowPasswordModal(false); setShowPasswordError(false); }}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handlePasswordSubmit} className="modal-form">
              <p className="verify-password-hint">
                Please enter your account password to authorize editing employee information.
              </p>
              <div className="form-group">
                <label htmlFor="verify-password">Password *</label>
                <input
                  id="verify-password"
                  type="password"
                  placeholder="Enter your password"
                  value={passwordInput}
                  onChange={(e) => {
                    setPasswordInput(e.target.value)
                    setShowPasswordError(false)
                  }}
                  required
                  autoFocus
                />
              </div>
              {showPasswordError && (
                <div className="error-message">
                  <AlertTriangle size={16} />
                  Incorrect password. Please try again.
                </div>
              )}
              {verifyPasswordMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(verifyPasswordMutation.error) || 'Verification failed'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => { setShowPasswordModal(false); setShowPasswordError(false); }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={verifyPasswordMutation.isPending}>
                  {verifyPasswordMutation.isPending ? 'Verifying...' : 'Verify & Edit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===== EDIT EMPLOYEE MODAL ===== */}
      {showEditModal && selectedEmployee && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><Edit2 size={20} /> Edit Employee</h2>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="edit-employee-banner">
              Editing: <strong>{selectedEmployee.full_name || selectedEmployee.employee_id}</strong>
            </div>
            <form onSubmit={handleEditSubmit} className="modal-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="edit-full_name">Full Name</label>
                  <input
                    id="edit-full_name"
                    type="text"
                    value={editFormData.full_name || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, full_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-status">Status</label>
                  <select
                    id="edit-status"
                    value={editFormData.status || 'active'}
                    onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                  >
                    {EMPLOYEE_STATUSES.map(status => (
                      <option key={status} value={status}>
                        {status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="edit-department">Department</label>
                  <select
                    id="edit-department"
                    value={editFormData.department || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, department: e.target.value })}
                  >
                    <option value="">Select department</option>
                    {DEPARTMENTS.map(dept => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="edit-position">Position</label>
                  <input
                    id="edit-position"
                    type="text"
                    value={editFormData.position || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, position: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="edit-salary">Salary</label>
                  <input
                    id="edit-salary"
                    type="number"
                    step="0.01"
                    min="0"
                    value={editFormData.salary || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, salary: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-hire_date">Hire Date</label>
                  <input
                    id="edit-hire_date"
                    type="date"
                    value={editFormData.hire_date || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, hire_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="edit-phone">Phone</label>
                  <input
                    id="edit-phone"
                    type="text"
                    value={editFormData.phone || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="edit-emergency_contact">Emergency Contact</label>
                  <input
                    id="edit-emergency_contact"
                    type="text"
                    value={editFormData.emergency_contact || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, emergency_contact: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="edit-address">Address</label>
                <textarea
                  id="edit-address"
                  value={editFormData.address || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, address: e.target.value })}
                  rows="2"
                />
              </div>
              <div className="form-group">
                <label htmlFor="edit-notes">Notes</label>
                <textarea
                  id="edit-notes"
                  value={editFormData.notes || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
                  rows="2"
                />
              </div>
              {updateEmployeeMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(updateEmployeeMutation.error) || 'Failed to update employee'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => {
                  setShowEditModal(false)
                  setShowPasswordModal(false)
                  setPasswordInput('')
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={updateEmployeeMutation.isPending}>
                  {updateEmployeeMutation.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ===== DELETE CONFIRMATION DIALOG ===== */}
      {showDeleteConfirm && (
        <div className="modal-overlay" onClick={() => setShowDeleteConfirm(null)}>
          <div className="modal-content modal-sm" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><AlertTriangle size={20} /> Confirm Deletion</h2>
              <button className="modal-close" onClick={() => setShowDeleteConfirm(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="delete-confirm-content">
              <div className="delete-warning-icon">
                <AlertTriangle size={48} />
              </div>
              <p>
                Are you sure you want to delete the employee record for
                <strong> {showDeleteConfirm.full_name || showDeleteConfirm.employee_id}</strong>?
              </p>
              <p className="delete-warning-text">
                This action cannot be undone. The employee record will be permanently removed from the system.
              </p>
              <div className="delete-employee-info">
                <span>ID: {showDeleteConfirm.employee_id}</span>
                {showDeleteConfirm.department && <span> | Dept: {showDeleteConfirm.department}</span>}
                {showDeleteConfirm.position && <span> | Position: {showDeleteConfirm.position}</span>}
              </div>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn-secondary" onClick={() => setShowDeleteConfirm(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-danger"
                onClick={handleDeleteConfirm}
                disabled={deleteEmployeeMutation.isPending}
              >
                {deleteEmployeeMutation.isPending ? 'Deleting...' : 'Delete Employee'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Employees
