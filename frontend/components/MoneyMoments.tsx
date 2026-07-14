'use client';
import { useState, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { AlertTriangle } from 'lucide-react';
import { cn, FOCUS_RING } from '@/lib/utils';
import { useToast } from '@/components/ui/Toast';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/Button';

interface WhyTrace {
  data_points: string[];
  rule: string;
  calculation: string;
}

interface Nudge {
  id: string;
  type: 'idle_cash' | 'sip_shortfall';
  title: string;
  body: string;
  severity: 'low' | 'medium' | 'high';
  why_trace: WhyTrace;
  chat_seed: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

const SEVERITY_CLASSES: Record<string, string> = {
  high: 'border-idbi-orange bg-idbi-warm',
  medium: 'border-idbi-gold bg-idbi-warmSoft',
  low: 'border-idbi-green bg-idbi-light',
};

const SEVERITY_BADGE: Record<string, string> = {
  high: 'bg-idbi-orange text-white',
  medium: 'bg-idbi-gold text-idbi-inkGreen',
  low: 'bg-idbi-green text-white',
};

const TYPE_ICON: Record<string, string> = {
  idle_cash: '💤',
  sip_shortfall: '📈',
};

interface Props {
  onNudgeSelect: (seed: string) => void;
}

export default function MoneyMoments({ onNudgeSelect }: Props) {
  const t = useTranslations('moments');
  const locale = useLocale();
  const { toast } = useToast();
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [reload, setReload] = useState(0);

  // Re-fetch whenever the locale changes so nudge prose follows the language
  // selection. Figures are deterministic and identical across locales.
  useEffect(() => {
    setLoaded(false);
    setError(false);
    fetch(`${BACKEND_URL}/api/nudges?language=${locale}`)
      .then(r => r.json())
      .then(d => setNudges(d.nudges ?? []))
      .catch(() => {
        setError(true);
        toast({
          tone: 'error',
          message: t('load_error'),
          action: { label: t('retry'), onClick: () => setReload(x => x + 1) },
        });
      })
      .finally(() => setLoaded(true));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale, reload]);

  // Still loading, or genuinely nothing to nudge about → stay quiet (this is a
  // secondary, proactive widget). A load *failure*, however, is surfaced below.
  if (!loaded) return null;
  if (error) {
    return (
      <section className="mt-6">
        <EmptyState
          icon={<AlertTriangle size={20} />}
          title={t('load_error')}
          action={
            <Button size="sm" variant="secondary" onClick={() => setReload(x => x + 1)}>
              {t('retry')}
            </Button>
          }
        />
      </section>
    );
  }
  if (nudges.length === 0) return null;

  return (
    <section className="mt-6">
      <h2 className="text-base font-bold text-idbi-slate mb-3 flex items-center gap-2">
        <span aria-hidden>⚡</span> {t('title')}
      </h2>
      <div className="space-y-3">
        {nudges.map(nudge => (
          <div
            key={nudge.id}
            className={cn('rounded-card border-l-4 p-4', SEVERITY_CLASSES[nudge.severity] ?? SEVERITY_CLASSES.low)}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl leading-none shrink-0" aria-hidden>
                {TYPE_ICON[nudge.type]}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-semibold text-sm text-idbi-slate">{nudge.title}</p>
                  <span className={cn('text-xs font-bold px-2 py-0.5 rounded-full', SEVERITY_BADGE[nudge.severity])}>
                    {t(`severity_${nudge.severity}` as const)}
                  </span>
                </div>
                <p className="text-xs text-idbi-faint mt-1.5 leading-relaxed">{nudge.body}</p>

                <button
                  onClick={() => setExpanded(expanded === nudge.id ? null : nudge.id)}
                  className={cn('text-xs font-medium mt-2 text-idbi-green hover:underline', FOCUS_RING)}
                >
                  {expanded === nudge.id ? `${t('why_hide')} ↑` : `${t('why_show')} ↓`}
                </button>

                {expanded === nudge.id && (
                  <div className="mt-2 bg-white/80 rounded-tile p-3 space-y-1.5">
                    {nudge.why_trace.data_points.map((pt, i) => (
                      <p key={i} className="text-xs text-idbi-faint flex gap-1.5">
                        <span className="text-idbi-green shrink-0">·</span>
                        <span>{pt}</span>
                      </p>
                    ))}
                    <p className="text-xs text-idbi-slate font-medium flex gap-1.5 mt-1 pt-1 border-t border-idbi-line">
                      <span className="text-idbi-green shrink-0">∴</span>
                      <span>{nudge.why_trace.calculation}</span>
                    </p>
                  </div>
                )}

                <button
                  onClick={() => onNudgeSelect(nudge.chat_seed)}
                  className={cn('mt-3 text-sm font-bold text-white bg-idbi-green px-4 py-1.5 rounded-full hover:bg-idbi-dark transition-colors shadow-glow', FOCUS_RING)}
                >
                  {t('talk_to_shreya')} →
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
