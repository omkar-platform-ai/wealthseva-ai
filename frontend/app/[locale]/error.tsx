'use client';
import { useTranslations } from 'next-intl';

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations('common');

  return (
    <div className="container mx-auto px-4 py-16 text-center">
      <div className="bg-white rounded-2xl shadow p-8 max-w-md mx-auto">
        <p className="text-gray-700 text-lg mb-6">{t('shreya_break')}</p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-idbi-green text-white rounded-lg hover:bg-idbi-dark transition-colors text-sm"
        >
          {t('refresh')}
        </button>
      </div>
    </div>
  );
}
