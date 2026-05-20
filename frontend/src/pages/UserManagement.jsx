import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../api/auth'
import { getErrorMessage } from '../utils/errorHandler'
import './UserManagement.css'

const UserManagement = () => {
  const { user } = useAuthStore()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [editData, setEditData] = useState({})

  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const data = await authAPI.getUsers()
      setUsers(data)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (user) => {
    setSelectedUser(user)
    setEditData({
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active
    })
    setShowModal(true)
    setError('')
    setSuccess('')
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      await authAPI.updateUser(selectedUser.id, editData)
      setSuccess('User updated successfully!')
      fetchUsers()
      setTimeout(() => {
        setShowModal(false)
        setSuccess('')
      }, 1500)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update user')
    }
  }

  const handleDelete = async (userId, username) => {
    if (!window.confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone.`)) {
      return
    }

    try {
      await authAPI.deleteUser(userId)
      setSuccess(`User "${username}" deleted successfully!`)
      fetchUsers()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to delete user')
    }
  }

  const handleToggleStatus = async (user) => {
    try {
      await authAPI.updateUser(user.id, { is_active: !user.is_active })
      setSuccess(`User ${user.is_active ? 'deactivated' : 'activated'} successfully!`)
      fetchUsers()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update user status')
    }
  }

  if (user?.role !== 'admin' && user?.role !== 'super_admin') {
    return (
      <div className="user-management-container">
        <div className="access-denied">
          <h1>Access Denied</h1>
          <p>You do not have permission to access user management.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="user-management-container">
      <div className="page-header">
        <h1>User Management</h1>
        <p>Manage system users and their permissions</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {loading ? (
        <div className="loading">Loading users...</div>
      ) : (
        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Username</th>
                <th>Email</th>
                <th>Full Name</th>
                {user?.role === 'super_admin' && <th>Organization</th>}
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className={!u.is_active ? 'inactive-row' : ''}>
                  <td>{u.id}</td>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td>{u.full_name}</td>
                  {user?.role === 'super_admin' && <td>{u.organization_name || '—'}</td>}
                  <td>
                    <span className={`role-badge role-${u.role}`}>
                      {u.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${u.is_active ? 'status-active' : 'status-inactive'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleEdit(u)}
                      className="btn-action btn-edit"
                      title="Edit user"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleToggleStatus(u)}
                      className={`btn-action ${u.is_active ? 'btn-deactivate' : 'btn-activate'}`}
                      title={u.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {u.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    {u.id !== user.id && (
                      <button
                        onClick={() => handleDelete(u.id, u.username)}
                        className="btn-action btn-delete"
                        title="Delete user"
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && (
            <div className="no-data">No users found</div>
          )}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit User: {selectedUser.username}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                ×
              </button>
            </div>

            <form onSubmit={handleUpdate} className="modal-form">
              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={editData.email}
                  onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Full Name *</label>
                <input
                  type="text"
                  value={editData.full_name}
                  onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Role *</label>
                <select
                  value={editData.role}
                  onChange={(e) => setEditData({ ...editData, role: e.target.value })}
                  required
                >
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="employee">Employee</option>
                  <option value="vendor">Vendor</option>
                </select>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editData.is_active}
                    onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })}
                  />
                  Active
                </label>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Update User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserManagement
