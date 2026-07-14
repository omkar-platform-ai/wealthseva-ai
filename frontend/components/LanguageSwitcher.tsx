'use client';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter, usePathname } from '../navigation';
import { useEffect, useRef, useState } from 'react';
import { Globe, Check } from 'lucide-react';
import { cn, FOCUS_RING } from '@/lib/utils';
import { useToast } from '@/components/ui/Toast';

const LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
];

export default function LanguageSwitcher() {
  const locale = useLocale();
  const t = useTranslations('nav');
  const router = useRouter();
  const pathname = usePathname();
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const switchLanguage = (newLocale: string) => {
    // next-intl's usePathname() strips the query string, so re-attach the
    // current search params — otherwise switching locale drops ?demo=true
    // and the Judge Demo page falls back to its "not a demo" prompt.
    const search = typeof window !== 'undefined' ? window.location.search : '';
    router.push(search ? `${pathname}${search}` : pathname, { locale: newLocale });
    setOpen(false);

    const lang = LANGUAGES.find(l => l.code === newLocale);
    if (lang) {
      setTimeout(
        () => toast({ tone: 'success', message: t('switched_to', { language: lang.native }), duration: 2500 }),
        100,
      );
    }
  };

  const current = LANGUAGES.find(l => l.code === locale);

  return (
    <div className="relative" ref={wrapRef}>
      <button
        onClick={() => setOpen(!open)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-field border border-white/40 text-white hover:bg-white/10 transition-colors font-medium text-sm',
          FOCUS_RING,
        )}
      >
        <Globe size={16} />
        <span>{current?.native ?? 'EN'}</span>
        <span className="text-xs">▼</span>
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute right-0 mt-2 w-44 max-w-[calc(100vw-2rem)] bg-white rounded-field shadow-pop border border-idbi-line z-50 overflow-hidden"
        >
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              role="option"
              aria-selected={lang.code === locale}
              onClick={() => switchLanguage(lang.code)}
              className={cn(
                'w-full text-left px-4 py-3 hover:bg-idbi-light hover:text-idbi-green transition-colors flex justify-between items-center',
                FOCUS_RING,
                lang.code === locale ? 'bg-idbi-light text-idbi-green font-semibold' : 'text-idbi-ink',
              )}
            >
              <span>{lang.native}</span>
              <span className="flex items-center gap-1.5">
                {lang.code === locale && <Check size={13} />}
                <span className="text-xs text-idbi-faint">{lang.label}</span>
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
