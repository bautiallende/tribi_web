/**
 * Format price according to locale
 * @param price - Price in USD
 * @param locale - Locale code (en, es, etc.)
 * @returns Formatted price string
 */
export function formatPrice(price: number, locale: string = 'en'): string {
  return new Intl.NumberFormat(locale === 'es' ? 'es-US' : 'en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price);
}

/**
 * Format data amount
 * @param dataGB - Data amount in GB
 * @param locale - Locale code
 * @returns Formatted data string
 */
export function formatData(dataGB: number, locale: string = 'en'): string {
  if (dataGB >= 1000) {
    return `${dataGB / 1000} TB`;
  }
  return `${dataGB} GB`;
}

/**
 * Format duration
 * @param days - Duration in days
 * @param locale - Locale code
 * @returns Formatted duration string
 */
export function formatDuration(days: number, locale: string = 'en'): string {
  const word = locale === 'es' ? 'días' : 'days';
  return `${days} ${word}`;
}
