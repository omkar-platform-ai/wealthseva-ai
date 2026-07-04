'use client';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter, usePathname } from 'next/navigation';
import { useState } from 'react';
import { Globe } from 'lucide-react';

const LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
];

export default function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; message: string }>({ show: false, message: '' });

  const switchLanguage = (newLocale: string) => {
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
    router.push(newPath);
    setOpen(false);
    
    // Show toast after switch
    const lang = LANGUAGES.find(l => l.code === newLocale);
    if (lang) {
      setTimeout(() => {
        setToast({ show: true, message: `Switched to ${lang.native}` });
        setTimeout(() => setToast({ show: false, message: '' }), 2000);
      }, 100);
    }
  };

  const current = LANGUAGES.find(l => l.code === locale);

  return (
    <>
    {toast.show && (
      <div 
        key={toast.message}
        className="fixed top-20 right-4 bg-idbi-green text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-all duration-300"
        style={{ animation: 'slideInDown 0.3s ease-out' }}
      >
        {toast.message}
      </div>
    )}
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg border border-idbi-green text-idbi-green hover:bg-idbi-light transition-colors font-medium text-sm"
      >
        <Globe size={16} />
        <span>{current?.native ?? 'EN'}</span>
        <span className="text-xs">▼</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-44 max-w-[calc(100vw-2rem)] bg-white rounded-xl shadow-xl border border-gray-200 z-50">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => switchLanguage(lang.code)}
              className={`w-full text-left px-4 py-3 hover:bg-idbi-light hover:text-idbi-green transition-colors first:rounded-t-xl last:rounded-b-xl flex justify-between items-center ${
                lang.code === locale ? 'bg-idbi-light text-idbi-green font-semibold' : 'text-gray-900'
              }`}
            >
              <span>{lang.native}</span>
              <span className="text-xs text-gray-500">{lang.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
    </>
  );
}
