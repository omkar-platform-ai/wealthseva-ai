'use client';
import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import AvatarChat from '@/components/AvatarChat';
import EscalateAdvisorModal from '@/components/EscalateAdvisorModal';
import ConsentGate from '@/components/ConsentGate';

export default function AdvisorPage() {
  const t = useTranslations('advisor');
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [escalateOpen, setEscalateOpen] = useState(false);

  useEffect(() => {
    setHasConsent(localStorage.getItem('wealthseva_consent_v1') === 'true');
  }, []);

  // Avoid flash of unstyled content before localStorage is read
  if (hasConsent === null) return null;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {!hasConsent && (
        <ConsentGate onAccept={() => setHasConsent(true)} />
      )}

      <h1 className="text-2xl font-bold text-idbi-blue mb-6">{t('title')}</h1>
      <AvatarChat />

      <p className="text-xs text-gray-500 text-center mt-1">
        {t('ai_disclaimer')}
      </p>

      <div className="mt-4 flex justify-center">
        <button
          onClick={() => setEscalateOpen(true)}
          className="text-idbi-blue border border-idbi-blue px-4 py-2 rounded-lg text-sm hover:bg-idbi-light transition-colors"
        >
          {t('escalate_cta')}
        </button>
      </div>

      {escalateOpen && (
        <EscalateAdvisorModal onClose={() => setEscalateOpen(false)} />
      )}
    </div>
  );
}
