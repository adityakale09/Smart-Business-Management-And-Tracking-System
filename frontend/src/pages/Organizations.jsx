import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import organizationsAPI from '../api/organizations'
import { getErrorMessage } from '../utils/errorHandler'
import { Building2, Plus } from 'lucide-react'
import './Organizations.css'

const Organizations = () => {
  const { user } = useAuthStore()
  const [organizations, setOrganizations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Create modal state
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createdOrg, setCreatedOrg] = useState(null)
  const [createData, setCreateData] = useState({
    name: '',
    slug: '',
    admin_email: '',
    admin_username: '',
    admin_password: '',
    admin_full_name: '',
    settings: '',
  })

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedOrg, setSelectedOrg] = useState(null)
  const [editData, setEditData] = useState({})

  useEffect(() => {
    fetchOrganizations()
  }, [])

  const fetchOrganizations = async () => {
    try {
      setLoading(true)
      setError('')
      const data = await organizationsAPI.listOrganizations()
      setOrganizations(data)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to load organizations')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setCreatedOrg(null)

    // Validate required fields
    const required = ['name', 'slug', 'admin_email', 'admin_username', 'admin_password']
    for (const field of required) {
      if (!createData[field]?.trim()) {
        setError(`${field.replace('_', ' ')} is required`)
        return
      }
    }

    if (createData.admin_password.length < 8) {
      setError('Admin password must be at least 8 characters')
      return
    }

    try {
      setCreating(true)
      const payload = {
        name: createData.name.trim(),
        slug: createData.slug.trim().toLowerCase(),
        admin_email: createData.admin_email.trim(),
        admin_username: createData.admin_username.trim(),
        admin_password: createData.admin_password,
        admin_full_name: createData.admin_full_name.trim() || undefined,
      }

      if (createData.settings.trim()) {
        try {
          payload.settings = JSON.parse(createData.settings)
        } catch {
          setError('Settings must be valid JSON (or leave empty)')
          setCreating(false)
          return
        }
      }

      const result = await organizationsAPI.createOrganization(payload)
      setCreatedOrg(result)
      setSuccess(result.message || 'Organization created successfully!')
      fetchOrganizations()

      // Reset form after 5s
      setTimeout(() => {
        setCreateData({
          name: '', slug: '', admin_email: '', admin_username: '',
          admin_password: '', admin_full_name: '', settings: '',
        })
        setCreatedOrg(null)
      }, 5000)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to create organization')
    } finally {
      setCreating(false)
    }
  }

  const handleEdit = (org) => {
    setSelectedOrg(org)
    setEditData({
      name: org.name,
      is_active: org.is_active,
    })
    setShowEditModal(true)
    setError('')
    setSuccess('')
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      const updatePayload = {}
      if (editData.name !== selectedOrg.name) updatePayload.name = editData.name
      if (editData.is_active !== selectedOrg.is_active) updatePayload.is_active = editData.is_active

      if (Object.keys(updatePayload).length === 0) {
        setShowEditModal(false)
        return
      }

      await organizationsAPI.updateOrganization(selectedOrg.id, updatePayload)
      setSuccess('Organization updated successfully!')
      setShowEditModal(false)
      fetchOrganizations()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update organization')
    }
  }

  const handleToggleStatus = async (org) => {
    try {
      await organizationsAPI.updateOrganization(org.id, { is_active: !org.is_active })
      setSuccess(`Organization ${org.is_active ? 'deactivated' : 'activated'} successfully!`)
      fetchOrganizations()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to update organization status')
    }
  }

  const resetCreateModal = () => {
    setShowCreateModal(false)
    setError('')
    setCreatedOrg(null)
    setCreateData({
      name: '', slug: '', admin_email: '', admin_username: '',
      admin_password: '', admin_full_name: '', settings: '',
    })
  }

  // Only super_admin can access
  if (user?.role !== 'super_admin') {
    return (
      <div className="organizations-container">
        <div className="access-denied">
          <Building2 size={48} strokeWidth={1.5} />
          <h1>Access Denied</h1>
          <p>Only super administrators can manage organizations.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="organizations-container">
      <div className="page-header">
        <h1>Organization Management</h1>
        <p>Create and manage businesses on the platform</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="org-toolbar">
        <span className="org-count">{organizations.length} organization(s)</span>
        <button className="btn-create" onClick={() => setShowCreateModal(true)}>
          <Plus size={18} />
          Create Organization
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading organizations...</div>
      ) : (
        <div className="org-table-container">
          <table className="org-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Organization</th>
                <th>Slug</th>
                <th>Users</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {organizations.map((org) => (
                <tr key={org.id} className={!org.is_active ? 'inactive-row' : ''}>
                  <td>{org.id}</td>
                  <td>
                    <span className="org-name-cell">{org.name}</span>
                  </td>
                  <td>
                    <code style={{ fontSize: '0.82rem', background: 'var(--bg-subtle, #f3f4f6)', padding: '2px 6px', borderRadius: '4px' }}>
                      {org.slug}
                    </code>
                  </td>
                  <td>
                    <span className="badge user-count-badge">
                      {org.user_count ?? '—'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${org.is_active ? 'badge-active' : 'badge-inactive'}`}>
                      {org.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                    {org.created_at ? new Date(org.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <div className="actions-cell">
                      <button
                        onClick={() => handleEdit(org)}
                        className="btn-action btn-edit"
                        title="Edit organization"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleToggleStatus(org)}
                        className={`btn-action ${org.is_active ? 'btn-toggle-deactivate' : 'btn-toggle-activate'}`}
                        title={org.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {org.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {organizations.length === 0 && (
            <div className="no-data">
              <p>No organizations found. Click "Create Organization" to add a business.</p>
            </div>
          )}
        </div>
      )}

      {/* Create Organization Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={resetCreateModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Organization</h2>
              <button className="modal-close" onClick={resetCreateModal}>×</button>
            </div>

            {createdOrg ? (
              <div className="modal-form">
                <div className="created-admin-info">
                  <h3>✓ Organization Created Successfully!</h3>
                  <p><strong>Organization:</strong> {createdOrg.organization.name}</p>
                  <p><strong>Admin Username:</strong> {createdOrg.admin_user.username}</p>
                  <p><strong>Admin Email:</strong> {createdOrg.admin_user.email}</p>
                  <p><strong>Role:</strong> {createdOrg.admin_user.role}</p>
                  <p style={{ marginTop: '0.5rem', color: 'var(--success-color, #16a34a)', fontWeight: 500 }}>
                    The admin can now log in and manage this organization's data.
                  </p>
                </div>
                <div className="modal-actions">
                  <button type="button" onClick={resetCreateModal} className="btn-primary">
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleCreate} className="modal-form">
                <div className="form-group">
                  <label>Organization Name *</label>
                  <input
                    type="text"
                    value={createData.name}
                    onChange={(e) => setCreateData({ ...createData, name: e.target.value })}
                    placeholder="e.g. Acme Corporation"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Slug *</label>
                  <input
                    type="text"
                    value={createData.slug}
                    onChange={(e) => setCreateData({ ...createData, slug: e.target.value.replace(/\s+/g, '-').toLowerCase() })}
                    placeholder="e.g. acme-corp"
                    pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                    required
                  />
                  <div className="field-hint">URL-friendly identifier: lowercase letters, numbers, hyphens</div>
                </div>

                <hr style={{ margin: '1.25rem 0', border: 'none', borderTop: '1px solid var(--border-color, #e5e7eb)' }} />
                <h3 style={{ fontSize: '0.95rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>Admin User Details</h3>

                <div className="form-group">
                  <label>Admin Email *</label>
                  <input
                    type="email"
                    value={createData.admin_email}
                    onChange={(e) => setCreateData({ ...createData, admin_email: e.target.value })}
                    placeholder="admin@acme-corp.com"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Admin Username *</label>
                  <input
                    type="text"
                    value={createData.admin_username}
                    onChange={(e) => setCreateData({ ...createData, admin_username: e.target.value.replace(/\s+/g, '_') })}
                    placeholder="e.g. acme_admin"
                    required
                  />
                  <div className="field-hint">Letters, numbers, and underscores only</div>
                </div>

                <div className="form-group">
                  <label>Admin Password *</label>
                  <input
                    type="password"
                    value={createData.admin_password}
                    onChange={(e) => setCreateData({ ...createData, admin_password: e.target.value })}
                    placeholder="Minimum 8 characters"
                    minLength={8}
                    required
                  />
                  <div className="field-hint">Must include uppercase, lowercase, and a number</div>
                </div>

                <div className="form-group">
                  <label>Admin Full Name</label>
                  <input
                    type="text"
                    value={createData.admin_full_name}
                    onChange={(e) => setCreateData({ ...createData, admin_full_name: e.target.value })}
                    placeholder="e.g. John Doe (optional)"
                  />
                </div>

                <div className="form-group">
                  <label>Settings (JSON)</label>
                  <input
                    type="text"
                    value={createData.settings}
                    onChange={(e) => setCreateData({ ...createData, settings: e.target.value })}
                    placeholder='e.g. {"timezone":"UTC","currency":"INR"} (optional)'
                  />
                  <div className="field-hint">Optional JSON object with organization preferences</div>
                </div>

                <div className="modal-actions">
                  <button type="button" onClick={resetCreateModal} className="btn-secondary">
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary" disabled={creating}>
                    {creating ? 'Creating...' : 'Create Organization'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Edit Organization Modal */}
      {showEditModal && selectedOrg && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Organization: {selectedOrg.name}</h2>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>×</button>
            </div>

            <form onSubmit={handleUpdate} className="modal-form">
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={editData.name}
                  onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Status</label>
                <select
                  value={editData.is_active}
                  onChange={(e) => setEditData({ ...editData, is_active: e.target.value === 'true' })}
                >
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowEditModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Organizations
