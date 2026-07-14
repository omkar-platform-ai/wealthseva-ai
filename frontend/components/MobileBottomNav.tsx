'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, MessageCircle, Target, TrendingUp, Map } from 'lucide-react';
import { cn, FOCUS_RING } from '@/lib/utils';

export default function MobileBottomNav() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();

  const tabs = [
    { href: `/${locale}/dashboard`, label: t('dashboard'), Icon: LayoutDashboard },
    { href: `/${locale}/advisor`, label: t('advisor'), Icon: MessageCircle },
    { href: `/${locale}/goals`, label: t('goals'), Icon: Target },
    { href: `/${locale}/insights`, label: t('insights'), Icon: TrendingUp },
    { href: `/${locale}/roadmap`, label: t('roadmap'), Icon: Map },
  ];

  return (
    // Floating pill bar — sits above the safe-area inset.
    <nav className="md:hidden fixed inset-x-0 bottom-0 z-40 px-4 pb-[max(env(safe-area-inset-bottom),12px)] pt-2 pointer-events-none">
      <div className="pointer-events-auto mx-auto max-w-md bg-white/95 backdrop-blur-md border border-idbi-line rounded-card shadow-float grid grid-cols-5 p-1.5">
        {tabs.map(({ href, label, Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? 'page' : undefined}
              className={cn('relative flex flex-col items-center gap-1 py-2 rounded-field transition-colors', FOCUS_RING)}
            >
              <span
                className={cn(
                  'flex items-center justify-center w-9 h-9 rounded-field transition-all',
                  active ? 'bg-idbi-light text-idbi-green' : 'text-idbi-faint',
                )}
              >
                <Icon size={20} strokeWidth={active ? 2.4 : 2} />
              </span>
              <span
                className={cn(
                  'text-xs font-semibold leading-none transition-colors',
                  active ? 'text-idbi-green' : 'text-idbi-faint',
                )}
              >
                {label}
              </span>
              {active && <span className="absolute -top-0.5 h-1 w-1 rounded-full bg-idbi-orange" />}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
