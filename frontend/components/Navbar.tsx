'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import LanguageSwitcher from './LanguageSwitcher';

function DemoLink({ locale }: { locale: string }) {
  const params = useSearchParams();
  if (params.get('demo') !== 'true') return null;
  return (
    <Link
      href={`/${locale}/demo?demo=true`}
      className="text-sm text-idbi-gold font-semibold hover:text-white transition-colors border border-idbi-gold/60 px-3 py-1 rounded-full"
    >
      Judge Demo →
    </Link>
  );
}

export default function Navbar() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const [menuOpen, setMenuOpen] = useState(false);

  const links = [
    { href: `/${locale}/dashboard`, label: t('dashboard') },
    { href: `/${locale}/advisor`, label: t('advisor') },
    { href: `/${locale}/goals`, label: t('goals') },
    { href: `/${locale}/insights`, label: t('insights') },
  ];

  return (
    <nav className="bg-idbi-blue text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-idbi-gold font-bold text-xl">WealthSeva</span>
          <span className="text-xs text-blue-200 bg-blue-900 px-2 py-0.5 rounded-full">AI</span>
        </div>

        {/* Desktop nav links */}
        <div className="hidden md:flex items-center gap-6">
          {links.map(link => (
            <Link key={link.href} href={link.href}
              className="text-sm text-blue-100 hover:text-idbi-gold transition-colors">
              {link.label}
            </Link>
          ))}
          <Suspense fallback={null}>
            <DemoLink locale={locale} />
          </Suspense>
        </div>

        <div className="flex items-center gap-2">
          <LanguageSwitcher />
          {/* Hamburger — mobile only */}
          <button
            className="md:hidden p-2 rounded-lg hover:bg-blue-900 transition-colors"
            onClick={() => setMenuOpen(o => !o)}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            <div className="w-5 h-0.5 bg-white mb-1" />
            <div className="w-5 h-0.5 bg-white mb-1" />
            <div className="w-5 h-0.5 bg-white" />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-blue-900 px-4 pb-4">
          {links.map(link => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className="block py-2 text-sm text-blue-100 hover:text-idbi-gold transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
