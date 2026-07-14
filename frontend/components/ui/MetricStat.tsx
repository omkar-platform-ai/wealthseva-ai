import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';

type DeltaTone = 'up' | 'down' | 'neutral';

export function MetricStat({
  label,
  value,
  delta,
  deltaTone = 'neutral',
  sub,
  children,
  onDark = false,
  className,
}: {
  label: string;
  value: React.ReactNode;
  delta?: string;
  deltaTone?: DeltaTone;
  sub?: string;
  /** sparkline / extra slot under the figure */
  children?: React.ReactNode;
  onDark?: boolean;
  className?: string;
}) {
  const deltaCls: Record<DeltaTone, string> = {
    up: onDark ? 'text-idbi-mintBright' : 'text-idbi-green',
    down: 'text-red-500',
    neutral: onDark ? 'text-idbi-mint' : 'text-idbi-muted',
  };
  const DeltaIcon = deltaTone === 'up' ? ArrowUpRight : deltaTone === 'down' ? ArrowDownRight : null;

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      <span className={cn('text-xs font-medium', onDark ? 'text-idbi-mint' : 'text-idbi-muted')}>{label}</span>
      <span className={cn('text-3xl font-extrabold tracking-tight tabular-nums', onDark ? 'text-white' : 'text-idbi-ink')}>
        {value}
      </span>
      {(delta || sub) && (
        <div className="flex items-center gap-1.5">
          {delta && (
            <span className={cn('inline-flex items-center gap-0.5 text-xs font-semibold', deltaCls[deltaTone])}>
              {DeltaIcon && <DeltaIcon size={13} />}
              {delta}
            </span>
          )}
          {sub && <span className={cn('text-xs', onDark ? 'text-idbi-mintDim' : 'text-idbi-faint')}>{sub}</span>}
        </div>
      )}
      {children}
    </div>
  );
}
