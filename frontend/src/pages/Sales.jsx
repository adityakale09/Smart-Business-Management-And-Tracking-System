import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { salesAPI } from '../api/sales'
import { inventoryAPI } from '../api/inventory'
import { Plus, Search, X, Trash2, Download, FileText } from 'lucide-react'
import { getErrorMessage } from '../utils/errorHandler'
import './Sales.css'

const Sales = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    customer_name: '',
    product_id: '',
    quantity: '',
    unit_price: '',
    payment_method: 'cash',
    notes: ''
  })
  const queryClient = useQueryClient()

  const { data: sales, isLoading } = useQuery({
    queryKey: ['sales'],
    queryFn: () => salesAPI.getAll(),
  })

  const { data: summary } = useQuery({
    queryKey: ['sales-summary'],
    queryFn: () => salesAPI.getSummary(30),
  })

  const { data: inventory } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => inventoryAPI.getAll(),
  })

  const createSaleMutation = useMutation({
    mutationFn: (saleData) => salesAPI.create(saleData),
    onSuccess: () => {
      queryClient.invalidateQueries(['sales'])
      queryClient.invalidateQueries(['sales-summary'])
      queryClient.invalidateQueries(['inventory'])
      setShowModal(false)
      setFormData({
        customer_name: '',
        product_id: '',
        quantity: '',
        unit_price: '',
        payment_method: 'cash',
        notes: ''
      })
    },
  })

  const deleteSaleMutation = useMutation({
    mutationFn: (saleId) => salesAPI.delete(saleId),
    onSuccess: () => {
      queryClient.invalidateQueries(['sales'])
      queryClient.invalidateQueries(['sales-summary'])
      queryClient.invalidateQueries(['inventory'])
    },
  })

  const handleDelete = (sale) => {
    if (window.confirm(`Are you sure you want to delete transaction ${sale.transaction_id}?\n\nCustomer: ${sale.customer_name}\nAmount: ₹${sale.total_amount.toLocaleString('en-IN')}`)) {
      deleteSaleMutation.mutate(sale.id)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validate required fields
    if (!formData.customer_name || !formData.customer_name.trim()) {
      alert('Please enter a customer name')
      return
    }
    
    if (!formData.product_id || formData.product_id === '') {
      alert('Please select a product')
      return
    }
    
    if (!formData.quantity || formData.quantity === '') {
      alert('Please enter a quantity')
      return
    }
    
    if (!formData.unit_price || formData.unit_price === '') {
      alert('Please enter a unit price')
      return
    }
    
    const productId = parseInt(formData.product_id)
    const quantity = parseInt(formData.quantity)
    const unitPrice = parseFloat(formData.unit_price)
    
    if (isNaN(productId) || productId <= 0) {
      alert('Please select a valid product')
      return
    }
    
    if (isNaN(quantity) || quantity <= 0) {
      alert('Please enter a valid quantity (greater than 0)')
      return
    }
    
    if (isNaN(unitPrice) || unitPrice < 0) {
      alert('Please enter a valid unit price')
      return
    }
    
    const saleData = {
      customer_name: formData.customer_name.trim(),
      product_id: productId,
      quantity: quantity,
      unit_price: unitPrice,
      payment_method: formData.payment_method || 'cash'
    }
    
    // Add notes only if provided
    if (formData.notes && formData.notes.trim()) {
      saleData.notes = formData.notes.trim()
    }
    
    createSaleMutation.mutate(saleData)
  }

  const handleProductChange = (e) => {
    const productId = e.target.value
    setFormData({ ...formData, product_id: productId })
    const selectedProduct = inventory?.find(p => p.id === parseInt(productId))
    if (selectedProduct) {
      setFormData(prev => ({ ...prev, unit_price: selectedProduct.unit_price }))
    }
  }

  const filteredSales = sales?.filter((sale) =>
    sale.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    sale.transaction_id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleExportCSV = async () => {
    try {
      const response = await salesAPI.exportCSV()
      const blob = new Blob([response], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sales_${new Date().toISOString().split('T')[0]}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to export CSV')
    }
  }

  const handleExportExcel = async () => {
    try {
      const response = await salesAPI.exportExcel()
      const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `sales_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to export Excel')
    }
  }

  const handleDownloadInvoice = async (saleId) => {
    try {
      const response = await salesAPI.downloadInvoice(saleId)
      const blob = new Blob([response], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice_${saleId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to download invoice')
    }
  }

  return (
    <div className="sales-page">
      <div className="page-header">
        <div>
          <h1>Sales Management</h1>
          <p>Track and manage all sales transactions</p>
        </div>
        <div className="header-actions">
          <button className="btn-secondary btn-icon" onClick={handleExportCSV} title="Export to CSV">
            <Download size={18} />
            CSV
          </button>
          <button className="btn-secondary btn-icon" onClick={handleExportExcel} title="Export to Excel">
            <Download size={18} />
            Excel
          </button>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={20} />
            New Sale
          </button>
        </div>
      </div>

      {summary && (
        <div className="summary-cards">
          <div className="summary-card">
            <h3>Total Revenue</h3>
            <p className="summary-value">₹{summary.total_revenue.toLocaleString('en-IN')}</p>
            <span className="summary-label">Last 30 days</span>
          </div>
          <div className="summary-card">
            <h3>Total Sales</h3>
            <p className="summary-value">{summary.total_sales}</p>
            <span className="summary-label">Transactions</span>
          </div>
          <div className="summary-card">
            <h3>Average Sale</h3>
            <p className="summary-value">₹{summary.average_sale.toFixed(2)}</p>
            <span className="summary-label">Per transaction</span>
          </div>
        </div>
      )}

      <div className="sales-controls">
        <div className="search-box">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search by customer or transaction ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="sales-table-container">
        {isLoading ? (
          <div className="loading">Loading sales...</div>
        ) : (
          <table className="sales-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Customer</th>
                <th>Product ID</th>
                <th>Quantity</th>
                <th>Amount</th>
                <th>Payment Method</th>
                <th>Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredSales?.length > 0 ? (
                filteredSales.map((sale) => (
                  <tr key={sale.id}>
                    <td>{sale.transaction_id}</td>
                    <td>{sale.customer_name}</td>
                    <td>{sale.product_id}</td>
                    <td>{sale.quantity}</td>
                    <td>₹{sale.total_amount.toFixed(2)}</td>
                    <td>
                      <span className="badge">{sale.payment_method}</span>
                    </td>
                    <td>{new Date(sale.created_at).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-badge ${sale.status}`}>
                        {sale.status}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="btn-icon btn-secondary"
                          onClick={() => handleDownloadInvoice(sale.id)}
                          title="Download Invoice"
                        >
                          <FileText size={16} />
                        </button>
                        <button
                          className="btn-icon btn-danger"
                          onClick={() => handleDelete(sale)}
                          disabled={deleteSaleMutation.isLoading}
                          title="Delete transaction"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="9" className="no-data">
                    No sales found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Sale</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label>Customer Name *</label>
                <input
                  type="text"
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Product *</label>
                <select
                  value={formData.product_id}
                  onChange={handleProductChange}
                  required
                >
                  <option value="">Select a product</option>
                  {inventory?.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.name} (Stock: {product.quantity}) - ${product.unit_price}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity *</label>
                <input
                  type="number"
                  min="1"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Unit Price *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.unit_price}
                  onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Payment Method *</label>
                <select
                  value={formData.payment_method}
                  onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  required
                >
                  <option value="cash">Cash</option>
                  <option value="card">Card</option>
                  <option value="online">Online</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows="3"
                />
              </div>
              {createSaleMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(createSaleMutation.error) || 'Failed to create sale'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createSaleMutation.isLoading}>
                  {createSaleMutation.isLoading ? 'Creating...' : 'Create Sale'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sales








