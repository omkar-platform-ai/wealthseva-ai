'use client';
import { useState, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import AvatarChat from '@/components/AvatarChat';
import MoneyMoments from '@/components/MoneyMoments';
import EscalateAdvisorModal from '@/components/EscalateAdvisorModal';
import ConsentGate from '@/components/ConsentGate';

export default function AdvisorPage() {
  const t = useTranslations('advisor');
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [escalateOpen, setEscalateOpen] = useState(false);
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
      {!hasConsent && (
        <ConsentGate onAccept={() => setHasConsent(true)} />
      )}

      <h1 className="text-2xl font-bold text-idbi-green mb-6">{t('title')}</h1>

      <div ref={chatRef}>
        <AvatarChat initialMessage={nudgeSeed} />
      </div>

      <p className="text-xs text-gray-500 text-center mt-1">
        {t('ai_disclaimer')}
      </p>

      <div className="mt-4 flex justify-center">
        <button
          onClick={() => setEscalateOpen(true)}
          className="text-idbi-green border border-idbi-green px-4 py-2 rounded-lg text-sm hover:bg-idbi-light transition-colors"
        >
          {t('escalate_cta')}
        </button>
      </div>

      <MoneyMoments onNudgeSelect={handleNudgeSelect} />

      {escalateOpen && (
        <EscalateAdvisorModal onClose={() => setEscalateOpen(false)} />
      )}
    </div>
  );
}
