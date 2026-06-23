'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import LanguageSwitcher from './LanguageSwitcher';

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
    <nav className="bg-idbi-blue text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-idbi-gold font-bold text-xl">WealthSeva</span>
          <span className="text-xs text-blue-200 bg-blue-900 px-2 py-0.5 rounded-full">AI</span>
        </div>
        <div className="hidden md:flex items-center gap-6">
          {links.map(link => (
            <Link key={link.href} href={link.href}
              className="text-sm text-blue-100 hover:text-idbi-gold transition-colors">
              {link.label}
            </Link>
          ))}
        </div>
        <LanguageSwitcher />
      </div>
    </nav>
  );
}
