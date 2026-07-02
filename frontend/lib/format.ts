const LAKH = 100_000;
const CRORE = 10_000_000;

const LAKH_LABELS: Record<string, string> = {
  hi: 'लाख',
  mr: 'लाख',
  ta: 'லட்சம்',
  bn: 'লাখ',
  en: 'lakh',
};

const CRORE_LABELS: Record<string, string> = {
  hi: 'करोड़',
  mr: 'करोड़',
  ta: 'கோடி',
  bn: 'কোটি',
  en: 'crore',
};

export function formatINR(value: number, locale: string = 'en'): string {
  const lakh = LAKH_LABELS[locale] ?? 'lakh';
  const crore = CRORE_LABELS[locale] ?? 'crore';

  if (value >= CRORE) {
    const v = value / CRORE;
    return `₹${v % 1 === 0 ? v : v.toFixed(1)} ${crore}`;
  }
  if (value >= LAKH) {
    const v = value / LAKH;
    return `₹${v % 1 === 0 ? v : v.toFixed(1)} ${lakh}`;
  }
  return `₹${value.toLocaleString('en-IN')}`;
}
