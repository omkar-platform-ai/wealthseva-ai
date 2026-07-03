'use client';
import { useTranslations } from 'next-intl';
import GoalPlanner from '@/components/GoalPlanner';

export default function GoalsPage() {
  const t = useTranslations('goals');

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-idbi-green mb-6">{t('title')}</h1>
      <GoalPlanner />
    </div>
  );
}
