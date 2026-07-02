'use client';
import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

const HINDI_SIP =
  'रमेश जी, ₹5,000 प्रति माह के SIP से 10 साल में लगभग ₹11.6 लाख बनेंगे। ' +
  'मैं आपको HDFC Flexi Cap Fund में SIP शुरू करने की सलाह दूंगी — यह moderate risk profile के लिए उपयुक्त है। ' +
  'क्या आप अपने retirement goal के बारे में भी जानना चाहेंगे?';

const QUIZ = [
  {
    q: 'What is your primary investment objective?',
    opts: ['Capital preservation & safety', 'Balanced growth with income', 'High growth potential', 'Maximum returns at any risk'],
  },
  {
    q: 'How long can you keep your money invested without needing it?',
    opts: ['Less than 1 year', '3–7 years', '7–15 years', 'More than 15 years'],
  },
  {
    q: 'If your portfolio dropped 20%, what would you do?',
    opts: ['Sell everything immediately', 'Hold and wait for recovery', 'Buy more at lower prices', 'Double down aggressively'],
  },
  {
    q: 'What is your approximate annual household income?',
    opts: ['Below ₹5 lakh', '₹5L – ₹15L', '₹15L – ₹30L', 'Above ₹30 lakh'],
  },
  {
    q: 'How comfortable are you with short-term market volatility?',
    opts: ['Not comfortable at all', 'Somewhat comfortable', 'Comfortable with ups & downs', 'Very comfortable — I embrace it'],
  },
];

const PORTFOLIO = [
  { name: 'HDFC Flexi Cap Fund', category: 'Equity', value: 114240, gain: 12.4 },
  { name: 'SBI Bluechip Fund', category: 'Equity', value: 61880, gain: 8.2 },
  { name: 'HDFC Short Term Debt', category: 'Debt', value: 84200, gain: 4.1 },
  { name: 'SBI Gold ETF', category: 'Gold', value: 9300, gain: 6.3 },
];

const TOTAL_PORTFOLIO = PORTFOLIO.reduce((s, h) => s + h.value, 0);
const STEP_LABELS = ['Meet Ramesh', 'Risk Quiz', 'Portfolio', 'Goal Plan', 'Hindi SIP'];

function formatINR(n: number) {
  return `₹${n.toLocaleString('en-IN')}`;
}

// ── Step progress bar ──────────────────────────────────────────────────────────

