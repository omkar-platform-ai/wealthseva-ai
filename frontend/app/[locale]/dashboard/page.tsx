import { useTranslations } from 'next-intl';
import PortfolioCard from '@/components/PortfolioCard';
import RiskProfileBadge from '@/components/RiskProfileBadge';

export default function DashboardPage() {
  const t = useTranslations('dashboard');

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-idbi-blue mb-6">{t('portfolio')}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <RiskProfileBadge />
        <PortfolioCard />
      </div>
    </div>
  );
}
