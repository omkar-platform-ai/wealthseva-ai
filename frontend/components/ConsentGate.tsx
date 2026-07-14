'use client';
import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Lock } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';

interface Props {
  onAccept: () => void;
  onDecline: () => void;
}

export default function ConsentGate({ onAccept, onDecline }: Props) {
  const t = useTranslations('consent');
  const [checked, setChecked] = useState(false);

  const handleContinue = () => {
    if (!checked) return;
    sessionStorage.setItem('wealthseva_consent_v1', 'true');
    onAccept();
  };

  // closeOnBackdrop is false: the DPDP consent gate must be answered
  // explicitly. Escape maps to decline (Modal onClose).
  return (
    <Modal open onClose={onDecline} closeOnBackdrop={false} size="md">
      <div className="p-6 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4 flex-shrink-0">
          <Lock className="text-idbi-green" size={22} />
          <div>
            <h2 className="text-lg font-bold text-idbi-green">{t('title')}</h2>
            <p className="text-xs text-idbi-muted">{t('fiduciary_label')}</p>
          </div>
        </div>

        {/* Scrollable notice body */}
        <div className="overflow-y-auto flex-1 mb-4 pr-1 space-y-4 text-sm text-idbi-slate leading-relaxed">
          <p>{t('body')}</p>

          <div className="bg-idbi-light rounded-field p-4 space-y-2">
            <p className="font-semibold text-idbi-green">{t('data_collected_heading')}</p>
            <p>{t('data_collected_body')}</p>
          </div>

          <div className="bg-idbi-light rounded-field p-4 space-y-2">
            <p className="font-semibold text-idbi-green">{t('rights_heading')}</p>
            <p>{t('rights_body')}</p>
          </div>

          <div className="bg-idbi-light rounded-field p-4 space-y-2">
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
          <span className="text-sm text-idbi-slate">{t('checkbox_label')}</span>
        </label>

        {/* Actions */}
        <div className="flex gap-3 flex-shrink-0">
          <Button variant="secondary" onClick={onDecline} className="flex-1">
            {t('decline')}
          </Button>
          <Button onClick={handleContinue} disabled={!checked} className="flex-1">
            {t('continue')}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
