'use client';
import { useTranslations } from 'next-intl';
import { ShieldCheck } from 'lucide-react';
import RiskQuiz from '@/components/RiskQuiz';

export default function OnboardingPage() {
  const t = useTranslations('onboarding');

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
      {/* Hero */}
      <div className="text-center mb-8">
        <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-idbi-light text-idbi-green text-xs font-bold mb-5">
          <ShieldCheck size={14} />
          {t('assessment_badge')}
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-idbi-ink mb-3 text-balance">
          {t('welcome')}
        </h1>
        <p className="text-idbi-muted text-base max-w-md mx-auto text-pretty">{t('subtitle')}</p>
      </div>

      {/* Quiz card */}
      <div className="bg-white rounded-card border border-idbi-line shadow-pop p-6 sm:p-8">
        <RiskQuiz />
      </div>

      <p className="text-center text-xs text-idbi-faint mt-6">
        {t('privacy_note')}
      </p>
    </div>
  );
}
