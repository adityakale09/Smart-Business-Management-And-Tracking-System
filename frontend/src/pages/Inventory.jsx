import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { inventoryAPI } from '../api/inventory'
import { Package, AlertTriangle, Search, X, Edit2, Trash2, Download } from 'lucide-react'
import { getErrorMessage } from '../utils/errorHandler'
import { downloadBlob } from '../utils/fileDownload'
import { isBlank, parseNonNegativeFloat, parseNonNegativeInt } from '../utils/validation'
import './Inventory.css'

const Inventory = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [lowStockFilter, setLowStockFilter] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showRestockModal, setShowRestockModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedItem, setSelectedItem] = useState(null)
  const [restockQuantity, setRestockQuantity] = useState('')
  const [restockNotes, setRestockNotes] = useState('')
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    category: '',
    quantity: '',
    reorder_level: '10',
    unit_price: '',
    supplier: '',
    location: ''
  })
  const queryClient = useQueryClient()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const { data, isLoading, error: inventoryError } = useQuery({
    queryKey: ['inventory', { low_stock: lowStockFilter, page, page_size: pageSize, search: searchTerm, category: selectedCategory }],
    queryFn: () => inventoryAPI.getAll({ low_stock: lowStockFilter, page, page_size: pageSize, search: searchTerm, category: selectedCategory || undefined }),
    onError: (error) => {
      console.error('Error loading inventory:', error)
    },
    keepPreviousData: true,
  })

  const inventory = data?.items || []
  const total = data?.total || 0
  const categories = [...new Set((data?.items || []).map(i => i.category).filter(Boolean))]

  const createProductMutation = useMutation({
    mutationFn: async (productData) => {
      try {
        const response = await inventoryAPI.create(productData)
        return response
      } catch (error) {
        console.error('Error in mutation function:', error)
        throw error
      }
    },
    onSuccess: () => {
      try {
        // Invalidate queries to refetch data
        queryClient.invalidateQueries(['inventory']).catch(err => {
          console.error('Error invalidating queries:', err)
        })
        // Close modal and reset form
        setShowModal(false)
        resetForm()
      } catch (error) {
        console.error('Error in success handler:', error)
        // Still close modal even if there's an error
        setShowModal(false)
      }
    },
    onError: (error) => {
      console.error('Error creating product:', error)
      // Don't close modal on error so user can see the error message
    },
  })

  const updateProductMutation = useMutation({
    mutationFn: async ({ id, productData }) => {
      const response = await inventoryAPI.update(id, productData)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['inventory'])
      setShowEditModal(false)
      setSelectedItem(null)
      resetForm()
      alert('Product updated successfully!')
    },
    onError: (error) => {
      console.error('Error updating product:', error)
      alert(`Error updating product: ${error.message}`)
    }
  })

  const deleteProductMutation = useMutation({
    mutationFn: async (item) => {
      try {
        await inventoryAPI.delete(item)
      } catch (error) {
        // If already deleted (404), treat as success
        if (error?.response?.status === 404) {
          return;
        }
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['inventory'])
      alert('Product deleted successfully!')
    },
    onError: (error) => {
      console.error('Error deleting product:', error)
      // Handle network/empty response errors gracefully
      if (error?.response?.status === 404) {
        queryClient.invalidateQueries(['inventory'])
        alert('Product already deleted.')
        return;
      }
      const serverDetail = error?.response?.data?.detail
      const detailText = typeof serverDetail === 'string' ? serverDetail : getErrorMessage(error)
      alert(`Error deleting product: ${detailText || error.message}`)
    }
  })

  const restockProductMutation = useMutation({
    mutationFn: async ({ id, quantity, notes }) => {
      const response = await inventoryAPI.restock(id, quantity, notes)
      return response
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['inventory'])
      setShowRestockModal(false)
      setSelectedItem(null)
      setRestockQuantity('')
      setRestockNotes('')
      alert('Product restocked successfully!')
    },
    onError: (error) => {
      console.error('Error restocking product:', error)
      const serverDetail = error?.response?.data?.detail
      const detailText = typeof serverDetail === 'string' ? serverDetail : getErrorMessage(error)
      alert(`Error restocking product: ${detailText || error.message}`)
    }
  })

  const resetForm = () => {
    setFormData({
      sku: '',
      name: '',
      description: '',
      category: '',
      quantity: '',
      reorder_level: '10',
      unit_price: '',
      supplier: '',
      location: ''
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    // Validate required fields
    if (isBlank(formData.sku)) {
      alert('Please enter a SKU')
      return
    }
    
    if (isBlank(formData.name)) {
      alert('Please enter a product name')
      return
    }
    
    if (isBlank(formData.unit_price)) {
      alert('Please enter a unit price')
      return
    }
    
    const unitPrice = parseNonNegativeFloat(formData.unit_price)
    if (unitPrice === null) {
      alert('Please enter a valid unit price')
      return
    }
    
    // Parse quantity and reorder_level, ensuring they're valid numbers
    const quantity = parseNonNegativeInt(formData.quantity, 0)
    if (quantity === null) {
      alert('Please enter a valid quantity (0 or greater)')
      return
    }
    
    const reorderLevel = parseNonNegativeInt(formData.reorder_level, 10)
    if (reorderLevel === null) {
      alert('Please enter a valid reorder level (0 or greater)')
      return
    }
    
    // Build product data, only including non-empty optional fields
    const productData = {
      sku: formData.sku.trim(),
      name: formData.name.trim(),
      unit_price: unitPrice,
      quantity: quantity,
      reorder_level: reorderLevel
    }
    
    // Add optional fields only if they have values
    if (formData.description && formData.description.trim()) {
      productData.description = formData.description.trim()
    }
    
    if (formData.category && formData.category.trim()) {
      productData.category = formData.category.trim()
    }
    
    if (formData.supplier && formData.supplier.trim()) {
      productData.supplier = formData.supplier.trim()
    }
    
    if (formData.location && formData.location.trim()) {
      productData.location = formData.location.trim()
    }

    createProductMutation.mutate(productData)
  }

  const handleUpdate = (e) => {
    e.preventDefault()
    
    // Similar validation as handleSubmit
    if (isBlank(formData.name)) {
      alert('Please enter a product name')
      return
    }
    
    if (isBlank(formData.unit_price)) {
      alert('Please enter a unit price')
      return
    }
    
    const unitPrice = parseNonNegativeFloat(formData.unit_price)
    if (unitPrice === null) {
      alert('Please enter a valid unit price')
      return
    }
    
    const quantity = parseNonNegativeInt(formData.quantity, 0)
    if (quantity === null) {
      alert('Please enter a valid quantity (0 or greater)')
      return
    }
    
    const reorderLevel = parseNonNegativeInt(formData.reorder_level, 10)
    if (reorderLevel === null) {
      alert('Please enter a valid reorder level (0 or greater)')
      return
    }
    
    const productData = {
      name: formData.name.trim(),
      unit_price: unitPrice,
      quantity: quantity,
      reorder_level: reorderLevel
    }
    
    // Add optional fields only if they have values
    if (formData.description && formData.description.trim()) {
      productData.description = formData.description.trim()
    }
    
    if (formData.category && formData.category.trim()) {
      productData.category = formData.category.trim()
    }
    
    if (formData.supplier && formData.supplier.trim()) {
      productData.supplier = formData.supplier.trim()
    }
    
    if (formData.location && formData.location.trim()) {
      productData.location = formData.location.trim()
    }
    
    updateProductMutation.mutate({ id: selectedItem.id, productData })
  }

  const handleEdit = (item) => {
    setSelectedItem(item)
    setFormData({
      sku: item.sku || '',
      name: item.name || '',
      description: item.description || '',
      category: item.category || '',
      quantity: item.quantity?.toString() || '0',
      reorder_level: item.reorder_level?.toString() || '10',
      unit_price: item.unit_price?.toString() || '',
      supplier: item.supplier || '',
      location: item.location || ''
    })
    setShowEditModal(true)
  }

  const handleDelete = (item) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      deleteProductMutation.mutate(item)
    }
  }

  const handleRestock = (item) => {
    setSelectedItem(item)
    setRestockQuantity('')
    setRestockNotes('')
    setShowRestockModal(true)
  }

  const handleRestockSubmit = (e) => {
    e.preventDefault()
    const quantity = parseInt(restockQuantity)
    if (isNaN(quantity) || quantity <= 0) {
      alert('Please enter a valid quantity (greater than 0)')
      return
    }
    restockProductMutation.mutate({
      id: selectedItem.id,
      quantity,
      notes: restockNotes.trim() || undefined
    })
  }



  const handleExportCSV = async () => {
    try {
      const response = await inventoryAPI.exportCSV()
      downloadBlob(response, 'text/csv', `inventory_${new Date().toISOString().split('T')[0]}.csv`)
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to export CSV')
    }
  }

  const handleExportExcel = async () => {
    try {
      const response = await inventoryAPI.exportExcel()
      downloadBlob(
        response,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        `inventory_${new Date().toISOString().split('T')[0]}.xlsx`
      )
    } catch (error) {
      alert(getErrorMessage(error) || 'Failed to export Excel')
    }
  }

  return (
    <div className="inventory-page">
      <div className="page-header">
        <div>
          <h1>Inventory Management</h1>
          <p>Manage your product inventory and stock levels</p>
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
            <Package size={20} />
            Add Product
          </button>
        </div>
      </div>

      <div className="inventory-controls">
        <div className="inventory-controls-row">
          <div className="search-box">
            <Search size={20} />
            <input
              type="text"
              placeholder="Search by name or SKU..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          {categories.length > 0 && (
            <select
              className="category-filter"
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setPage(1) }}
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          )}
        </div>
        <div className="inventory-controls-row">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={lowStockFilter}
              onChange={(e) => setLowStockFilter(e.target.checked)}
            />
            <span>Show low stock only (≤5)</span>
          </label>
        </div>
      </div>

      <div className="inventory-table-container">
        {inventoryError && (
          <div className="error-message">
            <strong>Error:</strong> {getErrorMessage(inventoryError) || 'Failed to load inventory'}
          </div>
        )}
        {isLoading ? (
          <div className="loading">Loading inventory...</div>
        ) : (
          <>
          <table className="inventory-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Category</th>
                <th>Quantity</th>
                <th>Reorder Level</th>
                <th>Unit Price</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {inventory && inventory.length > 0 ? (
                inventory.map((item) => (
                  <tr 
                    key={item.id} 
                    className={`${item.quantity <= 5 ? 'low-stock' : ''} ${item.quantity <= 0 ? 'out-of-stock-row' : ''} ${item.recently_updated ? 'recently-updated' : ''}`}
                    onClick={(e) => { if (!e.target.closest('.action-buttons') && !e.target.closest('.btn-sm')) handleEdit(item) }}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>{item.sku}</td>
                    <td>
                      {item.name}
                      {item.recently_updated && (
                        <span className="updated-badge" title="Recently updated from receipt">
                          New
                        </span>
                      )}
                    </td>
                    <td>{item.category || 'N/A'}</td>
                    <td>
                      <span className={item.quantity <= 5 ? 'quantity-low' : ''}>
                        {item.quantity || 0}
                      </span>
                    </td>
                    <td>{item.reorder_level || 0}</td>
                    <td>₹{(item.unit_price || 0).toFixed(2)}</td>
                    <td>
                      <span className={`status-badge ${item.status || 'active'}`}>
                        {item.status === 'low_stock' || item.status === 'out_of_stock' ? (
                          <>
                            <AlertTriangle size={14} />
                            {item.status === 'out_of_stock' ? 'Out of Stock' : 'Low Stock'}
                          </>
                        ) : (
                          (item.status || 'active').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                        )}
                      </span>
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button 
                          className="btn-sm btn-restock" 
                          onClick={() => handleRestock(item)}
                          title="Restock"
                        >
                          <Package size={16} />
                        </button>
                        <button 
                          className="btn-sm btn-edit" 
                          onClick={() => handleEdit(item)}
                          title="Edit"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button 
                          className="btn-sm btn-delete" 
                          onClick={() => handleDelete(item)}
                          title="Delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="no-data">
                    No inventory items found
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
              <h2>Add New Product</h2>
              <button className="modal-close" onClick={() => setShowModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label htmlFor="sku">SKU *</label>
                <input
                  id="sku"
                  type="text"
                  placeholder="Enter SKU"
                  value={formData.sku}
                  onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="name">Product Name *</label>
                <input
                  id="name"
                  type="text"
                  placeholder="Enter product name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  placeholder="Product description (optional)"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows="3"
                />
              </div>
              <div className="form-group">
                <label htmlFor="category">Category</label>
                <input
                  id="category"
                  type="text"
                  placeholder="Category (optional)"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="quantity">Quantity</label>
                  <input
                    id="quantity"
                    type="number"
                    min="0"
                    placeholder="0"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reorder_level">Reorder Level</label>
                  <input
                    id="reorder_level"
                    type="number"
                    min="0"
                    placeholder="10"
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })}
                  />
                </div>
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
                <label htmlFor="supplier">Supplier</label>
                <input
                  id="supplier"
                  type="text"
                  placeholder="Supplier (optional)"
                  value={formData.supplier}
                  onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="location">Location</label>
                <input
                  id="location"
                  type="text"
                  placeholder="Location (optional)"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                />
              </div>
              {createProductMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(createProductMutation.error) || 'Failed to create product'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createProductMutation.isLoading}>
                  {createProductMutation.isLoading ? 'Creating...' : 'Add Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEditModal && selectedItem && (
        <div className="modal-overlay" onClick={() => setShowEditModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Product</h2>
              <button className="modal-close" onClick={() => setShowEditModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleUpdate} className="modal-form">
              <div className="form-group">
                <label>SKU (Read-only)</label>
                <input
                  type="text"
                  value={formData.sku}
                  disabled
                  style={{ cursor: 'not-allowed' }}
                />
              </div>
              <div className="form-group">
                <label>Product Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows="3"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Category</label>
                  <input
                    type="text"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Unit Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.unit_price}
                    onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Quantity *</label>
                  <input
                    type="number"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Reorder Level *</label>
                  <input
                    type="number"
                    value={formData.reorder_level}
                    onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Supplier</label>
                  <input
                    type="text"
                    value={formData.supplier}
                    onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  />
                </div>
              </div>
              {updateProductMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(updateProductMutation.error) || 'Failed to update product'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowEditModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={updateProductMutation.isLoading}>
                  {updateProductMutation.isLoading ? 'Updating...' : 'Update Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showRestockModal && selectedItem && (
        <div className="modal-overlay" onClick={() => setShowRestockModal(false)}>
          <div className="modal-content modal-small" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Restock: {selectedItem.name}</h2>
              <button className="modal-close" onClick={() => setShowRestockModal(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleRestockSubmit} className="modal-form">
              <div className="restock-info">
                <div className="info-row">
                  <span className="label">Current Stock:</span>
                  <span className="value">{selectedItem.quantity}</span>
                </div>
                <div className="info-row">
                  <span className="label">SKU:</span>
                  <span className="value">{selectedItem.sku}</span>
                </div>
              </div>
              <div className="form-group">
                <label>Quantity to Add *</label>
                <input
                  type="number"
                  min="1"
                  value={restockQuantity}
                  onChange={(e) => setRestockQuantity(e.target.value)}
                  placeholder="Enter quantity"
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label>Notes (optional)</label>
                <textarea
                  value={restockNotes}
                  onChange={(e) => setRestockNotes(e.target.value)}
                  placeholder="Add notes about this restock..."
                  rows="3"
                />
              </div>
              {restockQuantity && (
                <div className="restock-preview">
                  <strong>New Stock Level:</strong> {selectedItem.quantity + parseInt(restockQuantity || 0)}
                </div>
              )}
              {restockProductMutation.isError && (
                <div className="error-message">
                  {getErrorMessage(restockProductMutation.error) || 'Failed to restock product'}
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowRestockModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={restockProductMutation.isLoading}>
                  {restockProductMutation.isLoading ? 'Restocking...' : 'Confirm Restock'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Inventory
