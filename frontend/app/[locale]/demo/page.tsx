'use client';
import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useTranslations } from 'next-intl';

// Keep identical to _DEMO_SIP_HINDI in backend/routers/chat.py.
// Compliance: fund *category*, never a specific fund name.
// Intentionally stays in Hindi in every locale — this step demos the Hindi SIP punchline.
const HINDI_SIP =
  'रमेश जी, ₹5,000 प्रति माह के SIP से 10 साल में लगभग ₹11.6 लाख बनेंगे। ' +
  'मैं आपको flexi-cap श्रेणी के diversified equity fund में SIP शुरू करने की सलाह दूंगी — यह moderate risk profile के लिए उपयुक्त है। ' +
  'क्या आप अपने retirement goal के बारे में भी जानना चाहेंगे?';

// Ramesh's holdings — keep consistent with MOCK_PORTFOLIO in backend/routers/idbi.py.
// Fund names stay literal (real products); the category label is localised for display.
const PORTFOLIO = [
  { name: 'HDFC Flexi Cap Fund', category: 'Equity', value: 114240, gain: 12.4 },
  { name: 'SBI Blue Chip Fund', category: 'Equity', value: 61880, gain: 8.2 },
  { name: 'HDFC Short Term Debt', category: 'Debt', value: 84200, gain: 4.1 },
  { name: 'SBI Gold ETF', category: 'Gold', value: 9300, gain: 6.3 },
  { name: 'ICICI Pru Liquid Fund', category: 'Liquid', value: 240000, gain: 6.9 },
];

const TOTAL_PORTFOLIO = PORTFOLIO.reduce((s, h) => s + h.value, 0);

function formatINR(n: number) {
  return `₹${n.toLocaleString('en-IN')}`;
}

// ── Step progress bar ──────────────────────────────────────────────────────────

