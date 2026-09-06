/**
 * Format utility functions for displaying numbers and text.
 */

/**
 * Formats a numeric value as a currency string.
 * @param amount Number representing price value
 * @param currency Currency code (defaults to USD)
 * @returns Formatted currency string
 */
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Capitalizes the first letter of an input string.
 * @param str Input string
 * @returns Capitalized string
 */
export function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Truncates text with an ellipsis if length exceeds maxLength.
 * @param text Original text
 * @param maxLength Max character limit
 * @returns Truncated or original text
 */
export const truncate = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength)}...`;
};
