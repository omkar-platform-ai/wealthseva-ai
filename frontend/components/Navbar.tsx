'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Suspense } from 'react';
import { TrendingUp } from 'lucide-react';
import LanguageSwitcher from './LanguageSwitcher';
import { cn, FOCUS_RING } from '@/lib/utils';

function DemoLink({ locale }: { locale: string }) {
  const t = useTranslations('nav');
  return (
    <Link
      href={`/${locale}/demo?demo=true`}
      className={cn(
        'text-sm text-white/90 font-semibold hover:text-white border border-white/40 px-3 py-1 rounded-full transition-colors',
        FOCUS_RING,
      )}
    >
      {t('judge_demo')} →
    </Link>
  );
}

export default function Navbar() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();

  const links = [
    { href: `/${locale}/dashboard`, label: t('dashboard') },
    { href: `/${locale}/advisor`, label: t('advisor') },
    { href: `/${locale}/goals`, label: t('goals') },
    { href: `/${locale}/insights`, label: t('insights') },
    { href: `/${locale}/roadmap`, label: t('roadmap') },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-idbi-green/95 backdrop-blur-md border-b border-white/10 shadow-[0_8px_30px_-18px_rgba(0,49,40,.6)]">
      <div className="max-w-[1200px] mx-auto px-5 sm:px-7 h-[66px] flex items-center gap-6 sm:gap-9">
        {/* Brand lockup */}
        <Link href={`/${locale}`} className={cn('flex items-center gap-2.5 shrink-0', FOCUS_RING)}>
          <span className="w-[30px] h-[30px] rounded-tile bg-idbi-orange flex items-center justify-center shadow-glowOrange">
            <TrendingUp size={17} strokeWidth={2.4} className="text-white" />
          </span>
          <span className="font-extrabold text-lg tracking-tight text-white">
            Wealth<span className="text-idbi-peach">Seva</span>
          </span>
          <span className="text-xs font-bold tracking-wide text-idbi-mint bg-white/10 px-1.5 py-0.5 rounded-md">
            AI
          </span>
        </Link>

        {/* Desktop nav links with active pill */}
        <div className="hidden md:flex items-center gap-1">
          {links.map(link => {
            const active = pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'text-sm font-semibold px-3.5 py-2 rounded-tile transition-all',
                  FOCUS_RING,
                  active
                    ? 'text-white bg-white/[0.14]'
                    : 'text-idbi-mint hover:text-white hover:bg-white/10',
                )}
              >
                {link.label}
              </Link>
            );
          })}
          <Suspense fallback={null}>
            <DemoLink locale={locale} />
          </Suspense>
        </div>

        <div className="ml-auto flex items-center gap-3.5">
          <LanguageSwitcher />
          <div
            className="w-[34px] h-[34px] rounded-full bg-gradient-to-br from-idbi-orange to-idbi-orangeLight text-white flex items-center justify-center font-bold text-sm ring-2 ring-white/25 shrink-0"
            aria-label="Account"
          >
            R
          </div>
        </div>
      </div>
    </nav>
  );
}
