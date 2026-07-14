'use client';
import { useTranslations } from 'next-intl';
import { ShieldCheck } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge, type BadgeTone } from '@/components/ui/Badge';

// Gauge fill + badge tone per profile (single source — was duplicated with
// RiskQuiz). The arc encodes relative risk appetite (conservative → aggressive)
// qualitatively; it deliberately carries no numeric score, since the dashboard
// has no real one. Note copy lives in messages (risk.note_*) so it localises.
const META: Record<string, { pct: number; tone: BadgeTone }> = {
  conservative: { pct: 0.28, tone: 'riskConservative' },
  moderate: { pct: 0.45, tone: 'riskModerate' },
  aggressive: { pct: 0.72, tone: 'riskAggressive' },
};

const R = 31;
const C = 2 * Math.PI * R;

export default function RiskProfileBadge({ profile = 'moderate' }: { profile?: string }) {
  const t = useTranslations('onboarding');
  const tDash = useTranslations('dashboard');
  const tRisk = useTranslations('risk');
  const profileKey = (META[profile] ? profile : 'moderate') as 'conservative' | 'moderate' | 'aggressive';
  const meta = META[profileKey];
  const label = t(profileKey);
  const noteKey = `note_${profileKey}` as const;
  const offset = C * (1 - meta.pct);

  return (
    <Card className="p-6">
      <p className="text-sm font-semibold text-idbi-muted mb-4">{tDash('risk_profile')}</p>
      <div className="flex items-center gap-4">
        <div className="relative w-[74px] h-[74px] shrink-0">
          <svg width="74" height="74" viewBox="0 0 74 74">
            <circle cx="37" cy="37" r={R} fill="none" className="stroke-idbi-track" strokeWidth="8" />
            <circle
              cx="37"
              cy="37"
              r={R}
              fill="none"
              className="stroke-idbi-orange"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={C}
              strokeDashoffset={offset}
              transform="rotate(-90 37 37)"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center">
            <ShieldCheck size={22} className="text-idbi-orange" strokeWidth={2.2} />
          </span>
        </div>
        <div>
          <Badge tone={meta.tone} className="capitalize">{label}</Badge>
          <p className="mt-2.5 text-xs leading-snug text-idbi-faint">{tRisk(noteKey)}</p>
        </div>
      </div>
    </Card>
  );
}
