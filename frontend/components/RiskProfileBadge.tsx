'use client';
import { useTranslations } from 'next-intl';

// Gauge position + badge treatment per profile (kept on-brand).
// Note copy lives in messages (risk.note_*) so it localises on language switch.
const META: Record<string, { pct: number; label: number; badge: string }> = {
  conservative: { pct: 0.28, label: 28, badge: 'bg-[#E4F4EC] text-[#1E7A4E]' },
  moderate: { pct: 0.45, label: 45, badge: 'bg-[#FFF3D6] text-[#9A6C00]' },
  aggressive: { pct: 0.72, label: 72, badge: 'bg-[#FDE7DD] text-[#C25A15]' },
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
    <div className="bg-white rounded-[20px] border border-idbi-line p-6 shadow-card">
      <p className="text-[13px] font-semibold text-idbi-muted mb-4">{tDash('risk_profile')}</p>
      <div className="flex items-center gap-4">
        <svg width="74" height="74" viewBox="0 0 74 74" className="shrink-0">
          <circle cx="37" cy="37" r={R} fill="none" stroke="#EEF3F1" strokeWidth="8" />
          <circle
            cx="37" cy="37" r={R} fill="none" stroke="#F37021" strokeWidth="8" strokeLinecap="round"
            strokeDasharray={C} strokeDashoffset={offset} transform="rotate(-90 37 37)"
          />
          <text x="37" y="41" textAnchor="middle" fontSize="15" fontWeight="800" fill="#122622" fontFamily="Montserrat">
            {meta.label}
          </text>
        </svg>
        <div>
          <span className={`inline-block text-[13px] font-bold capitalize px-3 py-1.5 rounded-full ${meta.badge}`}>
            {label}
          </span>
          <p className="mt-2.5 text-[12px] leading-snug text-idbi-faint">{tRisk(noteKey)}</p>
        </div>
      </div>
    </div>
  );
}
