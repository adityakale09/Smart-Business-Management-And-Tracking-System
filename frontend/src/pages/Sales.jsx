import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { salesAPI } from '../api/sales'
import { inventoryAPI } from '../api/inventory'
import { Plus, Search, X, Trash2, Download, FileText } from 'lucide-react'
import { getErrorMessage } from '../utils/errorHandler'
import { downloadBlob } from '../utils/fileDownload'
import { isBlank, parseNonNegativeFloat, parsePositiveInt } from '../utils/validation'
import './Sales.css'

const normalizeSalesPayload = (payload) => {
  if (!payload) {
    return { items: [], total: 0, page: 1, page_size: 20 }
  }

  if (Array.isArray(payload)) {
    return {
      items: payload,
      total: payload.length,
      page: 1,
      page_size: payload.length
    }
  }

  if (Array.isArray(payload.items)) {
    return payload
  }

  if (Array.isArray(payload.sales)) {
    return {
      items: payload.sales,
      total: payload.sales.length,
      page: payload.page ?? 1,
      page_size: payload.page_size ?? payload.sales.length
    }
  }

  return { items: [], total: 0, page: 1, page_size: 20 }
}

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

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const { data: salesPayload, isLoading, isError, error } = useQuery({
    queryKey: ['sales', { page, page_size: pageSize, search: searchTerm }],
    queryFn: () => salesAPI.getAll({ page, page_size: pageSize, search: searchTerm }),
    onError: (err) => {
      console.error('[Sales] Failed to load sales list:', err)
    },
    keepPreviousData: true,
  })

  const normalizedSales = normalizeSalesPayload(salesPayload)
  const sales = normalizedSales.items || []
  const total = normalizedSales.total || 0

  const { data: summary } = useQuery({
    queryKey: ['sales-summary'],
    queryFn: () => salesAPI.getSummary(30),
  })

  const { data: inventoryData } = useQuery({
    queryKey: ['inventory'],
    queryFn: () => inventoryAPI.getAll(),
  });
  const inventory = inventoryData?.items || [];

  const createSaleMutation = useMutation({
    mutationFn: (saleData) => salesAPI.create(saleData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales'] })
      queryClient.invalidateQueries({ queryKey: ['sales-summary'] })
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
      setPage(1)
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
      queryClient.invalidateQueries({ queryKey: ['sales'] })
      queryClient.invalidateQueries({ queryKey: ['sales-summary'] })
      queryClient.invalidateQueries({ queryKey: ['inventory'] })
    },
  })

  useEffect(() => {
    if (import.meta.env.DEV && salesPayload !== undefined) {
      console.log('[Sales] Sales list response:', salesPayload)
    }
  }, [salesPayload])

  useEffect(() => {
    if (import.meta.env.DEV) {
      console.log('[Sales] Sales rows:', sales)
    }
  }, [sales])

  useEffect(() => {
    setPage(1)
  }, [searchTerm])

  const handleDelete = (sale) => {
    if (window.confirm(`Are you sure you want to delete transaction ${sale.transaction_id}?\n\nCustomer: ${sale.customer_name}\nAmount: ₹${sale.total_amount.toLocaleString('en-IN')}`)) {
      deleteSaleMutation.mutate(sale.id)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validate required fields
    if (isBlank(formData.customer_name)) {
      alert('Please enter a customer name')
      return
    }
    
    if (isBlank(formData.product_id)) {
      alert('Please select a product')
      return
    }
    
    if (isBlank(formData.quantity)) {
      alert('Please enter a quantity')
      return
    }
    
    if (isBlank(formData.unit_price)) {
      alert('Please enter a unit price')
      return
    }
    
    const productId = parsePositiveInt(formData.product_id)
    const quantity = parsePositiveInt(formData.quantity)
    const unitPrice = parseNonNegativeFloat(formData.unit_price)
    
    if (productId === null) {
      alert('Please select a valid product')
      return
    }
    
    if (quantity === null) {
      alert('Please enter a valid quantity (greater than 0)')
      return
    }
    
    if (unitPrice === null) {
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



  const handleExportCSV = async () => {
    try {
      const response = await salesAPI.exportCSV()
      downloadBlob(response, 'text/csv', `sales_${new Date().toISOString().split('T')[0]}.csv`)
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to export CSV')
    }
  }

  const handleExportExcel = async () => {
    try {
      const response = await salesAPI.exportExcel()
      downloadBlob(
        response,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        `sales_${new Date().toISOString().split('T')[0]}.xlsx`
      )
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to export Excel')
    }
  }

  const handleDownloadInvoice = async (saleId) => {
    try {
      const response = await salesAPI.downloadInvoice(saleId)
      downloadBlob(response, 'application/pdf', `invoice_${saleId}.pdf`)
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
        ) : isError ? (
          <div className="error-message">
            {getErrorMessage(error) || 'Failed to load sales.'}
          </div>
        ) : (
          <>
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
              {sales?.length > 0 ? (
                sales.map((sale) => (
                  <tr key={sale.id}>
                    <td>{sale.transaction_id}</td>
                    <td>{sale.customer_name}</td>
                    <td>{sale.product_id ?? 'N/A'}</td>
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

          <div className="pagination-controls">
            <button disabled={page === 1} onClick={() => setPage(page - 1)}>Prev</button>
            <span>Page {page} of {Math.ceil(total / pageSize) || 1}</span>
            <button disabled={page * pageSize >= total} onClick={() => setPage(page + 1)}>Next</button>
            <select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(1) }}>
              {[10, 20, 50, 100].map(size => (
                <option key={size} value={size}>{size} / page</option>
              ))}
            </select>
          </div>
          </>
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
                <label htmlFor="customer_name">Customer Name *</label>
                <input
                  id="customer_name"
                  type="text"
                  placeholder="Enter customer name"
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="product_id">Product *</label>
                <select
                  id="product_id"
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
                <label htmlFor="quantity">Quantity *</label>
                <input
                  id="quantity"
                  type="number"
                  min="1"
                  placeholder="Enter quantity"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="unit_price">Unit Price *</label>
                <input
                  id="unit_price"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="Enter unit price"
                  value={formData.unit_price}
                  onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="payment_method">Payment Method *</label>
                <select
                  id="payment_method"
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
                <label htmlFor="notes">Notes</label>
                <textarea
                  id="notes"
                  placeholder="Additional notes (optional)"
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

