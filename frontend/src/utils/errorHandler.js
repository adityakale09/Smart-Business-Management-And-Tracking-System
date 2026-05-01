/**
 * Extract error message from API error response
 * Handles FastAPI validation errors which can be arrays of objects
 */
export const getErrorMessage = (error) => {
  if (!error) return 'An unknown error occurred'

  if (error.userMessage) {
    return error.userMessage
  }

  if (error.code === 'OFFLINE') {
    return 'You are offline. Reconnect to the internet and retry.'
  }

  if (error.code === 'ECONNABORTED') {
    return 'Request timed out. Please check your internet and try again.'
  }

  if (error.code === 'ERR_NETWORK') {
    return 'Network error. Please verify your internet connection and retry.'
  }

  if (error.code === 'ERR_CANCELED') {
    return 'Request cancelled. You can retry once your connection is stable.'
  }
  
  // Check if it's an axios error with response
  if (error.response?.data) {
    const data = error.response.data
    
    // If detail is a string, return it
    if (typeof data.detail === 'string') {
      return data.detail
    }
    
    // If detail is an array (validation errors)
    if (Array.isArray(data.detail)) {
      return data.detail
        .map((err) => {
          if (typeof err === 'string') return err
          // Handle new validation error format
          if (err.field && err.message) {
            return `${err.field}: ${err.message}`
          }
          if (err.loc && err.msg) {
            const field = Array.isArray(err.loc) ? err.loc.join('.') : err.loc
            return `${field}: ${err.msg}`
          }
          if (err.msg) return err.msg
          if (err.message) return err.message
          return JSON.stringify(err)
        })
        .join(', ')
    }
    
    // If detail is an object, try to extract message
    if (typeof data.detail === 'object') {
      if (data.detail.msg) return data.detail.msg
      if (data.detail.message) return data.detail.message
      return 'Validation error occurred'
    }
    
    // If data itself is an array (validation errors at root level)
    if (Array.isArray(data)) {
      return data
        .map((err) => {
          if (typeof err === 'string') return err
          if (err.msg) return err.msg
          if (err.message) return err.message
          return JSON.stringify(err)
        })
        .join(', ')
    }
    
    // If data has a message property
    if (data.message) {
      return data.message
    }
  }
  
  // If error has a message property
  if (error.message) {
    return error.message
  }
  
  // Fallback
  return 'An error occurred. Please try again.'
}

