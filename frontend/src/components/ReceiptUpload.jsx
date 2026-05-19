import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { receiptAPI } from '../api/receipt'
import { getErrorMessage } from '../utils/errorHandler'
import { fetchLiveExchangeRate, formatCurrencyAmount, SUPPORTED_CURRENCIES } from '../utils/currency'
import './ReceiptUpload.css'

const MIN_CROP_SIZE = 0.06

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

const isLikelyImageFile = (candidateFile) => {
  if (!candidateFile) {
    return false
  }

  const mime = String(candidateFile.type || '').toLowerCase()
  if (mime.startsWith('image/')) {
    return true
  }

  const name = String(candidateFile.name || '').toLowerCase()
  return /\.(jpg|jpeg|png|webp|bmp|gif|heic|heif)$/i.test(name)
}

const buildEditSignature = ({ file, zoom, rotation, brightness, contrast, saturation, sharpness, grayscale, cropRect }) => {
  const fileName = file?.name || ''
  const fileSize = file?.size || 0
  const fileStamp = file?.lastModified || 0

  return JSON.stringify({
    fileName,
    fileSize,
    fileStamp,
    zoom,
    rotation,
    brightness,
    contrast,
    saturation,
    sharpness,
    grayscale,
    cropRect,
  })
}

const buildFilterString = ({ brightness, contrast, saturation, grayscale }) => {
  return [
    `brightness(${brightness}%)`,
    `contrast(${contrast}%)`,
    `saturate(${saturation}%)`,
    grayscale ? 'grayscale(100%)' : 'grayscale(0%)',
  ].join(' ')
}

const loadImageFromDataUrl = (dataUrl) => {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('Failed to load image for editing'))
    image.src = dataUrl
  })
}

const getPointerPoint = (event) => {
  if (event.touches && event.touches[0]) {
    return event.touches[0]
  }
  if (event.changedTouches && event.changedTouches[0]) {
    return event.changedTouches[0]
  }
  return event
}

const applySharpenToContext = (ctx, width, height, amount) => {
  if (!amount || amount <= 0) {
    return
  }

  const source = ctx.getImageData(0, 0, width, height)
  const destination = ctx.createImageData(width, height)
  const srcData = source.data
  const dstData = destination.data
  const kernel = [0, -1, 0, -1, 5, -1, 0, -1, 0]

  for (let y = 1; y < height - 1; y += 1) {
    for (let x = 1; x < width - 1; x += 1) {
      const index = (y * width + x) * 4
      const channelValues = [0, 0, 0]
      let kernelIndex = 0

      for (let ky = -1; ky <= 1; ky += 1) {
        for (let kx = -1; kx <= 1; kx += 1) {
          const sampleIndex = ((y + ky) * width + (x + kx)) * 4
          const kernelWeight = kernel[kernelIndex]
          kernelIndex += 1
          channelValues[0] += srcData[sampleIndex] * kernelWeight
          channelValues[1] += srcData[sampleIndex + 1] * kernelWeight
          channelValues[2] += srcData[sampleIndex + 2] * kernelWeight
        }
      }

      for (let channel = 0; channel < 3; channel += 1) {
        const original = srcData[index + channel]
        const sharpened = clamp(channelValues[channel], 0, 255)
        dstData[index + channel] = clamp(original * (1 - amount) + sharpened * amount, 0, 255)
      }
      dstData[index + 3] = srcData[index + 3]
    }
  }

  ctx.putImageData(destination, 0, 0)
}

const ReceiptUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [receiptType, setReceiptType] = useState('')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [previewResult, setPreviewResult] = useState(null)
  const [error, setError] = useState(null)
  const [sourceCurrencyOverride, setSourceCurrencyOverride] = useState('')
  const [displayCurrency, setDisplayCurrency] = useState('')
  const [exchangeRate, setExchangeRate] = useState(1)
  const [rateLoading, setRateLoading] = useState(false)
  const [rateError, setRateError] = useState(null)
  const [isOnline, setIsOnline] = useState(() => (typeof navigator === 'undefined' ? true : navigator.onLine))

  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [brightness, setBrightness] = useState(110)
  const [contrast, setContrast] = useState(120)
  const [saturation, setSaturation] = useState(118)
  const [sharpness, setSharpness] = useState(0.35)
  const [grayscale, setGrayscale] = useState(false)
  const [editorMode, setEditorMode] = useState('crop')
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [cropRect, setCropRect] = useState({ x: 0, y: 0, width: 1, height: 1 })
  const [draftCropRect, setDraftCropRect] = useState(null)
  const [selectingCrop, setSelectingCrop] = useState(false)
  const [savingEdit, setSavingEdit] = useState(false)
  const [savedEditedFile, setSavedEditedFile] = useState(null)
  const [savedEditedPreviewUrl, setSavedEditedPreviewUrl] = useState('')
  const [savedEditSignature, setSavedEditSignature] = useState('')
  const [editorNotice, setEditorNotice] = useState('')
  const cropStartRef = useRef(null)
  const panStartRef = useRef(null)
  const imageEditorRef = useRef(null)
  const requestControllerRef = useRef(null)

  const detectedCurrency = useMemo(() => {
    return (previewResult?.currency_code || result?.currency_code || 'INR').toUpperCase()
  }, [previewResult, result])

  const sourceCurrency = (sourceCurrencyOverride || detectedCurrency).toUpperCase()
  const activeCurrency = displayCurrency || sourceCurrency
  const isConversionActive = Boolean(activeCurrency && sourceCurrency && activeCurrency !== sourceCurrency)
  const isImageFile = isLikelyImageFile(file)

  const visualFilter = useMemo(() => {
    return buildFilterString({ brightness, contrast, saturation, grayscale })
  }, [brightness, contrast, saturation, grayscale])

  const editorTransform = useMemo(() => {
    return `translate(${panOffset.x}px, ${panOffset.y}px) rotate(${rotation}deg) scale(${zoom})`
  }, [panOffset.x, panOffset.y, rotation, zoom])

  const editSignature = useMemo(() => {
    return buildEditSignature({
      file,
      zoom,
      rotation,
      brightness,
      contrast,
      saturation,
      sharpness,
      grayscale,
      cropRect,
    })
  }, [file, zoom, rotation, brightness, contrast, saturation, sharpness, grayscale, cropRect])

  const cropStyle = useMemo(() => {
    const activeCrop = draftCropRect || cropRect
    return {
      left: `${activeCrop.x * 100}%`,
      top: `${activeCrop.y * 100}%`,
      width: `${activeCrop.width * 100}%`,
      height: `${activeCrop.height * 100}%`,
    }
  }, [cropRect, draftCropRect])

  const resetEditorState = () => {
    setZoom(1)
    setRotation(0)
    setBrightness(110)
    setContrast(120)
    setSaturation(118)
    setSharpness(0.35)
    setGrayscale(false)
    setEditorMode('crop')
    setPanOffset({ x: 0, y: 0 })
    setIsPanning(false)
    setCropRect({ x: 0, y: 0, width: 1, height: 1 })
    setDraftCropRect(null)
    setSelectingCrop(false)
    cropStartRef.current = null
    panStartRef.current = null
  }

  const clearSavedEdit = () => {
    if (savedEditedPreviewUrl) {
      URL.revokeObjectURL(savedEditedPreviewUrl)
    }
    setSavedEditedPreviewUrl('')
    setSavedEditedFile(null)
    setSavedEditSignature('')
  }

  const cancelInFlightRequest = (message = 'Request cancelled.') => {
    if (requestControllerRef.current) {
      requestControllerRef.current.abort()
      requestControllerRef.current = null
    }
    setUploading(false)
    if (message) {
      setError(message)
    }
  }

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
      setResult(null)
      setPreviewResult(null)
      setSourceCurrencyOverride('')
      setDisplayCurrency('')
      setExchangeRate(1)
      setRateError(null)
      setEditorNotice('')
      clearSavedEdit()
      resetEditorState()

      if (isLikelyImageFile(selectedFile)) {
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

  useEffect(() => {
    if (!savedEditedFile) {
      return
    }

    if (savedEditSignature !== editSignature) {
      clearSavedEdit()
      setEditorNotice('Edits changed. Save edited receipt again before final upload.')
    }
  }, [editSignature, savedEditedFile, savedEditSignature])

  useEffect(() => {
    return () => {
      if (savedEditedPreviewUrl) {
        URL.revokeObjectURL(savedEditedPreviewUrl)
      }
    }
  }, [savedEditedPreviewUrl])

  useEffect(() => {
    setDisplayCurrency(sourceCurrency)
  }, [sourceCurrency])

  useEffect(() => {
    const loadRate = async () => {
      if (!displayCurrency || displayCurrency === sourceCurrency) {
        setExchangeRate(1)
        setRateError(null)
        return
      }

      setRateLoading(true)
      setRateError(null)
      try {
        const rate = await fetchLiveExchangeRate(sourceCurrency, displayCurrency)
        setExchangeRate(rate)
      } catch (err) {
        setExchangeRate(1)
        setRateError(err?.message || 'Unable to fetch live currency rate')
      } finally {
        setRateLoading(false)
      }
    }

    loadRate()
  }, [sourceCurrency, displayCurrency])

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      setError((prev) => (prev === 'Internet disconnected. Request stopped. Reconnect and try again.' ? null : prev))
    }

    const handleOffline = () => {
      setIsOnline(false)
      if (requestControllerRef.current) {
        cancelInFlightRequest('Internet disconnected. Request stopped. Reconnect and try again.')
      }
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      if (requestControllerRef.current) {
        requestControllerRef.current.abort()
        requestControllerRef.current = null
      }
    }
  }, [])

  const beginCropSelection = (event) => {
    if (!isImageFile || !imageEditorRef.current) {
      return
    }

    const pointer = getPointerPoint(event)
    const bounds = imageEditorRef.current.getBoundingClientRect()
    if (bounds.width <= 0 || bounds.height <= 0) {
      return
    }

    const x = clamp((pointer.clientX - bounds.left) / bounds.width, 0, 1)
    const y = clamp((pointer.clientY - bounds.top) / bounds.height, 0, 1)
    cropStartRef.current = { x, y }
    setSelectingCrop(true)
    setDraftCropRect({ x, y, width: MIN_CROP_SIZE, height: MIN_CROP_SIZE })
  }

  const beginPanning = (event) => {
    if (!imageEditorRef.current) {
      return
    }

    const pointer = getPointerPoint(event)
    panStartRef.current = {
      x: pointer.clientX,
      y: pointer.clientY,
      offsetX: panOffset.x,
      offsetY: panOffset.y,
    }
    setIsPanning(true)
  }

  const updatePanning = (event) => {
    if (!isPanning || !panStartRef.current) {
      return
    }

    const pointer = getPointerPoint(event)
    const start = panStartRef.current
    const dx = pointer.clientX - start.x
    const dy = pointer.clientY - start.y
    setPanOffset({
      x: clamp(start.offsetX + dx, -500, 500),
      y: clamp(start.offsetY + dy, -500, 500),
    })
  }

  const finalizePanning = () => {
    if (!isPanning) {
      return
    }

    setIsPanning(false)
    panStartRef.current = null
  }

  const beginEditorInteraction = (event) => {
    if (editorMode === 'pan') {
      beginPanning(event)
      return
    }
    beginCropSelection(event)
  }

  const updateEditorInteraction = (event) => {
    if (editorMode === 'pan') {
      updatePanning(event)
      return
    }
    updateCropSelection(event)
  }

  const finalizeEditorInteraction = () => {
    if (editorMode === 'pan') {
      finalizePanning()
      return
    }
    finalizeCropSelection()
  }

  const handleEditorWheel = useCallback((event) => {
    if (!isImageFile) {
      return
    }

    event.preventDefault()

    if (event.ctrlKey || event.metaKey || editorMode === 'crop') {
      const step = event.deltaY < 0 ? 0.1 : -0.1
      setZoom((prev) => clamp(prev + step, 1, 4))
      return
    }

    setPanOffset((prev) => ({
      x: clamp(prev.x - event.deltaX * 0.5, -500, 500),
      y: clamp(prev.y - event.deltaY * 0.5, -500, 500),
    }))
  }, [editorMode, isImageFile])

  useEffect(() => {
    const node = imageEditorRef.current
    if (!node) {
      return undefined
    }

    const onWheel = (event) => handleEditorWheel(event)
    node.addEventListener('wheel', onWheel, { passive: false })

    return () => {
      node.removeEventListener('wheel', onWheel)
    }
  }, [handleEditorWheel])

  const updateCropSelection = (event) => {
    if (!selectingCrop || !cropStartRef.current || !imageEditorRef.current) {
      return
    }

    const pointer = getPointerPoint(event)
    const bounds = imageEditorRef.current.getBoundingClientRect()
    const currentX = clamp((pointer.clientX - bounds.left) / bounds.width, 0, 1)
    const currentY = clamp((pointer.clientY - bounds.top) / bounds.height, 0, 1)
    const start = cropStartRef.current

    const left = Math.min(start.x, currentX)
    const top = Math.min(start.y, currentY)
    const width = Math.max(Math.abs(currentX - start.x), MIN_CROP_SIZE)
    const height = Math.max(Math.abs(currentY - start.y), MIN_CROP_SIZE)

    setDraftCropRect({
      x: clamp(left, 0, 1 - MIN_CROP_SIZE),
      y: clamp(top, 0, 1 - MIN_CROP_SIZE),
      width: clamp(width, MIN_CROP_SIZE, 1 - left),
      height: clamp(height, MIN_CROP_SIZE, 1 - top),
    })
  }

  const finalizeCropSelection = () => {
    if (!selectingCrop) {
      return
    }

    setSelectingCrop(false)
    cropStartRef.current = null

    if (draftCropRect) {
      setCropRect(draftCropRect)
      setDraftCropRect(null)
    }
  }

  const resetCrop = () => {
    setCropRect({ x: 0, y: 0, width: 1, height: 1 })
    setDraftCropRect(null)
  }

  const autoEnhance = () => {
    setBrightness(118)
    setContrast(132)
    setSaturation(122)
    setSharpness(0.5)
    setGrayscale(false)
  }

  const handleSaveEditedReceipt = async () => {
    if (!file) {
      setError('Please select a file first.')
      return
    }

    setSavingEdit(true)
    setError(null)
    setEditorNotice('')

    try {
      const editedFile = await buildUploadFile()

      if (savedEditedPreviewUrl) {
        URL.revokeObjectURL(savedEditedPreviewUrl)
      }

      const previewUrl = isImageFile ? URL.createObjectURL(editedFile) : ''
      setSavedEditedFile(editedFile)
      setSavedEditedPreviewUrl(previewUrl)
      setSavedEditSignature(editSignature)
      setEditorNotice('Edited receipt saved. Final upload will use this saved version.')
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to save edited receipt')
    } finally {
      setSavingEdit(false)
    }
  }

  const buildUploadFile = async () => {
    if (!file || !isImageFile || !preview) {
      return file
    }

    const image = await loadImageFromDataUrl(preview)
    const srcX = Math.round(cropRect.x * image.width)
    const srcY = Math.round(cropRect.y * image.height)
    const srcWidth = Math.max(1, Math.round(cropRect.width * image.width))
    const srcHeight = Math.max(1, Math.round(cropRect.height * image.height))

    const outputWidth = Math.max(280, srcWidth)
    const outputHeight = Math.max(280, srcHeight)
    const canvas = document.createElement('canvas')
    canvas.width = outputWidth
    canvas.height = outputHeight
    const context = canvas.getContext('2d', { willReadFrequently: true })

    if (!context) {
      throw new Error('Unable to prepare edited image')
    }

    context.save()
    context.translate(outputWidth / 2, outputHeight / 2)
    context.rotate((rotation * Math.PI) / 180)
    context.scale(zoom, zoom)
    context.filter = visualFilter
    context.drawImage(
      image,
      srcX,
      srcY,
      srcWidth,
      srcHeight,
      -outputWidth / 2,
      -outputHeight / 2,
      outputWidth,
      outputHeight,
    )
    context.restore()

    applySharpenToContext(context, outputWidth, outputHeight, sharpness)

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob((generatedBlob) => {
        if (!generatedBlob) {
          reject(new Error('Unable to export edited image'))
          return
        }
        resolve(generatedBlob)
      }, 'image/jpeg', 0.95)
    })

    const originalName = file.name.replace(/\.[^.]+$/, '')
    return new File([blob], `${originalName}-edited.jpg`, { type: 'image/jpeg' })
  }

  const convertAmount = (amount) => {
    const numeric = Number(amount || 0)
    if (!Number.isFinite(numeric)) {
      return 0
    }
    if (!displayCurrency || displayCurrency === sourceCurrency) {
      return numeric
    }
    return numeric * exchangeRate
  }

  const handlePreview = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    if (!isOnline) {
      setError('You are offline. Reconnect to the internet and retry.')
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)
    setPreviewResult(null)

    try {
      const controller = new AbortController()
      requestControllerRef.current = controller
      const editedFile = await buildUploadFile()
      const response = await receiptAPI.previewReceipt(editedFile, receiptType || null, {
        signal: controller.signal,
      })
      setPreviewResult(response)
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to preview receipt')
    } finally {
      requestControllerRef.current = null
      setUploading(false)
    }
  }

  const handleProcess = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    if (!isOnline) {
      setError('You are offline. Reconnect to the internet and retry.')
      return
    }

    if (isConversionActive && rateLoading) {
      setError('Please wait for live exchange rate to finish loading.')
      return
    }

    if (isConversionActive && rateError) {
      setError('Cannot process with currency conversion while exchange rate failed. Please retry conversion or use source currency.')
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const controller = new AbortController()
      requestControllerRef.current = controller
      if (isImageFile && (!savedEditedFile || savedEditSignature !== editSignature)) {
        setError('Please click Save Edited Receipt before final upload.')
        setUploading(false)
        requestControllerRef.current = null
        return
      }

      const editedFile = isImageFile ? savedEditedFile : await buildUploadFile()
      const response = await receiptAPI.uploadReceipt(editedFile, receiptType || null, {
        sourceCurrency,
        targetCurrency: activeCurrency,
        exchangeRate: isConversionActive ? exchangeRate : 1,
      }, {
        signal: controller.signal,
      })
      setResult(response)

      if (response.success && onUploadSuccess) {
        onUploadSuccess(response)
      }

      if (response.success) {
        setTimeout(() => {
          setFile(null)
          setPreview(null)
          clearSavedEdit()
          setEditorNotice('')
          resetEditorState()
          setReceiptType('')
          setPreviewResult(null)
          document.getElementById('file-input').value = ''
        }, 3000)
      }
    } catch (err) {
      setError(getErrorMessage(err) || 'Failed to process receipt')
    } finally {
      requestControllerRef.current = null
      setUploading(false)
    }
  }

  return (
    <div className="receipt-upload">
      <h2>Upload Receipt</h2>

      <form className="upload-form" onSubmit={(e) => e.preventDefault()}>
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
            <div className="preview-header">
              <h3>Image Editor</h3>
              {isImageFile && <span className="editor-hint">Crop mode: drag to select area, wheel to zoom. Pan mode: drag/scroll to move image.</span>}
            </div>

            {isImageFile ? (
              <>
                <div className="editor-toolbar">
                  <button type="button" className={`editor-btn ${editorMode === 'crop' ? 'active' : ''}`} onClick={() => setEditorMode('crop')} disabled={uploading}>Crop Mode</button>
                  <button type="button" className={`editor-btn ${editorMode === 'pan' ? 'active' : ''}`} onClick={() => setEditorMode('pan')} disabled={uploading}>Pan Mode</button>
                  <button type="button" className="editor-btn" onClick={() => setZoom((prev) => clamp(prev - 0.1, 1, 3))} disabled={uploading}>Zoom Out</button>
                  <button type="button" className="editor-btn" onClick={() => setZoom((prev) => clamp(prev + 0.1, 1, 3))} disabled={uploading}>Zoom In</button>
                  <button type="button" className="editor-btn" onClick={() => setRotation((prev) => prev - 5)} disabled={uploading}>Tilt Left</button>
                  <button type="button" className="editor-btn" onClick={() => setRotation((prev) => prev + 5)} disabled={uploading}>Tilt Right</button>
                  <button type="button" className="editor-btn" onClick={() => setRotation((prev) => prev - 90)} disabled={uploading}>Rotate Left</button>
                  <button type="button" className="editor-btn" onClick={() => setRotation((prev) => prev + 90)} disabled={uploading}>Rotate Right</button>
                  <button type="button" className="editor-btn" onClick={resetCrop} disabled={uploading}>Reset Crop</button>
                  <button type="button" className="editor-btn" onClick={autoEnhance} disabled={uploading}>Auto Enhance</button>
                  <button type="button" className="editor-btn primary" onClick={handleSaveEditedReceipt} disabled={uploading || savingEdit}>{savingEdit ? 'Saving...' : 'Save Edited Receipt'}</button>
                  <button type="button" className="editor-btn" onClick={resetEditorState} disabled={uploading}>Reset All</button>
                </div>

                {editorNotice && <div className="editor-notice">{editorNotice}</div>}

                {savedEditedFile && savedEditSignature === editSignature && (
                  <div className="editor-saved-info">
                    <span>Saved: {savedEditedFile.name} ({(savedEditedFile.size / 1024).toFixed(1)} KB)</span>
                    {savedEditedPreviewUrl && (
                      <a href={savedEditedPreviewUrl} download={savedEditedFile.name} className="editor-download-link">Download edited receipt</a>
                    )}
                  </div>
                )}

                <div
                  ref={imageEditorRef}
                  className="image-editor-canvas"
                  onMouseDown={beginEditorInteraction}
                  onMouseMove={updateEditorInteraction}
                  onMouseUp={finalizeEditorInteraction}
                  onMouseLeave={finalizeEditorInteraction}
                  onTouchStart={beginEditorInteraction}
                  onTouchMove={updateEditorInteraction}
                  onTouchEnd={finalizeEditorInteraction}
                >
                  <img
                    src={preview}
                    alt="Receipt preview"
                    className="preview-image editable"
                    style={{ transform: editorTransform, filter: visualFilter }}
                  />
                  <div className="crop-overlay">
                    <div className="crop-rect" style={cropStyle} />
                  </div>
                </div>

                <div className="editor-sliders">
                  <label>
                    Zoom: {zoom.toFixed(2)}x
                    <input type="range" min="1" max="4" step="0.05" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} disabled={uploading} />
                  </label>
                  <label>
                    Rotation: {rotation}deg
                    <input type="range" min="-180" max="180" step="1" value={rotation} onChange={(e) => setRotation(Number(e.target.value))} disabled={uploading} />
                  </label>
                  <label>
                    Brightness: {brightness}%
                    <input type="range" min="70" max="170" step="1" value={brightness} onChange={(e) => setBrightness(Number(e.target.value))} disabled={uploading} />
                  </label>
                  <label>
                    Contrast: {contrast}%
                    <input type="range" min="70" max="180" step="1" value={contrast} onChange={(e) => setContrast(Number(e.target.value))} disabled={uploading} />
                  </label>
                  <label>
                    Saturation: {saturation}%
                    <input type="range" min="50" max="180" step="1" value={saturation} onChange={(e) => setSaturation(Number(e.target.value))} disabled={uploading} />
                  </label>
                  <label>
                    Sharpness: {sharpness.toFixed(2)}
                    <input type="range" min="0" max="1" step="0.05" value={sharpness} onChange={(e) => setSharpness(Number(e.target.value))} disabled={uploading} />
                  </label>
                </div>

                <label className="checkbox-enhance">
                  <input type="checkbox" checked={grayscale} onChange={(e) => setGrayscale(e.target.checked)} disabled={uploading} />
                  Force grayscale OCR mode
                </label>
              </>
            ) : (
              <img src={preview} alt="Receipt preview" className="preview-image" />
            )}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="receipt-type">Receipt Type (Optional)</label>
          <select
            id="receipt-type"
            value={receiptType}
            onChange={(e) => {
              setReceiptType(e.target.value)
              setPreviewResult(null)
              setResult(null)
            }}
            disabled={uploading}
          >
            <option value="">Auto-detect</option>
            <option value="purchase">Purchase (Add Stock)</option>
            <option value="sale">Sale (Deduct Stock)</option>
          </select>
        </div>

        <div className="receipt-actions">
          <button type="button" onClick={handlePreview} disabled={uploading || !file || !isOnline} className="upload-button secondary">
            {uploading ? 'Extracting...' : 'Preview Extracted Items'}
          </button>
          <button
            type="button"
            onClick={handleProcess}
            disabled={uploading || !file || !previewResult?.success || !isOnline || (isConversionActive && (rateLoading || Boolean(rateError)))}
            className="upload-button"
          >
            {uploading ? 'Processing...' : 'Confirm & Process Receipt'}
          </button>
          {uploading && (
            <button type="button" onClick={() => cancelInFlightRequest('Request cancelled.')} className="upload-button secondary">
              Cancel
            </button>
          )}
        </div>
      </form>

      {!isOnline && (
        <div className="network-banner">
          You are offline. Processing is paused until internet reconnects.
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {(previewResult || result) && (
        <div className="currency-panel">
          <div className="currency-panel-row">
            <span className="currency-label">Detected Currency: <strong>{detectedCurrency}</strong></span>
            <label htmlFor="source-currency" className="currency-select-label">Source Currency</label>
            <select
              id="source-currency"
              className="currency-select"
              value={sourceCurrency}
              onChange={(e) => setSourceCurrencyOverride(e.target.value)}
            >
              {SUPPORTED_CURRENCIES.map((code) => (
                <option key={`src-${code}`} value={code}>{code}</option>
              ))}
            </select>
            <label htmlFor="display-currency" className="currency-select-label">Display Currency</label>
            <select
              id="display-currency"
              className="currency-select"
              value={displayCurrency}
              onChange={(e) => setDisplayCurrency(e.target.value)}
            >
              {SUPPORTED_CURRENCIES.map((code) => (
                <option key={`dst-${code}`} value={code}>{code}</option>
              ))}
            </select>
          </div>
          {displayCurrency && displayCurrency !== sourceCurrency && (
            <div className="currency-rate">
              {rateLoading
                ? `Fetching live rate for ${sourceCurrency} to ${displayCurrency}...`
                : `1 ${sourceCurrency} = ${exchangeRate.toFixed(4)} ${displayCurrency}`}
            </div>
          )}
          {rateError && <div className="currency-error">{rateError}</div>}
        </div>
      )}

      {previewResult && (
        <div className="result-message preview">
          <h3>Preview: Check Extracted Items</h3>
          <p>{previewResult.message}</p>

          {(!previewResult.items || previewResult.items.length === 0) && (
            <div className="warning-message">
              <strong>No items extracted yet.</strong> Try a tighter crop around the table area, then preview again.
            </div>
          )}

          {previewResult.items && previewResult.items.length > 0 && (
            <div className="items-table">
              <h4>Extracted Items ({previewResult.items_processed})</h4>
              <table>
                <thead>
                  <tr>
                    <th>Product Name</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {previewResult.items.map((item, index) => (
                    <tr key={index}>
                      <td>{item.product_name}</td>
                      <td>{item.quantity}</td>
                      <td>{formatCurrencyAmount(convertAmount(item.unit_price || 0), activeCurrency)}</td>
                      <td>{formatCurrencyAmount(convertAmount(item.total_price || (item.quantity * item.unit_price) || 0), activeCurrency)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {(previewResult.ocr_text_preview || (previewResult.ocr_lines_preview && previewResult.ocr_lines_preview.length > 0)) && (
            <details className="ocr-debug">
              <summary>Show OCR Debug Text</summary>
              {previewResult.ocr_lines_preview && previewResult.ocr_lines_preview.length > 0 ? (
                <pre>{previewResult.ocr_lines_preview.join('\n')}</pre>
              ) : (
                <pre>{previewResult.ocr_text_preview}</pre>
              )}
            </details>
          )}

          <div className="preview-hint">If everything looks correct, click Confirm & Process Receipt.</div>
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
                      <td>{formatCurrencyAmount(convertAmount(item.unit_price || 0), activeCurrency)}</td>
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

