'use client';
import { useState } from 'react';
import { useTranslations } from 'next-intl';

interface Props {
  onAccept: () => void;
}

export default function ConsentGate({ onAccept }: Props) {
  const t = useTranslations('consent');
  const [checked, setChecked] = useState(false);

  const handleContinue = () => {
    if (!checked) return;
    localStorage.setItem('wealthseva_consent_v1', 'true');
    onAccept();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">🔒</span>
          <h2 className="text-lg font-bold text-idbi-green">{t('title')}</h2>
        </div>

        <p className="text-sm text-gray-700 leading-relaxed mb-5">{t('body')}</p>

        <label className="flex items-start gap-3 cursor-pointer mb-6">
          <input
            type="checkbox"
            checked={checked}
            onChange={e => setChecked(e.target.checked)}
            className="mt-0.5 w-4 h-4 accent-idbi-green flex-shrink-0"
          />
          <span className="text-sm text-gray-800">{t('checkbox_label')}</span>
        </label>

        <button
          onClick={handleContinue}
          disabled={!checked}
          className="w-full bg-idbi-green text-white py-2 rounded-xl text-sm font-medium hover:bg-idbi-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {t('continue')}
        </button>
      </div>
    </div>
  );
}
