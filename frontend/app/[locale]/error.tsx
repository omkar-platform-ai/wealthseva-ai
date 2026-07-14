'use client';
import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/Button';

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations('common');

  return (
    <div className="container mx-auto px-4 py-16 text-center">
      <div className="bg-white rounded-card border border-idbi-line shadow-card p-8 max-w-md mx-auto">
        <p className="text-idbi-slate text-lg mb-6">{t('shreya_break')}</p>
        <Button onClick={reset}>{t('refresh')}</Button>
      </div>
    </div>
  );
}
