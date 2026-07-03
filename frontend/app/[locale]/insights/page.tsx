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

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-idbi-green mb-1">{t('title')}</h1>
      <p className="text-sm text-gray-500 mb-6">{t('subtitle')}</p>

      {status === 'loading' && (
        <div className="space-y-4">
          {[0, 1, 2].map(i => (
            <div key={i} className="bg-white rounded-2xl shadow p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {status === 'error' && (
        <div className="bg-white rounded-2xl shadow p-8 text-center">
          <p className="text-gray-600 mb-4">{t('error')}</p>
          <button
            onClick={load}
            className="inline-flex items-center gap-2 bg-idbi-green text-white px-5 py-2 rounded-xl text-sm font-medium hover:bg-idbi-dark transition-colors"
          >
            <RefreshCw size={14} />
            {t('retry')}
          </button>
        </div>
      )}

      {status === 'ready' && insights.length === 0 && (
        <div className="bg-white rounded-2xl shadow p-8 text-center">
          <p className="text-gray-500">{t('empty')}</p>
        </div>
      )}

      {status === 'ready' && insights.length > 0 && (
        <div className="space-y-4">
          {insights.map((item, i) => (
            <FadeIn key={i} delay={i * 0.08}>
              <div className="bg-white rounded-2xl shadow p-6 flex items-start gap-4">
                <div className="w-9 h-9 rounded-full bg-idbi-light flex items-center justify-center flex-shrink-0">
                  <TrendingUp size={16} className="text-idbi-green" />
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">{item}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-400 text-center mt-6">{t('disclaimer')}</p>
    </div>
  );
}
