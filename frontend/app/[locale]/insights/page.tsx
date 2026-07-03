'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useCallback, useEffect, useState } from 'react';
import { TrendingUp, RefreshCw } from 'lucide-react';
import FadeIn from '@/components/FadeIn';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

type Status = 'loading' | 'ready' | 'error';

export default function InsightsPage() {
  const t = useTranslations('insights');
  const locale = useLocale();
  const [insights, setInsights] = useState<string[]>([]);
  const [status, setStatus] = useState<Status>('loading');

  // ---- Backend wiring: GET /api/insights ----
  const load = useCallback(async () => {
    setStatus('loading');
    try {
      const res = await fetch(`${BACKEND_URL}/api/insights?language=${locale}`);
      if (!res.ok) throw new Error('failed');
      const data = await res.json();
      setInsights(Array.isArray(data.insights) ? data.insights : []);
      setStatus('ready');
    } catch {
      setStatus('error');
    }
  }, [locale]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="max-w-[760px] mx-auto px-5 sm:px-7 py-8">
      <div className="mb-6">
        <h1 className="text-[28px] font-extrabold tracking-tight text-idbi-ink">{t('title')}</h1>
        <p className="mt-1.5 text-[13.5px] text-idbi-muted">{t('subtitle')}</p>
      </div>

      {status === 'loading' && (
        <div className="space-y-3.5">
          {[0, 1, 2].map(i => (
            <div key={i} className="bg-white rounded-[18px] border border-idbi-line shadow-card p-5 animate-pulse flex items-start gap-4">
              <div className="w-10 h-10 rounded-[12px] bg-idbi-light shrink-0" />
              <div className="flex-1 pt-1">
                <div className="h-3.5 bg-gray-200 rounded w-3/4 mb-2" />
                <div className="h-3.5 bg-gray-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {status === 'error' && (
        <div className="bg-white rounded-[18px] border border-idbi-line shadow-card p-8 text-center">
          <p className="text-idbi-slate mb-4">{t('error')}</p>
          <button
            onClick={load}
            className="inline-flex items-center gap-2 bg-idbi-green text-white px-5 py-2.5 rounded-xl text-sm font-bold hover:bg-idbi-dark transition-colors"
          >
            <RefreshCw size={14} />
            {t('retry')}
          </button>
        </div>
      )}

      {status === 'ready' && insights.length === 0 && (
        <div className="bg-white rounded-[18px] border border-idbi-line shadow-card p-8 text-center">
          <p className="text-idbi-faint">{t('empty')}</p>
        </div>
      )}

      {status === 'ready' && insights.length > 0 && (
        <div className="space-y-3.5">
          {insights.map((item, i) => (
            <FadeIn key={i} delay={i * 0.08}>
              <div className="bg-white rounded-[18px] border border-idbi-line shadow-card p-5 flex items-start gap-4 hover:border-idbi-green/25 transition-colors">
                <div className="w-10 h-10 rounded-[12px] bg-idbi-light flex items-center justify-center shrink-0">
                  <TrendingUp size={19} className="text-idbi-green" strokeWidth={2.2} />
                </div>
                <p className="text-[14px] leading-relaxed text-idbi-slate pt-0.5">{item}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      )}

      <p className="text-center text-[11.5px] text-idbi-faint mt-6">{t('disclaimer')}</p>
    </div>
  );
}
