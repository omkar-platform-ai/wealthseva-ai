'use client';
import { useState } from 'react';
import { useTranslations } from 'next-intl';

interface Props {
  onAccept: () => void;
  onDecline: () => void;
}

export default function ConsentGate({ onAccept, onDecline }: Props) {
  const t = useTranslations('consent');
  const [checked, setChecked] = useState(false);

  const handleContinue = () => {
    if (!checked) return;
    localStorage.setItem('wealthseva_consent_v1', 'true');
    onAccept();
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4 flex-shrink-0">
          <span className="text-2xl">🔒</span>
          <div>
            <h2 className="text-lg font-bold text-idbi-green">{t('title')}</h2>
            <p className="text-xs text-gray-500">{t('fiduciary_label')}</p>
          </div>
        </div>

        {/* Scrollable notice body */}
        <div className="overflow-y-auto flex-1 mb-4 pr-1 space-y-4 text-sm text-gray-700 leading-relaxed">
          <p>{t('body')}</p>

          <div className="bg-idbi-light rounded-xl p-4 space-y-2">
            <p className="font-semibold text-idbi-green">{t('data_collected_heading')}</p>
            <p>{t('data_collected_body')}</p>
          </div>

          <div className="bg-idbi-light rounded-xl p-4 space-y-2">
            <p className="font-semibold text-idbi-green">{t('rights_heading')}</p>
            <p>{t('rights_body')}</p>
          </div>

          <div className="bg-idbi-light rounded-xl p-4 space-y-2">
            <p className="font-semibold text-idbi-green">{t('withdraw_heading')}</p>
            <p>{t('withdraw_body')}</p>
          </div>
        </div>

        {/* Checkbox */}
        <label className="flex items-start gap-3 cursor-pointer mb-5 flex-shrink-0">
          <input
            type="checkbox"
            checked={checked}
            onChange={e => setChecked(e.target.checked)}
            className="mt-0.5 w-4 h-4 accent-idbi-green flex-shrink-0"
          />
          <span className="text-sm text-gray-800">{t('checkbox_label')}</span>
        </label>

        {/* Actions */}
        <div className="flex gap-3 flex-shrink-0">
          <button
            onClick={onDecline}
            className="flex-1 border border-gray-300 text-gray-600 py-2 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            {t('decline')}
          </button>
          <button
            onClick={handleContinue}
            disabled={!checked}
            className="flex-1 bg-idbi-green text-white py-2 rounded-xl text-sm font-medium hover:bg-idbi-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {t('continue')}
          </button>
        </div>
      </div>
    </div>
  );
}
