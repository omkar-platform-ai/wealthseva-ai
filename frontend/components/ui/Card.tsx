import { cn } from '@/lib/utils';

export type CardVariant = 'default' | 'elevated' | 'gradient' | 'flat';

const VARIANTS: Record<CardVariant, string> = {
  default: 'bg-white border border-idbi-line shadow-card',
  elevated: 'bg-white border border-idbi-line shadow-pop',
  gradient: 'bg-gradient-to-br from-idbi-green to-idbi-deep text-white',
  flat: 'bg-white border border-idbi-line',
};

/** Surface primitive — bg/border/radius/elevation only. Add padding in the
 *  consumer so layout stays flexible. */
export function Card({
  variant = 'default',
  className,
  children,
  ...props
}: { variant?: CardVariant; className?: string; children: React.ReactNode } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('rounded-card', VARIANTS[variant], className)} {...props}>
      {children}
    </div>
  );
}
