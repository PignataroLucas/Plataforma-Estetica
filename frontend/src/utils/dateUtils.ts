/**
 * Date utilities for Argentina timezone and formatting
 * Handles timezone conversions and date formatting for the application
 */

/**
 * Formats a date string or Date object to DD/MM/YYYY format (Argentina)
 * @param date - Date object or ISO string
 * @returns Formatted date string in DD/MM/YYYY format
 */
export const formatDateArgentina = (date: Date | string | null | undefined): string => {
  if (!date) return ''

  const dateObj = typeof date === 'string' ? new Date(date) : date

  const day = dateObj.getDate().toString().padStart(2, '0')
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const year = dateObj.getFullYear()

  return `${day}/${month}/${year}`
}

/**
 * Formats a date to YYYY-MM-DD format for input[type="date"] values
 * Adjusts for timezone to ensure the correct date is shown
 * @param date - Date object or ISO string
 * @returns Date string in YYYY-MM-DD format
 */
export const formatDateForInput = (date: Date | string | null | undefined): string => {
  if (!date) return ''

  const dateObj = typeof date === 'string' ? new Date(date) : date

  // Get the date components in local timezone
  const year = dateObj.getFullYear()
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const day = dateObj.getDate().toString().padStart(2, '0')

  return `${year}-${month}-${day}`
}

/**
 * Converts a date from input[type="date"] to ISO string for API
 * Ensures the date is sent with correct timezone information
 * @param dateString - Date string in YYYY-MM-DD format
 * @returns ISO string with Argentina timezone
 */
export const dateInputToISO = (dateString: string): string => {
  if (!dateString) return ''

  // Create date at noon in local timezone to avoid timezone shifting
  const [year, month, day] = dateString.split('-').map(Number)
  const date = new Date(year, month - 1, day, 12, 0, 0)

  return date.toISOString()
}

/**
 * Gets today's date in YYYY-MM-DD format for input[type="date"] default value
 * @returns Today's date in YYYY-MM-DD format
 */
export const getTodayForInput = (): string => {
  const today = new Date()
  const year = today.getFullYear()
  const month = (today.getMonth() + 1).toString().padStart(2, '0')
  const day = today.getDate().toString().padStart(2, '0')

  return `${year}-${month}-${day}`
}

/**
 * Formats a datetime string to DD/MM/YYYY HH:mm format
 * @param datetime - Date object or ISO string
 * @returns Formatted datetime string
 */
export const formatDateTimeArgentina = (datetime: Date | string | null | undefined): string => {
  if (!datetime) return ''

  const dateObj = typeof datetime === 'string' ? new Date(datetime) : datetime

  const day = dateObj.getDate().toString().padStart(2, '0')
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const year = dateObj.getFullYear()
  const hours = dateObj.getHours().toString().padStart(2, '0')
  const minutes = dateObj.getMinutes().toString().padStart(2, '0')

  return `${day}/${month}/${year} ${hours}:${minutes}`
}

/**
 * Formats a datetime string for input[type="datetime-local"]
 * @param datetime - Date object or ISO string
 * @returns Formatted datetime string in YYYY-MM-DDTHH:mm format
 */
export const formatDateTimeForInput = (datetime: Date | string | null | undefined): string => {
  if (!datetime) return ''

  const dateObj = typeof datetime === 'string' ? new Date(datetime) : datetime

  const year = dateObj.getFullYear()
  const month = (dateObj.getMonth() + 1).toString().padStart(2, '0')
  const day = dateObj.getDate().toString().padStart(2, '0')
  const hours = dateObj.getHours().toString().padStart(2, '0')
  const minutes = dateObj.getMinutes().toString().padStart(2, '0')

  return `${year}-${month}-${day}T${hours}:${minutes}`
}

/**
 * Parses a DD/MM/YYYY string to Date object
 * @param dateString - Date string in DD/MM/YYYY format
 * @returns Date object
 */
export const parseDateArgentina = (dateString: string): Date | null => {
  if (!dateString) return null

  const [day, month, year] = dateString.split('/').map(Number)

  if (!day || !month || !year) return null

  return new Date(year, month - 1, day)
}

/**
 * Gets current date and time in Argentina timezone as ISO string
 * @returns ISO string for current datetime
 */
export const getNowISO = (): string => {
  return new Date().toISOString()
}

/**
 * Checks if a date string is today
 * @param date - Date object or ISO string
 * @returns True if the date is today
 */
export const isToday = (date: Date | string): boolean => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const today = new Date()

  return (
    dateObj.getDate() === today.getDate() &&
    dateObj.getMonth() === today.getMonth() &&
    dateObj.getFullYear() === today.getFullYear()
  )
}

/**
 * Gets relative date text (e.g., "Hoy", "Ayer", "Mañana")
 * @param date - Date object or ISO string
 * @returns Relative date text or formatted date
 */
export const getRelativeDateText = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  if (isToday(dateObj)) return 'Hoy'

  if (
    dateObj.getDate() === yesterday.getDate() &&
    dateObj.getMonth() === yesterday.getMonth() &&
    dateObj.getFullYear() === yesterday.getFullYear()
  ) {
    return 'Ayer'
  }

  if (
    dateObj.getDate() === tomorrow.getDate() &&
    dateObj.getMonth() === tomorrow.getMonth() &&
    dateObj.getFullYear() === tomorrow.getFullYear()
  ) {
    return 'Mañana'
  }

  return formatDateArgentina(dateObj)
}
