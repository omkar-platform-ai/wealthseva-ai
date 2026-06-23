'use client';
import { useTranslations } from 'next-intl';
import AvatarChat from '@/components/AvatarChat';

export default function AdvisorPage() {
  const t = useTranslations('advisor');

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-idbi-blue mb-6">{t('title')}</h1>
      <AvatarChat />
    </div>
  );
}
