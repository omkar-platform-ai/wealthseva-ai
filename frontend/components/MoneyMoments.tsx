'use client';
import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';

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
  high: 'border-idbi-orange bg-orange-50',
  medium: 'border-amber-400 bg-amber-50',
  low: 'border-idbi-green bg-idbi-light',
};

const SEVERITY_BADGE: Record<string, string> = {
  high: 'bg-idbi-orange text-white',
  medium: 'bg-amber-400 text-white',
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
  const [nudges, setNudges] = useState<Nudge[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/nudges`)
      .then(r => r.json())
      .then(d => setNudges(d.nudges ?? []))
      .catch(() => {})
      .finally(() => setLoaded(true));
  }, []);

  if (!loaded || nudges.length === 0) return null;

  return (
    <section className="mt-6">
      <h2 className="text-base font-bold text-idbi-slate mb-3 flex items-center gap-2">
        <span aria-hidden>⚡</span> {t('title')}
      </h2>
      <div className="space-y-3">
        {nudges.map(nudge => (
          <div
            key={nudge.id}
            className={`rounded-[16px] border-l-4 p-4 ${SEVERITY_CLASSES[nudge.severity] ?? SEVERITY_CLASSES.low}`}
          >
            <div className="flex items-start gap-3">
              <span className="text-xl leading-none shrink-0" aria-hidden>
                {TYPE_ICON[nudge.type]}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-semibold text-sm text-idbi-slate">{nudge.title}</p>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SEVERITY_BADGE[nudge.severity]}`}>
                    {t(`severity_${nudge.severity}` as const)}
                  </span>
                </div>
                <p className="text-xs text-idbi-faint mt-1.5 leading-relaxed">{nudge.body}</p>

                <button
                  onClick={() => setExpanded(expanded === nudge.id ? null : nudge.id)}
                  className="text-[11px] font-medium mt-2 text-idbi-green hover:underline"
                >
                  {expanded === nudge.id ? `${t('why_hide')} ↑` : `${t('why_show')} ↓`}
                </button>

                {expanded === nudge.id && (
                  <div className="mt-2 bg-white/80 rounded-[10px] p-3 space-y-1.5">
                    {nudge.why_trace.data_points.map((pt, i) => (
                      <p key={i} className="text-[11px] text-idbi-faint flex gap-1.5">
                        <span className="text-idbi-green shrink-0">·</span>
                        <span>{pt}</span>
                      </p>
                    ))}
                    <p className="text-[11px] text-idbi-slate font-medium flex gap-1.5 mt-1 pt-1 border-t border-idbi-line">
                      <span className="text-idbi-green shrink-0">∴</span>
                      <span>{nudge.why_trace.calculation}</span>
                    </p>
                  </div>
                )}

                <button
                  onClick={() => onNudgeSelect(nudge.chat_seed)}
                  className="mt-3 text-[12px] font-bold text-white bg-idbi-green px-4 py-1.5 rounded-full hover:bg-idbi-dark transition-colors shadow-[0_4px_12px_-4px_rgba(0,131,108,.5)]"
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
