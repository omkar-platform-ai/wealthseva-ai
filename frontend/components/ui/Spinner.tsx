import { cn } from '@/lib/utils';

/** Single loading affordance for the whole app (collapses 4 former patterns).
 *  Inherits its color from the parent's text color (currentColor). */
export function Spinner({
  size = 'md',
  label = 'Loading',
  className,
}: {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}) {
  const sizeCls = { sm: 'w-4 h-4', md: 'w-5 h-5', lg: 'w-7 h-7' }[size];
  return (
    <span
      className={cn(
        'inline-block animate-spin rounded-full border-2 border-current border-t-transparent align-[-0.125em]',
        sizeCls,
        className,
      )}
      role="status"
      aria-label={label}
    />
  );
}
