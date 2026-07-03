'use client';
import { useTranslations } from 'next-intl';

const COLORS = { conservative: 'bg-green-100 text-green-800', moderate: 'bg-yellow-100 text-yellow-800', aggressive: 'bg-red-100 text-red-800' };

export default function RiskProfileBadge({ profile = 'moderate' }: { profile?: string }) {
  const t = useTranslations('onboarding');
  const tDash = useTranslations('dashboard');
  const label = t(profile as 'conservative' | 'moderate' | 'aggressive');
  return (
    <div className="bg-white rounded-2xl shadow p-6">
      <p className="text-sm text-gray-500 mb-2">{tDash('risk_profile')}</p>
      <span className={`px-3 py-1 rounded-full text-sm font-semibold capitalize ${COLORS[profile as keyof typeof COLORS]}`}>{label}</span>
    </div>
  );
}
