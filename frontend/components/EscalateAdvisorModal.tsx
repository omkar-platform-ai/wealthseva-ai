'use client';
import { useTranslations } from 'next-intl';
import { Phone, Landmark } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';

interface Props {
  onClose: () => void;
}

export default function EscalateAdvisorModal({ onClose }: Props) {
  const t = useTranslations('advisor');

  return (
    <Modal open onClose={onClose} size="sm">
      <div className="p-6">
        <h2 className="text-lg font-bold text-idbi-green mb-1">{t('escalate_cta')}</h2>
        <p className="text-xs text-idbi-muted mb-5">{t('escalate_subtitle')}</p>

        <div className="space-y-3 mb-6">
          <div className="flex items-start gap-3 p-3 bg-idbi-light rounded-field">
            <Phone className="text-idbi-green mt-0.5" size={18} />
            <div>
              <p className="text-sm font-semibold text-idbi-slate">{t('escalate_phone_label')}</p>
              <p className="text-sm text-idbi-green font-bold">1800-200-1947</p>
              <p className="text-xs text-idbi-muted">{t('escalate_phone_hours')}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 bg-idbi-light rounded-field">
            <Landmark className="text-idbi-green mt-0.5" size={18} />
            <div>
              <p className="text-sm font-semibold text-idbi-slate">{t('escalate_branch_label')}</p>
              <p className="text-xs text-idbi-muted">{t('escalate_branch_desc')}</p>
            </div>
          </div>
        </div>

        <Button onClick={onClose} className="w-full">
          {t('escalate_close')}
        </Button>
      </div>
    </Modal>
  );
}
