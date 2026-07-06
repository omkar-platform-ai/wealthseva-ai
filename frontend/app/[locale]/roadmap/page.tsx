'use client';
import { useTranslations } from 'next-intl';
import { CheckCircle2, CircleDashed, Circle, Map } from 'lucide-react';
import FadeIn from '@/components/FadeIn';

interface RoadmapItem {
  title: string;
  desc: string;
}

interface RoadmapPhase {
  tag: string;
  status: 'shipped' | 'next' | 'planned';
  items: RoadmapItem[];
}

// Per-status visual treatment. Full class strings so Tailwind keeps them at build.
const STATUS_STYLE = {
  shipped: { Icon: CheckCircle2, pill: 'bg-idbi-light text-idbi-green', ring: 'border-idbi-green/20', icon: 'text-idbi-green' },
  next: { Icon: CircleDashed, pill: 'bg-orange-50 text-idbi-orange', ring: 'border-idbi-orange/20', icon: 'text-idbi-orange' },
  planned: { Icon: Circle, pill: 'bg-gray-100 text-idbi-muted', ring: 'border-idbi-line', icon: 'text-idbi-faint' },
} as const;

export default function RoadmapPage() {
  const t = useTranslations('roadmap');
  const phases = t.raw('phases') as RoadmapPhase[];

  return (
    <div className="max-w-[1100px] mx-auto px-5 sm:px-7 py-8">
      {/* Header */}
      <div className="mb-8 flex items-start gap-3.5">
        <span className="w-11 h-11 rounded-[13px] bg-idbi-light flex items-center justify-center shrink-0">
          <Map size={22} className="text-idbi-green" strokeWidth={2.1} />
        </span>
        <div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-idbi-ink">{t('title')}</h1>
          <p className="mt-1.5 text-[13.5px] text-idbi-muted max-w-[560px]">{t('subtitle')}</p>
        </div>
      </div>

      {/* Phase columns */}
      <div className="grid gap-5 md:grid-cols-3">
        {phases.map((phase, pi) => {
          const s = STATUS_STYLE[phase.status] ?? STATUS_STYLE.planned;
          return (
            <FadeIn key={phase.tag} delay={pi * 0.1}>
              <section className={`h-full bg-white rounded-[20px] border ${s.ring} shadow-card p-5`}>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[12.5px] font-bold text-idbi-slate">{phase.tag}</span>
                  <span className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-1 rounded-full ${s.pill}`}>
                    <s.Icon size={13} strokeWidth={2.4} />
                    {t(`status_${phase.status}`)}
                  </span>
                </div>
                <ul className="space-y-3">
                  {phase.items.map((item, ii) => (
                    <li key={ii} className="flex items-start gap-2.5">
                      <s.Icon size={16} strokeWidth={2.2} className={`mt-0.5 shrink-0 ${s.icon}`} />
                      <div>
                        <p className="text-[13.5px] font-bold text-idbi-ink leading-snug">{item.title}</p>
                        <p className="mt-0.5 text-[12.5px] text-idbi-muted leading-relaxed">{item.desc}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            </FadeIn>
          );
        })}
      </div>

      <p className="text-center text-[11.5px] text-idbi-faint mt-8">{t('note')}</p>
    </div>
  );
}
