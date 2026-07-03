'use client';
import { useTranslations } from 'next-intl';

interface Props {
  onClose: () => void;
}

export default function EscalateAdvisorModal({ onClose }: Props) {
  const t = useTranslations('advisor');

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-6"
        onClick={e => e.stopPropagation()}
      >
        <h2 className="text-lg font-bold text-idbi-green mb-1">{t('escalate_cta')}</h2>
        <p className="text-xs text-gray-500 mb-5">{t('escalate_subtitle')}</p>

        <div className="space-y-3 mb-6">
          <div className="flex items-start gap-3 p-3 bg-idbi-light rounded-xl">
            <span className="text-idbi-green text-lg">📞</span>
            <div>
              <p className="text-sm font-semibold text-gray-800">{t('escalate_phone_label')}</p>
              <p className="text-sm text-idbi-green font-bold">1800-200-1947</p>
              <p className="text-xs text-gray-500">{t('escalate_phone_hours')}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-idbi-light rounded-xl">
            <span className="text-idbi-green text-lg">🏦</span>
            <div>
              <p className="text-sm font-semibold text-gray-800">{t('escalate_branch_label')}</p>
              <p className="text-xs text-gray-500">{t('escalate_branch_desc')}</p>
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full bg-idbi-green text-white py-2 rounded-xl text-sm font-medium hover:bg-idbi-dark transition-colors"
        >
          {t('escalate_close')}
        </button>
      </div>
    </div>
  );
}
