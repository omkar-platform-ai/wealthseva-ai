'use client';
import { useTranslations } from 'next-intl';
import RiskQuiz from '@/components/RiskQuiz';

export default function OnboardingPage() {
  const t = useTranslations('onboarding');

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-idbi-blue mb-3">{t('welcome')}</h1>
          <p className="text-gray-600">{t('subtitle')}</p>
        </div>

        <RiskQuiz />
      </div>
    </div>
  );
}
