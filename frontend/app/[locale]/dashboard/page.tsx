'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import PortfolioCard from '@/components/PortfolioCard';
import RiskProfileBadge from '@/components/RiskProfileBadge';
import FadeIn from '@/components/FadeIn';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

// Demo customer: Ramesh, 42 — keep consistent with backend/routers/idbi.py mocks.
// Compliance: no specific market figures in canned insights (FINANCIAL FIGURES rule).
const DEMO_DATA = {
  portfolioValue: 509620,
  riskProfile: 'moderate' as const,
  monthlySip: 16000,
  insights: [
    'Staying invested through market cycles has historically beaten trying to time entries and exits.',
    'Laddering fixed deposits across maturities balances liquidity with returns.',
    'Gold can hedge inflation — most advisors suggest capping it near 10% of your portfolio.',
  ],
};

function DashboardInner() {
  const t = useTranslations('dashboard');
  const locale = useLocale();
  const searchParams = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';

  const [insights, setInsights] = useState<string[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);

  useEffect(() => {
    if (isDemo) {
      setInsights(DEMO_DATA.insights);
      return;
    }
    setInsightsLoading(true);
    fetch(`${BACKEND_URL}/api/insights?language=${locale}`)
      .then(r => r.json())
      .then(data => {
        const bullets = Array.isArray(data.insights) ? data.insights : Array.isArray(data.bullets) ? data.bullets : [];
        setInsights(bullets);
      })
      .catch(() => setInsights([]))
      .finally(() => setInsightsLoading(false));
  }, [locale, isDemo]);

  const portfolioValue = isDemo ? DEMO_DATA.portfolioValue : null;
  const riskProfile = isDemo ? DEMO_DATA.riskProfile : 'moderate';
  const monthlySip = isDemo ? DEMO_DATA.monthlySip : null;

  return (
    <div className="container mx-auto px-4 py-8">
      {isDemo && (
        <div className="mb-4 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm font-medium">
          Demo Mode — pre-populated with sample data
        </div>
      )}

      <h1 className="text-2xl font-bold text-idbi-blue mb-6">{t('title')}</h1>

      {/* 3 stat cards */}
      <FadeIn className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow p-6">
          <p className="text-sm text-gray-500 mb-1">{t('portfolio_value')}</p>
          <p className="text-2xl font-bold text-idbi-blue">
            {portfolioValue != null ? `₹${portfolioValue.toLocaleString('en-IN')}` : '—'}
          </p>
        </div>

        <RiskProfileBadge profile={riskProfile} />

        <div className="bg-white rounded-2xl shadow p-6">
          <p className="text-sm text-gray-500 mb-1">{t('monthly_sip')}</p>
          <p className="text-2xl font-bold text-idbi-blue">
            {monthlySip != null ? `₹${monthlySip.toLocaleString('en-IN')}` : '—'}
          </p>
        </div>
      </FadeIn>

      {/* Portfolio Card */}
      <FadeIn delay={0.08} className="mb-6">
        <PortfolioCard />
      </FadeIn>

      {/* Market insights strip */}
      <FadeIn delay={0.16} className="bg-white rounded-2xl shadow p-6">
        <h2 className="text-lg font-semibold text-idbi-blue mb-3">{t('insights_title')}</h2>
        {insightsLoading ? (
          <div className="space-y-2 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-200 rounded w-2/3" />
            <div className="h-4 bg-gray-100 rounded w-1/2" />
          </div>
        ) : insights.length === 0 ? (
          <p className="text-sm text-gray-400">—</p>
        ) : (
          <ul className="space-y-2">
            {insights.slice(0, 3).map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-idbi-gold font-bold mt-0.5">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        )}
      </FadeIn>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense>
      <DashboardInner />
    </Suspense>
  );
}
