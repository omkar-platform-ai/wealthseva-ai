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
    // Floating pill bar — sits above the safe-area inset, matches redesign.
    <nav className="md:hidden fixed inset-x-0 bottom-0 z-40 px-4 pb-[max(env(safe-area-inset-bottom),12px)] pt-2 pointer-events-none">
      <div className="pointer-events-auto mx-auto max-w-md bg-white/95 backdrop-blur-md border border-idbi-line rounded-[22px] shadow-float grid grid-cols-4 p-1.5">
        {tabs.map(({ href, label, Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className="relative flex flex-col items-center gap-1 py-2 rounded-[16px] transition-colors"
            >
              <span
                className={`flex items-center justify-center w-9 h-9 rounded-[13px] transition-all ${
                  active ? 'bg-idbi-light text-idbi-green' : 'text-idbi-faint'
                }`}
              >
                <Icon size={20} strokeWidth={active ? 2.4 : 2} />
              </span>
              <span
                className={`text-[11px] font-semibold leading-none transition-colors ${
                  active ? 'text-idbi-green' : 'text-idbi-faint'
                }`}
              >
                {label}
              </span>
              {active && (
                <span className="absolute -top-0.5 h-1 w-1 rounded-full bg-idbi-orange" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
