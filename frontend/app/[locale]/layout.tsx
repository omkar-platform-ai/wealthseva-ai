import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { Montserrat } from 'next/font/google';
import '../globals.css';
import Navbar from '@/components/Navbar';
import MobileBottomNav from '@/components/MobileBottomNav';

const montserrat = Montserrat({ subsets: ['latin'] });

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();

  return (
    <html lang={locale}>
      {/* pb-28 leaves room for the floating mobile bottom nav */}
      <body className={`${montserrat.className} antialiased bg-idbi-bg`}>
        <NextIntlClientProvider messages={messages}>
          <Navbar />
          <main className="min-h-screen pb-28 md:pb-0">
            {children}
          </main>
          <MobileBottomNav />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
