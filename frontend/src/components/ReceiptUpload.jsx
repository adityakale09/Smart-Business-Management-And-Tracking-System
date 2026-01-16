import { useState } from 'react'
import { receiptAPI } from '../api/receipt'
import { getErrorMessage } from '../utils/errorHandler'
import './ReceiptUpload.css'

const ReceiptUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [receiptType, setReceiptType] = useState('')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setResult(null)

      // Create preview for images
      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader()
        reader.onloadend = () => {
          setPreview(reader.result)
        }
        reader.readAsDataURL(selectedFile)
      } else {
        setPreview(null)
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!file) {
      setError('Please select a file')
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const response = await receiptAPI.uploadReceipt(file, receiptType || null)
      setResult(response)
      
      if (response.success && onUploadSuccess) {
        onUploadSuccess(response)
      }
      
      // Reset form after successful upload
      setTimeout(() => {
        setFile(null)
        setPreview(null)
        setReceiptType('')
        document.getElementById('file-input').value = ''
      }, 3000)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to upload receipt')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="receipt-upload">
      <h2>Upload Receipt</h2>
      
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="file-input">Select Receipt (Image or PDF)</label>
          <input
            id="file-input"
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileChange}
            disabled={uploading}
            required
          />
          {file && (
            <p className="file-info">
              Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        {preview && (
          <div className="preview-container">
            <h3>Preview</h3>
            <img src={preview} alt="Receipt preview" className="preview-image" />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="receipt-type">Receipt Type (Optional)</label>
          <select
            id="receipt-type"
            value={receiptType}
            onChange={(e) => setReceiptType(e.target.value)}
            disabled={uploading}
          >
            <option value="">Auto-detect</option>
            <option value="purchase">Purchase (Add Stock)</option>
            <option value="sale">Sale (Deduct Stock)</option>
          </select>
        </div>

        <button type="submit" disabled={uploading || !file} className="upload-button">
          {uploading ? 'Processing...' : 'Upload & Process Receipt'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div className={`result-message ${result.success ? 'success' : 'error'}`}>
          <h3>{result.success ? '✓ Success!' : '✗ Failed'}</h3>
          <p>{result.message}</p>
          
          {result.success && result.items && result.items.length > 0 && (
            <div className="items-table">
              <h4>Extracted Items ({result.items_processed})</h4>
              <table>
                <thead>
                  <tr>
                    <th>Product Name</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.items.map((item, index) => (
                    <tr key={index}>
                      <td>{item.product_name}</td>
                      <td>{item.quantity}</td>
                      <td>₹{item.unit_price.toFixed(2)}</td>
                      <td>
                        <span className={`status-badge ${item.inventory_updated ? 'success' : 'warning'}`}>
                          {item.inventory_updated ? 'Updated' : item.message || 'Pending'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.success && (
            <div className="success-badge">
              <span>✓ Inventory Updated Successfully</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ReceiptUpload

