import { useState, useEffect, useCallback } from 'react'
import { receiptAPI } from '../api/receipt'
import ReceiptUpload from '../components/ReceiptUpload'
import { getErrorMessage } from '../utils/errorHandler'
import { Trash2, Edit, Eye, X, Download, BarChart3 } from 'lucide-react'
import './ReceiptsPage.css'

const ReceiptsPage = () => {
  const [receipts, setReceipts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [viewModal, setViewModal] = useState(null)
  const [editModal, setEditModal] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(true)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    loadReceipts()
  }, [filter, categoryFilter, startDate, endDate])

  useEffect(() => {
    loadAnalytics()
  }, [startDate, endDate])

  const loadAnalytics = async () => {
    try {
      setAnalyticsLoading(true)
      const params = {}
      if (startDate) {
        params.start_date = startDate
      }
      if (endDate) {
        params.end_date = endDate
      }
      const data = await receiptAPI.getAnalytics(params)
      setAnalytics(data)
    } catch (err) {
      console.error('Error loading analytics:', err)
      setAnalytics(null)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const loadReceipts = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {}
      if (filter !== 'all') {
        params.receipt_type = filter
      }
      if (categoryFilter) {
        params.category = categoryFilter
      }
      if (startDate) {
        params.start_date = startDate
      }
      if (endDate) {
        params.end_date = endDate
      }
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
      receipt_type: receipt.receipt_type || 'purchase',
      category: receipt.category || '',
      notes: receipt.notes || ''
    })
  }

  const handleUpdateReceipt = async (e) => {
    e.preventDefault()
    try {
      const formData = new FormData()
      formData.append('source', editModal.source)
      formData.append('receipt_type', editModal.receipt_type)
      formData.append('category', editModal.category)
      formData.append('notes', editModal.notes)
      
      await receiptAPI.updateReceipt(editModal.id, formData)
      setEditModal(null)
      loadReceipts()
    } catch (err) {
      alert(getErrorMessage(err) || 'Failed to update receipt')
    }
  }

  const handleExport = async (format) => {
    try {
      setExporting(true)
      const params = { format }
      if (startDate) {
        params.start_date = startDate
      }
      if (endDate) {
        params.end_date = endDate
      }
      if (filter !== 'all') {
        params.receipt_type = filter
      }
      if (categoryFilter) {
        params.category = categoryFilter
      }
      
      if (format === 'json') {
        const data = await receiptAPI.exportReceipts(params)
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `receipts_export_${new Date().toISOString().slice(0, 10)}.json`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const blob = await receiptAPI.exportReceipts({ ...params, format: 'csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `receipts_export_${new Date().toISOString().slice(0, 10)}.csv`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      alert(getErrorMessage(err) || 'Failed to export receipts')
    } finally {
      setExporting(false)
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
          <label>Category:</label>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="">All Categories</option>
            <option value="grocery">Grocery</option>
            <option value="electronics">Electronics</option>
            <option value="office_supplies">Office Supplies</option>
            <option value="restaurant">Restaurant</option>
            <option value="transportation">Transportation</option>
            <option value="utilities">Utilities</option>
            <option value="medical">Medical</option>
            <option value="other">Other</option>
          </select>
          <label>From:</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="date-filter-input"
          />
          <label>To:</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="date-filter-input"
          />
          <div className="export-buttons">
            <button
              className="btn-icon btn-export"
              onClick={() => handleExport('csv')}
              disabled={exporting}
              title="Export as CSV"
            >
              <Download size={16} />
              <span>CSV</span>
            </button>
            <button
              className="btn-icon btn-export"
              onClick={() => handleExport('json')}
              disabled={exporting}
              title="Export as JSON"
            >
              <Download size={16} />
              <span>JSON</span>
            </button>
          </div>
        </div>
      </div>

      {/* Analytics Summary Section */}
      {analytics && !analyticsLoading && (
        <div className="analytics-summary">
          <div className="analytics-header">
            <BarChart3 size={20} />
            <h3>Receipt Analytics</h3>
          </div>
          <div className="analytics-cards">
            <div className="analytics-card">
              <span className="analytics-label">Total Receipts</span>
              <span className="analytics-value">{analytics.total_receipts}</span>
            </div>
            <div className="analytics-card">
              <span className="analytics-label">Total Amount</span>
              <span className="analytics-value">{formatCurrency(analytics.total_amount)}</span>
            </div>
            <div className="analytics-card">
              <span className="analytics-label">Total Items</span>
              <span className="analytics-value">{analytics.total_items}</span>
            </div>
            <div className="analytics-card">
              <span className="analytics-label">Avg per Receipt</span>
              <span className="analytics-value">{formatCurrency(analytics.average_per_receipt)}</span>
            </div>
          </div>
          {analytics.category_breakdown && analytics.category_breakdown.length > 0 && (
            <div className="analytics-breakdown">
              <h4>Category Breakdown</h4>
              <div className="breakdown-bars">
                {analytics.category_breakdown.map((cat, i) => (
                  <div key={i} className="breakdown-item">
                    <div className="breakdown-label">
                      <span>{cat.category.replace('_', ' ')}</span>
                      <span>{formatCurrency(cat.total_amount)} ({cat.percentage}%)</span>
                    </div>
                    <div className="breakdown-bar-track">
                      <div
                        className="breakdown-bar-fill"
                        style={{ width: `${Math.max(cat.percentage, 2)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {analytics.top_sources && analytics.top_sources.length > 0 && (
            <div className="analytics-sources">
              <h4>Top Sources</h4>
              <div className="sources-list">
                {analytics.top_sources.map((src, i) => (
                  <div key={i} className="source-item">
                    <span className="source-name">{src.source}</span>
                    <span className="source-count">{src.count} receipts</span>
                    <span className="source-amount">{formatCurrency(src.total_amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {analyticsLoading && (
        <div className="analytics-summary analytics-loading">
          <div className="loading">Loading analytics...</div>
        </div>
      )}

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
                    <th>Category</th>
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
                          <td>
                            {receipt.category ? (
                              <span className={`category-badge ${receipt.category}`}>
                                {receipt.category.replace('_', ' ')}
                              </span>
                            ) : (
                              <span className="no-category">—</span>
                            )}
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
                <p><strong>Category:</strong> {viewModal.category || 'Uncategorized'}</p>
                <p><strong>Date:</strong> {formatDate(viewModal.receipt_date)}</p>
                <p><strong>Total:</strong> {formatCurrency(viewModal.total_amount)}</p>
                {viewModal.notes && <p><strong>Notes:</strong> {viewModal.notes}</p>}
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
              <div className="form-group">
                <label>Category</label>
                <select
                  value={editModal.category}
                  onChange={(e) => setEditModal({ ...editModal, category: e.target.value })}
                >
                  <option value="">Uncategorized</option>
                  <option value="grocery">Grocery</option>
                  <option value="electronics">Electronics</option>
                  <option value="office_supplies">Office Supplies</option>
                  <option value="restaurant">Restaurant</option>
                  <option value="transportation">Transportation</option>
                  <option value="utilities">Utilities</option>
                  <option value="medical">Medical</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={editModal.notes}
                  onChange={(e) => setEditModal({ ...editModal, notes: e.target.value })}
                  placeholder="Optional notes about this receipt"
                  rows={3}
                />
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

