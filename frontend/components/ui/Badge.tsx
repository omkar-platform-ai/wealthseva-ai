import { cn } from '@/lib/utils';

export type BadgeTone =
  | 'green'
  | 'orange'
  | 'mint'
  | 'neutral'
  | 'onDark'
  | 'riskConservative'
  | 'riskModerate'
  | 'riskAggressive';

const TONES: Record<BadgeTone, string> = {
  green: 'bg-idbi-light text-idbi-green',
  orange: 'bg-idbi-warm text-idbi-orange',
  mint: 'bg-idbi-mintBright/30 text-idbi-inkGreen',
  neutral: 'bg-idbi-tint text-idbi-slate',
  onDark: 'bg-white/10 text-white',
  riskConservative: 'bg-idbi-risk-conservative-bg text-idbi-risk-conservative-text',
  riskModerate: 'bg-idbi-risk-moderate-bg text-idbi-risk-moderate-text',
  riskAggressive: 'bg-idbi-risk-aggressive-bg text-idbi-risk-aggressive-text',
};

export function Badge({
  tone = 'green',
  className,
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold', TONES[tone], className)}>
      {children}
    </span>
  );
}
