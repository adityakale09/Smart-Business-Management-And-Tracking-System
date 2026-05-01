export const SUPPORTED_CURRENCIES = ['USD', 'INR', 'EUR', 'GBP', 'AED', 'CAD', 'AUD', 'JPY']

export const formatCurrencyAmount = (amount, currencyCode) => {
  const safeAmount = Number.isFinite(Number(amount)) ? Number(amount) : 0
  const code = (currencyCode || 'INR').toUpperCase()

  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: code,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(safeAmount)
  } catch {
    return `${code} ${safeAmount.toFixed(2)}`
  }
}

export const fetchLiveExchangeRate = async (baseCurrency, targetCurrency) => {
  const from = (baseCurrency || '').toUpperCase()
  const to = (targetCurrency || '').toUpperCase()

  if (!from || !to) {
    throw new Error('Currency codes are required')
  }
  if (from === to) {
    return 1
  }

  const response = await fetch(`https://api.frankfurter.app/latest?from=${from}&to=${to}`)
  if (!response.ok) {
    throw new Error('Unable to fetch live exchange rate')
  }

  const data = await response.json()
  const rate = data?.rates?.[to]

  if (!rate || typeof rate !== 'number') {
    throw new Error('Live rate unavailable for selected currencies')
  }

  return rate
}