function StepProgress({ step }: { step: number }) {
  const t = useTranslations('demo');
  const stepLabels = t.raw('step_labels') as string[];
  return (
    <div className="mb-8">
      <div className="flex justify-between text-sm mb-2">
        <span className="font-semibold text-idbi-green">{t('step_counter', { step })}</span>
        <span className="text-gray-500">{t('percent_complete', { percent: Math.round((step / 5) * 100) })}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
        <div
          className="bg-idbi-green h-2 rounded-full transition-all duration-700"
          style={{ width: `${(step / 5) * 100}%` }}
        />
      </div>
      <div className="hidden sm:flex justify-between">
        {stepLabels.map((label, i) => (
          <span
            key={i}
            className={`text-xs transition-colors ${i + 1 <= step ? 'text-idbi-green font-semibold' : 'text-gray-400'}`}
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Step 1: Meet Ramesh ────────────────────────────────────────────────────────

function Step1Intro({ onStart }: { onStart: () => void }) {
  const t = useTranslations('demo');
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
      <div className="w-24 h-24 bg-gradient-to-br from-idbi-green to-idbi-teal rounded-full flex items-center justify-center mx-auto mb-6 text-5xl shadow-lg">
        👨‍💼
      </div>
      <h2 className="text-3xl font-bold text-idbi-green mb-1">{t('s1_title')}</h2>
      <p className="text-gray-500 mb-6">{t('s1_subtitle')}</p>
      <div className="bg-idbi-light rounded-xl p-5 text-left text-sm text-gray-700 mb-6 space-y-2 max-w-sm mx-auto">
        <p>💼 {t('s1_income_label')}: <strong>{t('s1_income_value')}</strong></p>
        <p>💰 {t('s1_invest_label')}: <strong>{t('s1_invest_value')}</strong> {t('s1_invest_note')}</p>
        <p>🎯 {t('s1_goal_label')}: {t('s1_goal_pre')} <strong>{t('s1_goal_value')}</strong></p>
        <p>📊 {t('s1_risk_label')}: <strong>{t('s1_risk_value')}</strong></p>
        <p>🗣️ {t('s1_lang_label')}: <strong>{t('s1_lang_value')}</strong></p>
      </div>
      <p className="text-gray-500 text-sm mb-8 max-w-md mx-auto">
        {t('s1_watch')}
      </p>
      <button
        onClick={onStart}
        className="bg-idbi-green text-white px-10 py-4 rounded-xl font-bold text-lg hover:bg-idbi-dark transition-colors shadow-md"
      >
        {t('s1_start')} →
      </button>
    </div>
  );
}

// ── Step 2: Risk Quiz ──────────────────────────────────────────────────────────

function Step2RiskQuiz({ onComplete }: { onComplete: () => void }) {
  const t = useTranslations('demo');
  const quiz = t.raw('s2_quiz') as { q: string; opts: string[] }[];
  const [qIdx, setQIdx] = useState(0);
  const [highlighted, setHighlighted] = useState<number | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (done) return;
    const t1 = setTimeout(() => setHighlighted(1), 1500);
    const t2 = setTimeout(() => {
      if (qIdx < quiz.length - 1) {
        setQIdx(q => q + 1);
        setHighlighted(null);
      } else {
        setDone(true);
      }
    }, 4000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [qIdx, done, quiz.length]);

  if (done) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="text-6xl mb-4">✅</div>
        <h2 className="text-2xl font-bold text-idbi-green mb-2">{t('s2_result_title')}</h2>
        <p className="text-gray-600 mb-6">{t('s2_result_desc')}</p>
        <div className="flex gap-3 justify-center flex-wrap mb-8">
          {[
            [t('s2_alloc_equity'), '60%', 'bg-emerald-100 text-emerald-800'],
            [t('s2_alloc_debt'), '30%', 'bg-blue-100 text-blue-800'],
            [t('s2_alloc_gold'), '10%', 'bg-amber-100 text-amber-800'],
          ].map(([cat, pct, cls]) => (
            <div key={cat} className={`px-5 py-2 rounded-full text-sm font-semibold ${cls}`}>
              {cat}: {pct}
            </div>
          ))}
        </div>
        <button
          onClick={onComplete}
          className="bg-idbi-green text-white px-8 py-3 rounded-xl font-bold text-base hover:bg-idbi-dark transition-colors shadow-md"
        >
          {t('next_step')} →
        </button>
      </div>
    );
  }

  const q = quiz[qIdx];
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-idbi-green">{t('s2_title')}</h2>
        <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">{t('s2_counter', { n: qIdx + 1 })}</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-1.5 mb-6">
        <div
          className="bg-idbi-orange h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${((qIdx + 1) / 5) * 100}%` }}
        />
      </div>
      <p className="text-lg font-medium text-gray-800 mb-6">{q.q}</p>
      <div className="space-y-3">
        {q.opts.map((opt, i) => {
          const isSelected = highlighted === i;
          return (
            <div
              key={i}
              className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                isSelected
                  ? 'border-idbi-green bg-idbi-light font-semibold text-idbi-green'
                  : 'border-gray-200 text-gray-600'
              }`}
            >
              <span className="font-bold mr-2">{['A', 'B', 'C', 'D'][i]}.</span>
              {opt}
              {isSelected && <span className="ml-2">✓</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Step 3: Portfolio ──────────────────────────────────────────────────────────

function Step3Portfolio({ onComplete }: { onComplete: () => void }) {
  const t = useTranslations('demo');
  const [uploading, setUploading] = useState(true);

  // Category value stays literal (drives styling); label is localised for display.
  const catLabel = (c: string) => t(`s3_cat_${c.toLowerCase()}` as 's3_cat_equity');

  useEffect(() => {
    const t1 = setTimeout(() => setUploading(false), 1200);
    return () => clearTimeout(t1);
  }, []);

  if (uploading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="text-4xl mb-4 animate-bounce">📂</div>
        <h2 className="text-xl font-bold text-idbi-green mb-2">{t('s3_uploading')}</h2>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
          <div className="bg-idbi-orange h-2 rounded-full animate-pulse w-3/4" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-idbi-green">{t('s3_title')}</h2>
        <span className="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">✓ {t('s3_loaded_badge')}</span>
      </div>
      <div className="bg-idbi-light rounded-xl p-4 mb-4 flex justify-between items-center">
        <span className="text-gray-600 text-sm">{t('s3_total_label')}</span>
        <span className="text-2xl font-bold text-idbi-green">{formatINR(TOTAL_PORTFOLIO)}</span>
      </div>
      <div className="space-y-3">
        {PORTFOLIO.map((h, i) => (
          <div key={i} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
            <div>
              <p className="font-medium text-gray-800 text-sm">{h.name}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full mt-0.5 inline-block ${
                h.category === 'Equity' ? 'bg-emerald-100 text-emerald-700'
                : h.category === 'Debt' ? 'bg-blue-100 text-blue-700'
                : h.category === 'Liquid' ? 'bg-sky-100 text-sky-700'
                : 'bg-amber-100 text-amber-700'
              }`}>{catLabel(h.category)}</span>
            </div>
            <div className="text-right">
              <p className="font-semibold text-gray-800 text-sm">{formatINR(h.value)}</p>
              <p className="text-xs text-green-600 font-medium">+{h.gain}%</p>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 text-center">
        <button
          onClick={onComplete}
          className="bg-idbi-green text-white px-8 py-3 rounded-xl font-bold text-base hover:bg-idbi-dark transition-colors shadow-md"
        >
          {t('next_step')} →
        </button>
      </div>
    </div>
  );
}

// ── Step 4: Goal Plan ──────────────────────────────────────────────────────────

function Step4Goals({ onComplete }: { onComplete: () => void }) {
  const t = useTranslations('demo');
  const fundSplit = t.raw('s4_fund_split') as string[];
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-idbi-green">{t('s4_title')}</h2>
        <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full">{t('s4_prefilled_badge')}</span>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-6">
        {[
          [t('s4_goalname_label'), t('s4_goalname_value')],
          [t('s4_target_label'), t('s4_target_value')],
          [t('s4_horizon_label'), t('s4_horizon_value')],
          [t('s4_earmarked_label'), t('s4_earmarked_value')],
        ].map(([label, value]) => (
          <div key={label} className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className="font-bold text-gray-800">{value}</p>
          </div>
        ))}
      </div>
      <div className="bg-idbi-light rounded-xl p-5">
        <p className="text-sm text-gray-600 mb-2">{t('s4_sip_label')}</p>
        <p className="text-3xl font-bold text-idbi-green mb-1">{t('s4_sip_value')}</p>
        <p className="text-xs text-gray-500 mb-3">{t('s4_sip_note')}</p>
        {/* Compliance: fund categories only, never specific fund names */}
        <div className="bg-white rounded-lg p-3 text-xs text-gray-700 space-y-1">
          {fundSplit.map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
      </div>
      <div className="mt-6 text-center">
        <button
          onClick={onComplete}
          className="bg-idbi-green text-white px-8 py-3 rounded-xl font-bold text-base hover:bg-idbi-dark transition-colors shadow-md"
        >
          {t('next_step')} →
        </button>
      </div>
    </div>
  );
}

// ── Step 5: Hindi SIP Streaming ────────────────────────────────────────────────

function Step5HindiSIP() {
  const t = useTranslations('demo');
  const words = HINDI_SIP.split(' ');
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count >= words.length) return;
    const timer = setTimeout(() => setCount(c => c + 1), 160);
    return () => clearTimeout(timer);
  }, [count, words.length]);

  const done = count >= words.length;
  const displayed = words.slice(0, count).join(' ');

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-idbi-green to-idbi-teal rounded-full flex items-center justify-center text-2xl shadow flex-shrink-0">
          🤖
        </div>
        <div>
          <h2 className="text-xl font-bold text-idbi-green">WealthSeva AI</h2>
          {/* Intentional bilingual badge — this step showcases Hindi mode. */}
          <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
            हिंदी मोड · Hindi Mode
          </span>
        </div>
      </div>

      <div className="bg-gradient-to-br from-idbi-light to-teal-50 rounded-xl p-6 min-h-[120px] mb-4">
        <p className="text-gray-800 leading-relaxed text-base font-medium">
          {displayed}
          {!done && (
            <span className="inline-block w-0.5 h-5 bg-idbi-green ml-0.5 align-middle animate-pulse" />
          )}
        </p>
      </div>

      {done && (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
            <strong>⚠️ {t('s5_disclosure_label')}</strong> {t('s5_disclosure_text')}
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
            <div className="text-4xl mb-2">🎉</div>
            <p className="text-green-700 font-bold text-lg">{t('s5_complete_title')}</p>
            <p className="text-gray-500 text-sm mt-1">
              {t('s5_complete_desc')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────────

function DemoInner() {
  const t = useTranslations('demo');
  const searchParams = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';
  const [step, setStep] = useState(1);
  const advance = useCallback(() => setStep(s => s + 1), []);

  if (!isDemo) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <p className="text-gray-400 text-lg">
          {t.rich('not_demo_prompt', {
            code: (chunks) => <code className="bg-gray-100 px-2 py-0.5 rounded">{chunks}</code>,
          })}
        </p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-6 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm font-medium text-center">
        🎬 {t('banner')}
      </div>
      <StepProgress step={step} />
      {step === 1 && <Step1Intro onStart={advance} />}
      {step === 2 && <Step2RiskQuiz onComplete={advance} />}
      {step === 3 && <Step3Portfolio onComplete={advance} />}
      {step === 4 && <Step4Goals onComplete={advance} />}
      {step === 5 && <Step5HindiSIP />}
    </div>
  );
}

export default function DemoPage() {
  return (
    <Suspense>
      <DemoInner />
    </Suspense>
  );
}
