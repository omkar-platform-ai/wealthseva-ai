'use client';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { Languages, LineChart, Bell, ShieldCheck, UserCheck, Lock, Globe, ArrowRight } from 'lucide-react';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import ShreyaAvatar from '@/components/ShreyaAvatar';
import FadeIn from '@/components/FadeIn';
import { buttonVariants } from '@/components/ui/Button';
import { cn, FOCUS_RING } from '@/lib/utils';

export default function LandingPage() {
  const t = useTranslations('landing');
  const tNav = useTranslations('nav');
  const locale = useLocale();

  const features = [
    { Icon: Languages, title: t('feature_voice_title'), desc: t('feature_voice_desc') },
    { Icon: LineChart, title: t('feature_explain_title'), desc: t('feature_explain_desc') },
    { Icon: Bell, title: t('feature_moments_title'), desc: t('feature_moments_desc') },
  ];

  const steps = [
    { title: t('step1_title'), desc: t('step1_desc') },
    { title: t('step2_title'), desc: t('step2_desc') },
    { title: t('step3_title'), desc: t('step3_desc') },
  ];

  const trust = [
    { Icon: ShieldCheck, label: t('trust_sebi') },
    { Icon: UserCheck, label: t('trust_oversight') },
    { Icon: Lock, label: t('trust_privacy') },
  ];

  return (
    <div>
      {/* HERO */}
      <section className="relative border-b border-idbi-line">
        <div aria-hidden className="absolute inset-0 bg-gradient-to-b from-idbi-mintSoft to-idbi-bg" />
        <div className="relative max-w-[820px] mx-auto px-5 sm:px-7 pt-14 sm:pt-20 pb-16 text-center">
          <FadeIn>
            <div className="flex justify-center mb-6">
              <ShreyaAvatar size="lg" className="text-idbi-green" />
            </div>
            <span className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-idbi-light text-idbi-green text-xs font-bold mb-5">
              <ShieldCheck size={14} />
              {t('badge')}
            </span>
            <h1 className="text-3xl font-extrabold tracking-tight text-idbi-ink text-balance">
              {t('headline')}
            </h1>
            <p className="mt-4 text-lg text-idbi-muted max-w-xl mx-auto text-pretty">
              {t('subheadline')}
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link href={`/${locale}/advisor`} className={buttonVariants({ size: 'lg' })}>
                {t('cta_primary')}
                <ArrowRight size={18} />
              </Link>
              <Link
                href={`/${locale}/onboarding`}
                className={buttonVariants({ variant: 'secondary', size: 'lg' })}
              >
                {t('cta_secondary')}
              </Link>
            </div>

            {/* Language is the product's headline capability — surface it in the hero */}
            <div className="mt-9 inline-flex items-center gap-3 rounded-field bg-gradient-to-r from-idbi-green to-idbi-deep px-4 py-3 shadow-glow">
              <span className="flex items-center gap-2 text-sm font-semibold text-white/90">
                <Globe size={16} />
                {tNav('language_switcher_label')}
              </span>
              <LanguageSwitcher />
            </div>
          </FadeIn>
        </div>
      </section>

      {/* TRUST STRIP */}
      <section className="max-w-[1200px] mx-auto px-5 sm:px-7 py-7">
        <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 text-sm font-semibold text-idbi-slate">
          {trust.map(({ Icon, label }) => (
            <span key={label} className="inline-flex items-center gap-2">
              <Icon size={15} className="text-idbi-green" strokeWidth={2.2} />
              {label}
            </span>
          ))}
        </div>
      </section>

      {/* FEATURE TRIPTYCH */}
      <section className="max-w-[1200px] mx-auto px-5 sm:px-7 pb-4">
        <div className="grid gap-5 md:grid-cols-3">
          {features.map(({ Icon, title, desc }, i) => (
            <FadeIn key={title} delay={i * 0.08}>
              <div className="h-full bg-white rounded-card border border-idbi-line p-6 shadow-card">
                <span className="w-11 h-11 rounded-field bg-idbi-light flex items-center justify-center mb-4">
                  <Icon size={20} className="text-idbi-green" strokeWidth={2.1} />
                </span>
                <h3 className="text-lg font-bold text-idbi-ink mb-1.5">{title}</h3>
                <p className="text-sm text-idbi-muted leading-relaxed">{desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="max-w-[1000px] mx-auto px-5 sm:px-7 py-12">
        <h2 className="text-xl font-extrabold tracking-tight text-idbi-ink text-center mb-8">
          {t('how_title')}
        </h2>
        <div className="grid gap-5 sm:grid-cols-3">
          {steps.map(({ title, desc }, i) => (
            <FadeIn key={title} delay={i * 0.08}>
              <div className="h-full bg-idbi-surface rounded-card border border-idbi-line p-6">
                <span className="w-9 h-9 rounded-full bg-idbi-green text-white font-extrabold text-base flex items-center justify-center mb-4 tabular-nums">
                  {i + 1}
                </span>
                <h3 className="text-base font-bold text-idbi-ink mb-1.5">{title}</h3>
                <p className="text-sm text-idbi-muted leading-relaxed">{desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-idbi-line">
        <div className="max-w-[1200px] mx-auto px-5 sm:px-7 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-idbi-faint max-w-xl text-center sm:text-left">{t('footer_note')}</p>
          <Link
            href={`/${locale}/demo?demo=true`}
            className={cn(
              'shrink-0 inline-flex items-center gap-1.5 text-sm font-bold text-idbi-green hover:text-idbi-dark transition-colors rounded-field',
              FOCUS_RING,
            )}
          >
            {tNav('judge_demo')}
            <ArrowRight size={14} />
          </Link>
        </div>
      </footer>
    </div>
  );
}
