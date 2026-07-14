import { cn } from '@/lib/utils';

/** Loading placeholder. Defaults to a subtle tint + pulse; pass rounded/size via className. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-tile bg-idbi-light', className)} />;
}
