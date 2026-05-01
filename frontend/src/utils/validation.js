export const isBlank = (value) => {
  return value === undefined || value === null || String(value).trim() === ''
}

export const parsePositiveInt = (value) => {
  const parsed = Number.parseInt(value, 10)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
}

export const parseNonNegativeInt = (value, fallback = 0) => {
  if (isBlank(value)) {
    return fallback
  }

  const parsed = Number.parseInt(value, 10)
  if (!Number.isInteger(parsed) || parsed < 0) {
    return null
  }
  return parsed
}

export const parseNonNegativeFloat = (value) => {
  const parsed = Number.parseFloat(value)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : null
}
