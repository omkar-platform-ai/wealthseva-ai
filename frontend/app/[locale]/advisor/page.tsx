'use client';
import { useState, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import AvatarChat from '@/components/AvatarChat';
import MoneyMoments from '@/components/MoneyMoments';
import ConsentGate from '@/components/ConsentGate';

export default function AdvisorPage() {
  const t = useTranslations('advisor');
  const tc = useTranslations('consent');
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [declined, setDeclined] = useState(false);
  const [nudgeSeed, setNudgeSeed] = useState<string | undefined>();
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHasConsent(localStorage.getItem('wealthseva_consent_v1') === 'true');
  }, []);

  const handleNudgeSelect = (seed: string) => {
    setNudgeSeed(seed);
    chatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Avoid flash of unstyled content before localStorage is read
  if (hasConsent === null) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {!hasConsent && !declined && (
        <ConsentGate
          onAccept={() => setHasConsent(true)}
          onDecline={() => setDeclined(true)}
        />
      )}

      {declined && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 text-center">
            <span className="text-4xl mb-4 block">🔒</span>
            <h2 className="text-lg font-bold text-idbi-green mb-3">{tc('declined_title')}</h2>
            <p className="text-sm text-gray-700 mb-6">{tc('declined_body')}</p>
            <button
              onClick={() => setDeclined(false)}
              className="w-full bg-idbi-green text-white py-2 rounded-xl text-sm font-medium hover:bg-idbi-dark transition-colors"
            >
              {tc('declined_review_cta')}
            </button>
          </div>
        </div>
      )}

      <h1 className="text-2xl font-bold text-idbi-green mb-6">{t('title')}</h1>

      <div ref={chatRef}>
        <AvatarChat initialMessage={nudgeSeed} />
      </div>

      <p className="text-xs text-gray-500 text-center mt-1">
        {t('ai_disclaimer')}
      </p>

      <MoneyMoments onNudgeSelect={handleNudgeSelect} />
    </div>
  );
}
