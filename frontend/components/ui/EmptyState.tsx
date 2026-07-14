import { cn } from '@/lib/utils';

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col items-center text-center py-10 px-6', className)}>
      {icon && (
        <div className="w-12 h-12 rounded-tile bg-idbi-light text-idbi-green flex items-center justify-center mb-3">
          {icon}
        </div>
      )}
      <p className="text-base font-semibold text-idbi-ink">{title}</p>
      {description && <p className="text-sm text-idbi-muted max-w-sm mt-1">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
