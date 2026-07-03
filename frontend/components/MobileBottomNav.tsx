'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, MessageCircle, Target, TrendingUp } from 'lucide-react';

export default function MobileBottomNav() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();

  const tabs = [
    { href: `/${locale}/dashboard`, label: t('dashboard'), Icon: LayoutDashboard },
    { href: `/${locale}/advisor`, label: t('advisor'), Icon: MessageCircle },
    { href: `/${locale}/goals`, label: t('goals'), Icon: Target },
    { href: `/${locale}/insights`, label: t('insights'), Icon: TrendingUp },
  ];

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-gray-200 pb-[env(safe-area-inset-bottom)]">
      <div className="grid grid-cols-4">
        {tabs.map(({ href, label, Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-1 py-2 text-xs font-medium transition-colors ${
                active ? 'text-idbi-blue' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              <Icon size={20} strokeWidth={active ? 2.4 : 2} />
              {label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
