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
      <body className={`${montserrat.className} antialiased`}>
        <NextIntlClientProvider messages={messages}>
          <Navbar />
          <main className="min-h-screen bg-gray-50 pb-20 md:pb-0">
            {children}
          </main>
          <MobileBottomNav />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