function StepProgress({ step }: { step: number }) {
  return (
    <div className="mb-8">
      <div className="flex justify-between text-sm mb-2">
        <span className="font-semibold text-idbi-blue">Step {step} of 5</span>
        <span className="text-gray-500">{Math.round((step / 5) * 100)}% complete</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
        <div
          className="bg-idbi-blue h-2 rounded-full transition-all duration-700"
          style={{ width: `${(step / 5) * 100}%` }}
        />
      </div>
      <div className="hidden sm:flex justify-between">
        {STEP_LABELS.map((label, i) => (
          <span
            key={i}
            className={`text-xs transition-colors ${i + 1 <= step ? 'text-idbi-blue font-semibold' : 'text-gray-400'}`}
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
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
      <div className="w-24 h-24 bg-gradient-to-br from-idbi-blue to-blue-400 rounded-full flex items-center justify-center mx-auto mb-6 text-5xl shadow-lg">
        👨‍💼
      </div>
      <h2 className="text-3xl font-bold text-idbi-blue mb-1">Meet Ramesh</h2>
      <p className="text-gray-500 mb-6">Age 42 · Mumbai · Salaried Professional</p>
      <div className="bg-idbi-light rounded-xl p-5 text-left text-sm text-gray-700 mb-6 space-y-2 max-w-sm mx-auto">
        <p>💼 Monthly income: <strong>₹80,000</strong></p>
        <p>💰 Current savings: <strong>₹2,50,000</strong></p>
        <p>🎯 Goal: Retire at 62 with <strong>₹50L corpus</strong></p>
        <p>📊 Risk preference: <strong>Moderate</strong></p>
        <p>🗣️ Preferred language: <strong>Hindi</strong></p>
      </div>
      <p className="text-gray-500 text-sm mb-8 max-w-md mx-auto">
        Watch WealthSeva AI guide Ramesh through a complete financial plan — from risk profiling to personalized SIP advice in Hindi.
      </p>
      <button
        onClick={onStart}
        className="bg-idbi-blue text-white px-10 py-4 rounded-xl font-bold text-lg hover:bg-blue-900 transition-colors shadow-md"
      >
        Start Demo →
      </button>
    </div>
  );
}

// ── Step 2: Risk Quiz ──────────────────────────────────────────────────────────

function Step2RiskQuiz({ onComplete }: { onComplete: () => void }) {
  const [qIdx, setQIdx] = useState(0);
  const [highlighted, setHighlighted] = useState<number | null>(null);
  const [done, setDone] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    if (done) return;
    const t1 = setTimeout(() => setHighlighted(1), 700);
    const t2 = setTimeout(() => {
      if (qIdx < QUIZ.length - 1) {
        setQIdx(q => q + 1);
        setHighlighted(null);
      } else {
        setDone(true);
      }
    }, 1900);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [qIdx, done]);

  useEffect(() => {
    if (!done) return;
    const t = setTimeout(() => onCompleteRef.current(), 2500);
    return () => clearTimeout(t);
  }, [done]);

  if (done) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="text-6xl mb-4">✅</div>
        <h2 className="text-2xl font-bold text-idbi-blue mb-2">Risk Profile: Moderate</h2>
        <p className="text-gray-600 mb-6">Ramesh has a balanced, growth-oriented investment approach.</p>
        <div className="flex gap-3 justify-center flex-wrap">
          {[
            ['Equity', '60%', 'bg-emerald-100 text-emerald-800'],
            ['Debt', '30%', 'bg-blue-100 text-blue-800'],
            ['Gold', '10%', 'bg-amber-100 text-amber-800'],
          ].map(([cat, pct, cls]) => (
            <div key={cat} className={`px-5 py-2 rounded-full text-sm font-semibold ${cls}`}>
              {cat}: {pct}
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-400 animate-pulse mt-6">Loading portfolio analysis…</p>
      </div>
    );
  }

  const q = QUIZ[qIdx];
  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-idbi-blue">Risk Profile Quiz</h2>
        <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">Q {qIdx + 1} / 5</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-1.5 mb-6">
        <div
          className="bg-idbi-gold h-1.5 rounded-full transition-all duration-500"
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
                  ? 'border-idbi-blue bg-idbi-light font-semibold text-idbi-blue'
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
  const [uploading, setUploading] = useState(true);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    const t1 = setTimeout(() => setUploading(false), 1200);
    const t2 = setTimeout(() => onCompleteRef.current(), 4000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);

  if (uploading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="text-4xl mb-4 animate-bounce">📂</div>
        <h2 className="text-xl font-bold text-idbi-blue mb-2">Uploading Sample Portfolio…</h2>
        <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
          <div className="bg-idbi-gold h-2 rounded-full animate-pulse w-3/4" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-idbi-blue">Portfolio Analysis</h2>
        <span className="bg-green-100 text-green-800 text-xs font-semibold px-3 py-1 rounded-full">✓ Sample Loaded</span>
      </div>
      <div className="bg-idbi-light rounded-xl p-4 mb-4 flex justify-between items-center">
        <span className="text-gray-600 text-sm">Total Portfolio Value</span>
        <span className="text-2xl font-bold text-idbi-blue">{formatINR(TOTAL_PORTFOLIO)}</span>
      </div>
      <div className="space-y-3">
        {PORTFOLIO.map((h, i) => (
          <div key={i} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
            <div>
              <p className="font-medium text-gray-800 text-sm">{h.name}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full mt-0.5 inline-block ${
                h.category === 'Equity' ? 'bg-emerald-100 text-emerald-700'
                : h.category === 'Debt' ? 'bg-blue-100 text-blue-700'
                : 'bg-amber-100 text-amber-700'
              }`}>{h.category}</span>
            </div>
            <div className="text-right">
              <p className="font-semibold text-gray-800 text-sm">{formatINR(h.value)}</p>
              <p className="text-xs text-green-600 font-medium">+{h.gain}%</p>
            </div>
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-400 text-center mt-4 animate-pulse">Advancing to Goal Planner…</p>
    </div>
  );
}

// ── Step 4: Goal Plan ──────────────────────────────────────────────────────────

function Step4Goals({ onComplete }: { onComplete: () => void }) {
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    const t = setTimeout(() => onCompleteRef.current(), 4000);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-idbi-blue">Retirement Goal Plan</h2>
        <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full">Pre-filled</span>
      </div>
      <div className="grid grid-cols-2 gap-4 mb-6">
        {[
          ['Goal Name', 'Retirement'],
          ['Target Corpus', '₹50,00,000'],
          ['Time Horizon', '20 Years'],
          ['Current Savings', '₹2,50,000'],
        ].map(([label, value]) => (
          <div key={label} className="bg-gray-50 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className="font-bold text-gray-800">{value}</p>
          </div>
        ))}
      </div>
      <div className="bg-idbi-light rounded-xl p-5">
        <p className="text-sm text-gray-600 mb-2">Recommended Monthly SIP</p>
        <p className="text-3xl font-bold text-idbi-blue mb-1">₹5,000 / month</p>
        <p className="text-xs text-gray-500 mb-3">At 12% p.a. CAGR → ₹49.9L in 20 years</p>
        <div className="bg-white rounded-lg p-3 text-xs text-gray-700 space-y-1">
          <p>🏦 HDFC Flexi Cap Fund — 60% (Equity core)</p>
          <p>📈 SBI Bluechip Fund — 20% (Large cap stability)</p>
          <p>🔒 HDFC Short Term Debt — 20% (Debt cushion)</p>
        </div>
      </div>
      <p className="text-xs text-gray-400 text-center mt-4 animate-pulse">Switching to Hindi for SIP advice…</p>
    </div>
  );
}

// ── Step 5: Hindi SIP Streaming ────────────────────────────────────────────────

function Step5HindiSIP() {
  const words = HINDI_SIP.split(' ');
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count >= words.length) return;
    const t = setTimeout(() => setCount(c => c + 1), 110);
    return () => clearTimeout(t);
  }, [count, words.length]);

  const done = count >= words.length;
  const displayed = words.slice(0, count).join(' ');

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 bg-gradient-to-br from-idbi-blue to-blue-400 rounded-full flex items-center justify-center text-2xl shadow flex-shrink-0">
          🤖
        </div>
        <div>
          <h2 className="text-xl font-bold text-idbi-blue">WealthSeva AI</h2>
          <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
            हिंदी मोड · Hindi Mode
          </span>
        </div>
      </div>

      <div className="bg-gradient-to-br from-idbi-light to-blue-50 rounded-xl p-6 min-h-[120px] mb-4">
        <p className="text-gray-800 leading-relaxed text-base font-medium">
          {displayed}
          {!done && (
            <span className="inline-block w-0.5 h-5 bg-idbi-blue ml-0.5 align-middle animate-pulse" />
          )}
        </p>
      </div>

      {done && (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
            <strong>⚠️ AI Disclosure:</strong> This response is AI-generated for educational and demonstration purposes only. Please consult a SEBI-registered investment advisor before making investment decisions.
          </div>
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
            <div className="text-4xl mb-2">🎉</div>
            <p className="text-green-700 font-bold text-lg">Demo Complete!</p>
            <p className="text-gray-500 text-sm mt-1">
              WealthSeva AI guided Ramesh through a full financial plan in under 2 minutes.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main ───────────────────────────────────────────────────────────────────────

function DemoInner() {
  const searchParams = useSearchParams();
  const isDemo = searchParams.get('demo') === 'true';
  const [step, setStep] = useState(1);
  const advance = useCallback(() => setStep(s => s + 1), []);

  if (!isDemo) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <p className="text-gray-400 text-lg">Visit this page with <code className="bg-gray-100 px-2 py-0.5 rounded">?demo=true</code> to start the demo.</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-6 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm font-medium text-center">
        🎬 Judge Demo Mode — Automated WealthSeva AI walkthrough
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
