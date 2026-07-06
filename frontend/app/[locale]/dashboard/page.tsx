'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { TrendingUp, IndianRupee, ArrowRight } from 'lucide-react';
import PortfolioCard from '@/components/PortfolioCard';
import RiskProfileBadge from '@/components/RiskProfileBadge';
import FadeIn from '@/components/FadeIn';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

// Decorative sparkline path — purely visual, no fabricated figures.
const SPARK =
  'M0,34 C25,30 40,36 62,28 C88,19 104,26 128,20 C150,15 168,24 190,16 C214,8 232,18 258,10 C276,5 288,9 300,6';

interface Holding { current_value: number; gain_loss_pct: number; }
interface Goal { monthly_sip: number; }

interface PortfolioSummary {
  value: number | null;
  gainPct: number | null;
  risk: string;
  sip: number | null;
}

function DashboardInner() {
  const t = useTranslations('dashboard');
  const locale = useLocale();
  const searchParams = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';

  const [summary, setSummary] = useState<PortfolioSummary>({ value: null, gainPct: null, risk: 'moderate', sip: null });
  const [insights, setInsights] = useState<string[]>([]);
  const [insightsLoading, setInsightsLoading] = useState(false);

  // ---- Backend wiring: real portfolio / risk / goals from the IDBI sandbox ----
  // These endpoints are mock-backed on the server, so they always resolve with
  // Ramesh's coherent demo customer until live sandbox access is granted.
  useEffect(() => {
    let cancelled = false;

    const num = (v: unknown) => (typeof v === 'number' && isFinite(v) ? v : 0);

    async function loadSummary() {
      try {
        const [pfRes, riskRes, goalsRes] = await Promise.all([
          fetch(`${BACKEND_URL}/api/idbi/portfolio`),
          fetch(`${BACKEND_URL}/api/idbi/risk`),
          fetch(`${BACKEND_URL}/api/idbi/goals`),
        ]);
        const [pf, risk, goals] = await Promise.all([pfRes.json(), riskRes.json(), goalsRes.json()]);

        const holdings: Holding[] = Array.isArray(pf?.data) ? pf.data : [];
        const totalValue = holdings.reduce((sum, h) => sum + num(h.current_value), 0);
        // value-weighted average gain — a real figure, not fabricated
        const weightedGain = totalValue > 0
          ? holdings.reduce((s, h) => s + num(h.current_value) * num(h.gain_loss_pct), 0) / totalValue
          : null;

        const goalList: Goal[] = Array.isArray(goals?.data) ? goals.data : [];
        const totalSip = goalList.reduce((s, g) => s + num(g.monthly_sip), 0);

        if (cancelled) return;
        setSummary({
          value: totalValue > 0 ? Math.round(totalValue) : null,
          gainPct: weightedGain != null ? Math.round(weightedGain * 10) / 10 : null,
          risk: (risk?.data?.profile as string) || 'moderate',
          sip: totalSip > 0 ? Math.round(totalSip) : null,
        });
      } catch {
        if (!cancelled) setSummary({ value: null, gainPct: null, risk: 'moderate', sip: null });
      }
    }

    loadSummary();
    return () => { cancelled = true; };
  }, []);

  // Insights strip. In demo mode we serve canned insights from messages so they
  // re-localise on language switch (locale is in the dep array); live mode fetches.
  useEffect(() => {
    if (isDemo) { setInsights(t.raw('demo_insights') as string[]); return; }
    setInsightsLoading(true);
    fetch(`${BACKEND_URL}/api/insights?language=${locale}`)
      .then(r => r.json())
      .then(data => {
        const bullets = Array.isArray(data.insights) ? data.insights : Array.isArray(data.bullets) ? data.bullets : [];
        setInsights(bullets);
      })
      .catch(() => setInsights([]))
      .finally(() => setInsightsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale, isDemo]);

  const { value: portfolioValue, gainPct, risk: riskProfile, sip: monthlySip } = summary;
  const gainPositive = (gainPct ?? 0) >= 0;

  return (
    <div className="max-w-[1200px] mx-auto px-5 sm:px-7 py-8">
      {isDemo && (
        <div className="mb-5 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-sm font-semibold">
          {t('demo_banner')}
        </div>
      )}

      {/* Header */}
      <div className="flex items-end justify-between gap-5 mb-6 flex-wrap">
        <h1 className="text-[30px] font-extrabold tracking-tight text-idbi-ink">{t('title')}</h1>
        <div className="flex items-center gap-2 bg-white border border-idbi-line px-3.5 py-2 rounded-xl shadow-[0_1px_2px_rgba(16,40,34,.04)]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_0_3px_rgba(34,176,125,.18)]" />
          <span className="text-[12.5px] font-semibold text-idbi-slate">{t('sync_status')}</span>
        </div>
      </div>

      {/* KPI ROW */}
      <FadeIn className="grid grid-cols-1 md:grid-cols-[1.15fr_1fr_1fr] gap-[18px] mb-[18px]">
        {/* Portfolio value — gradient hero (real value from backend) */}
        <div className="relative overflow-hidden rounded-[20px] p-6 text-white bg-gradient-to-b from-idbi-green to-idbi-deep shadow-[0_18px_40px_-22px_rgba(0,73,60,.8)]">
          <div className="absolute -right-8 -top-8 w-36 h-36 rounded-full bg-white/[0.06]" />
          <div className="relative flex items-center justify-between">
            <p className="text-[13px] font-semibold text-[#BFE6DC]">{t('portfolio_value')}</p>
            {gainPct != null && (
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${gainPositive ? 'text-[#0B4C3E] bg-[#8FE0C4]' : 'text-white bg-red-500/80'}`}>
                {gainPositive ? '▲' : '▼'} {Math.abs(gainPct)}%
              </span>
            )}
          </div>
          <p className="relative mt-2.5 mb-1 text-[34px] font-extrabold tracking-tight">
            {portfolioValue != null ? `₹${portfolioValue.toLocaleString('en-IN')}` : '—'}
          </p>
          <p className="relative mb-3.5 text-[12.5px] text-[#A9DBCC]">
            {portfolioValue != null ? t('value_subtitle_linked') : t('value_subtitle_empty')}
          </p>
          <svg width="100%" height="46" viewBox="0 0 300 46" preserveAspectRatio="none" className="relative block">
            <defs>
              <linearGradient id="spark" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor="#8FE0C4" stopOpacity=".45" />
                <stop offset="1" stopColor="#8FE0C4" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d={`${SPARK} L300,46 L0,46 Z`} fill="url(#spark)" />
            <path d={SPARK} fill="none" stroke="#C6F1E0" strokeWidth="2.2" strokeLinecap="round" />
          </svg>
        </div>

        {/* Risk profile (gauge card, driven by /api/idbi/risk) */}
        <RiskProfileBadge profile={riskProfile} />

        {/* Monthly SIP (sum of goal SIPs from /api/idbi/goals) */}
        <div className="bg-white rounded-[20px] border border-idbi-line p-6 shadow-card">
          <div className="flex items-center justify-between">
            <p className="text-[13px] font-semibold text-idbi-muted">{t('monthly_sip')}</p>
            <span className="w-[30px] h-[30px] rounded-[9px] bg-idbi-light flex items-center justify-center">
              <IndianRupee size={15} className="text-idbi-green" strokeWidth={2.2} />
            </span>
          </div>
          <p className="mt-2.5 mb-1 text-[32px] font-extrabold tracking-tight text-idbi-ink">
            {monthlySip != null ? `₹${monthlySip.toLocaleString('en-IN')}` : '—'}
          </p>
          <p className="mb-3.5 text-[12.5px] text-idbi-muted">{monthlySip != null ? t('sip_subtitle_active') : t('sip_subtitle_empty')}</p>
          <div className="h-2 rounded-full bg-idbi-light overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-idbi-green to-idbi-teal" style={{ width: monthlySip != null ? '72%' : '0%' }} />
          </div>
          <p className="mt-2 text-[11.5px] font-semibold text-idbi-faint">
            {monthlySip != null ? t('sip_recommended', { pct: 72, amount: '22,000' }) : t('sip_setup_prompt')}
          </p>
        </div>
      </FadeIn>

      {/* Portfolio Analysis */}
      <FadeIn delay={0.08} className="mb-[18px]">
        <PortfolioCard />
      </FadeIn>

      {/* Today's Insights */}
      <FadeIn delay={0.16} className="bg-white rounded-[20px] border border-idbi-line p-6 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-idbi-ink">{t('insights_title')}</h2>
          <a href={`/${locale}/insights`} className="inline-flex items-center gap-1 text-[12.5px] font-bold text-idbi-green hover:text-idbi-dark transition-colors">
            {t('view_all')} <ArrowRight size={14} />
          </a>
        </div>
        {insightsLoading ? (
          <div className="grid sm:grid-cols-3 gap-3.5">
            {[0, 1, 2].map(i => (
              <div key={i} className="border border-idbi-line rounded-[14px] p-4 animate-pulse">
                <div className="w-[30px] h-[30px] rounded-[9px] bg-idbi-light mb-2.5" />
                <div className="h-3 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : insights.length === 0 ? (
          <p className="text-sm text-idbi-faint">—</p>
        ) : (
          <div className="grid sm:grid-cols-3 gap-3.5">
            {insights.slice(0, 3).map((item, i) => (
              <div key={i} className="border border-idbi-line rounded-[14px] p-4 bg-[#FBFDFC]">
                <div className="w-[30px] h-[30px] rounded-[9px] bg-idbi-light flex items-center justify-center mb-2.5">
                  <TrendingUp size={15} className="text-idbi-green" strokeWidth={2.2} />
                </div>
                <p className="text-[12.5px] leading-relaxed text-idbi-slate">{item}</p>
              </div>
            ))}
          </div>
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
