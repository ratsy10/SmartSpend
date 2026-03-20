export function formatCurrency(amount: number, currencyCode: string = 'USD'): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currencyCode,
      minimumFractionDigits: 0,
    }).format(amount);
  } catch (error) {
    // Fallback if currency code is invalid or not supported by the browser
    const symbol = currencyCode === 'INR' ? '₹' : currencyCode === 'EUR' ? '€' : currencyCode === 'GBP' ? '£' : '$';
    return `${symbol}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
}

export function getCurrencySymbol(currencyCode: string = 'USD'): string {
  try {
    const parts = new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currencyCode,
    }).formatToParts(0);
    return parts.find((p) => p.type === 'currency')?.value || '$';
  } catch {
    return currencyCode === 'INR' ? '₹' : currencyCode === 'EUR' ? '€' : currencyCode === 'GBP' ? '£' : '$';
  }
}
