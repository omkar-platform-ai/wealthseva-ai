'use client';
import { useState, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { useRouter } from '@/navigation';
import { Lock } from 'lucide-react';
import AvatarChat from '@/components/AvatarChat';
import MoneyMoments from '@/components/MoneyMoments';
import ConsentGate from '@/components/ConsentGate';
import { Button } from '@/components/ui/Button';

export default function AdvisorPage() {
  const t = useTranslations('advisor');
  const tc = useTranslations('consent');
  const router = useRouter();
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [declined, setDeclined] = useState(false);
  const [nudgeSeed, setNudgeSeed] = useState<string | undefined>();
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHasConsent(sessionStorage.getItem('wealthseva_consent_v1') === 'true');
  }, []);

  const handleNudgeSelect = (seed: string) => {
    setNudgeSeed(seed);
    chatRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Avoid flash of unstyled content before sessionStorage is read
  if (hasConsent === null) return null;

  // Hard gate: AvatarChat (and its backend calls) must NOT mount until consent
  // is granted. Decline shows a blocked overlay; neither path renders the chat.
  if (declined) {
    return (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
        <div className="bg-white rounded-card shadow-pop border border-idbi-line max-w-md w-full p-8 text-center">
          <span className="mx-auto mb-4 flex w-12 h-12 items-center justify-center rounded-card bg-idbi-light">
            <Lock className="text-idbi-green" size={24} />
          </span>
          <h2 className="text-lg font-bold text-idbi-green mb-3">{tc('declined_title')}</h2>
          <p className="text-sm text-idbi-slate mb-6">{tc('declined_body')}</p>
          <Button onClick={() => setDeclined(false)} className="w-full">
            {tc('declined_review_cta')}
          </Button>
          <Button variant="secondary" onClick={() => router.push('/dashboard')} className="w-full mt-3">
            {tc('declined_exit_cta')}
          </Button>
        </div>
      </div>
    );
  }

  if (!hasConsent) {
    return (
      <ConsentGate
        onAccept={() => setHasConsent(true)}
        onDecline={() => setDeclined(true)}
      />
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-idbi-green mb-6">{t('title')}</h1>

      <div ref={chatRef}>
        <AvatarChat initialMessage={nudgeSeed} />
      </div>

      <p className="text-xs text-idbi-faint text-center mt-1">
        {t('ai_disclaimer')}
      </p>

      <MoneyMoments onNudgeSelect={handleNudgeSelect} />
    </div>
  );
}
