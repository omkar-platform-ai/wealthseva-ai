'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import LanguageSwitcher from './LanguageSwitcher';

function DemoLink({ locale }: { locale: string }) {
  const params = useSearchParams();
  if (params.get('demo') !== 'true') return null;
  return (
    <Link
      href={`/${locale}/demo?demo=true`}
      className="text-sm text-idbi-orange font-semibold hover:text-white transition-colors border border-idbi-orange/60 px-3 py-1 rounded-full"
    >
      Judge Demo →
    </Link>
  );
}

export default function Navbar() {
  const t = useTranslations('nav');
  const locale = useLocale();

  const links = [
    { href: `/${locale}/dashboard`, label: t('dashboard') },
    { href: `/${locale}/advisor`, label: t('advisor') },
    { href: `/${locale}/goals`, label: t('goals') },
    { href: `/${locale}/insights`, label: t('insights') },
  ];

  return (
    <nav className="bg-idbi-green text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-idbi-orange font-bold text-xl">WealthSeva</span>
          <span className="text-xs text-emerald-200 bg-idbi-dark px-2 py-0.5 rounded-full">AI</span>
        </div>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-6">
          {links.map(link => (
            <Link key={link.href} href={link.href}
              className="text-sm text-emerald-100 hover:text-idbi-orange transition-colors">
              {link.label}
            </Link>
          ))}
          <Suspense fallback={null}>
            <DemoLink locale={locale} />
          </Suspense>
        </div>

        {/* Mobile navigation lives in MobileBottomNav — only the switcher up top */}
        <LanguageSwitcher />
      </div>
    </nav>
  );
}
