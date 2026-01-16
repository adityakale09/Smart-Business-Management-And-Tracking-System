import { useState, useEffect } from 'react'
import { receiptAPI } from '../api/receipt'
import ReceiptUpload from '../components/ReceiptUpload'
import { getErrorMessage } from '../utils/errorHandler'
import { Trash2, Edit, Eye, X } from 'lucide-react'
import './ReceiptsPage.css'

const ReceiptsPage = () => {
  const [receipts, setReceipts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')
  const [viewModal, setViewModal] = useState(null)
  const [editModal, setEditModal] = useState(null)

  useEffect(() => {
    loadReceipts()
  }, [filter])

  const loadReceipts = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = filter !== 'all' ? { receipt_type: filter } : {}
      const response = await receiptAPI.getReceipts(params)
      if (response && response.receipts) {
        setReceipts(Array.isArray(response.receipts) ? response.receipts : [])
      } else {
        setReceipts([])
      }
    } catch (err) {
      console.error('Error loading receipts:', err)
      setError(getErrorMessage(err) || 'Failed to load receipts')
      setReceipts([]) // Set empty array on error to prevent crashes
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = () => {
    loadReceipts()
  }

  const handleDelete = async (receipt) => {
    if (window.confirm(`Are you sure you want to delete receipt ${receipt.receipt_number || receipt.id}?\n\nTotal Amount: ${formatCurrency(receipt.total_amount)}\nItems: ${receipt.items?.length || 0}`)) {
      try {
        await receiptAPI.deleteReceipt(receipt.id)
        loadReceipts() // Reload the list
      } catch (err) {
        alert(getErrorMessage(err) || 'Failed to delete receipt')
      }
    }
  }

  const handleView = (receipt) => {
    setViewModal(receipt)
  }

  const handleEdit = (receipt) => {
    setEditModal({
      id: receipt.id,
      source: receipt.source || '',
      receipt_type: receipt.receipt_type || 'purchase'
    })
  }

  const handleUpdateReceipt = async (e) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append('source', editModal.source)
      formData.append('receipt_type', editModal.receipt_type)
      
      await receiptAPI.updateReceipt(editModal.id, formData)
      setEditModal(null)
      loadReceipts()
    } catch (err) {
      alert(getErrorMessage(err) || 'Failed to update receipt')
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'Invalid Date'
      return date.toLocaleString()
    } catch (error) {
      console.error('Error formatting date:', error)
      return 'Invalid Date'
    }
  }

  const formatCurrency = (amount) => {
    if (!amount || isNaN(amount)) return '₹0.00'
    try {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
      }).format(amount)
    } catch (error) {
      console.error('Error formatting currency:', error)
      return '₹0.00'
    }
  }

  return (
    <div className="receipts-page">
      <div className="page-header">
        <h1>Receipt Processing</h1>
        <div className="filter-controls">
          <label>Filter:</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All Receipts</option>
            <option value="purchase">Purchases</option>
            <option value="sale">Sales</option>
          </select>
        </div>
      </div>

      <div className="content-grid">
        <div className="upload-section">
          <ReceiptUpload onUploadSuccess={handleUploadSuccess} />
        </div>

        <div className="receipts-section">
          <h2>Processed Receipts ({receipts.length})</h2>

          {loading && <div className="loading">Loading receipts...</div>}

          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          {!loading && !error && receipts.length === 0 && (
            <div className="empty-state">
              <p>No receipts found. Upload a receipt to get started.</p>
            </div>
          )}

          {!loading && !error && receipts.length > 0 && (
            <div className="receipts-table-container">
              <table className="receipts-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Type</th>
                    <th>Source</th>
                    <th>Items</th>
                    <th>Total Amount</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {receipts.map((receipt) => {
                    if (!receipt || !receipt.id) return null
                    try {
                      const dateToFormat = receipt.receipt_date || receipt.created_at
                      const itemCount = receipt.items?.length || (receipt.receipt_items ? receipt.receipt_items.length : 0) || 0
                      const totalAmount = receipt.total_amount || 0
                      return (
                        <tr key={receipt.id}>
                          <td>{formatDate(dateToFormat)}</td>
                          <td>
                            <span className={`type-badge ${receipt.receipt_type || 'unknown'}`}>
                              {receipt.receipt_type || 'N/A'}
                            </span>
                          </td>
                          <td>{receipt.source || 'Manual Upload'}</td>
                          <td>{itemCount}</td>
                          <td>{formatCurrency(totalAmount)}</td>
                          <td>
                            <span className="status-badge success">Processed</span>
                          </td>
                          <td>
                            <div className="action-buttons">
                              <button
                                className="btn-icon btn-info"
                                onClick={() => handleView(receipt)}
                                title="View receipt"
                              >
                                <Eye size={16} />
                              </button>
                              <button
                                className="btn-icon btn-primary"
                                onClick={() => handleEdit(receipt)}
                                title="Edit receipt"
                              >
                                <Edit size={16} />
                              </button>
                              <button
                                className="btn-icon btn-danger"
                                onClick={() => handleDelete(receipt)}
                                title="Delete receipt"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    } catch (error) {
                      console.error('Error rendering receipt:', error, receipt)
                      return null
                    }
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* View Receipt Modal */}
      {viewModal && (
        <div className="modal-overlay" onClick={() => setViewModal(null)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>View Receipt</h2>
              <button className="modal-close" onClick={() => setViewModal(null)}>
                <X size={20} />
              </button>
            </div>
            <div className="modal-body">
              <div className="receipt-details">
                <p><strong>Source:</strong> {viewModal.source || 'N/A'}</p>
                <p><strong>Type:</strong> {viewModal.receipt_type}</p>
                <p><strong>Date:</strong> {formatDate(viewModal.receipt_date)}</p>
                <p><strong>Total:</strong> {formatCurrency(viewModal.total_amount)}</p>
              </div>
              {viewModal.image_data ? (
                <div className="receipt-image-container">
                  <img src={viewModal.image_data} alt="Receipt" className="receipt-image" />
                </div>
              ) : (
                <p className="no-image">No image available for this receipt</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Receipt Modal */}
      {editModal && (
        <div className="modal-overlay" onClick={() => setEditModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Receipt</h2>
              <button className="modal-close" onClick={() => setEditModal(null)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleUpdateReceipt} className="modal-form">
              <div className="form-group">
                <label>Source</label>
                <input
                  type="text"
                  value={editModal.source}
                  onChange={(e) => setEditModal({ ...editModal, source: e.target.value })}
                  placeholder="Store or source name"
                />
              </div>
              <div className="form-group">
                <label>Receipt Type</label>
                <select
                  value={editModal.receipt_type}
                  onChange={(e) => setEditModal({ ...editModal, receipt_type: e.target.value })}
                >
                  <option value="purchase">Purchase</option>
                  <option value="sale">Sale</option>
                </select>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={() => setEditModal(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Update Receipt
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReceiptsPage

