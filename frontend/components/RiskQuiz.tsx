'use client';
import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { ChevronDown, Info, Sparkles, Check } from 'lucide-react';
import { cn, FOCUS_RING } from '@/lib/utils';
import { useToast } from '@/components/ui/Toast';

// Allocation legend colours (kept on-brand: green/teal/orange family)
const COLORS = ['#00836C', '#4FA9A7', '#F37021', '#F5C36B'];

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000';

interface QuizAnswer {
  question_id: number;
  answer: string;
}

interface RiskProfile {
  profile: string;
  score: number;
  explanation: string;
  recommended_allocation: { [key: string]: number };
  trace?: {
    answer_points: number[];
    score: number;
    max_score: number;
    bands: { [key: string]: number[] };
  };
}

const PROFILE_BADGE: Record<string, string> = {
  conservative: 'bg-idbi-risk-conservative-bg text-idbi-risk-conservative-text',
  moderate: 'bg-idbi-risk-moderate-bg text-idbi-risk-moderate-text',
  aggressive: 'bg-idbi-risk-aggressive-bg text-idbi-risk-aggressive-text',
};

// Backend returns English asset-class names as the allocation dict keys
// (see services/risk_service.py ALLOCATIONS). Map each to a translation key
// so the chart legend renders in the user's language, not always English.
const ALLOC_LABEL_KEY: Record<string, string> = {
  'Debt': 'alloc_debt',
  'Large Cap': 'alloc_large_cap',
  'Gold': 'alloc_gold',
  'Equity Diversified': 'alloc_equity_diversified',
  'Balanced': 'alloc_balanced',
  'Equity': 'alloc_equity',
  'Mid/Small Cap': 'alloc_mid_small_cap',
};

export default function RiskQuiz() {
  const t = useTranslations('risk');
  const locale = useLocale();
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState(1);
  const [answers, setAnswers] = useState<QuizAnswer[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<RiskProfile | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showWhy, setShowWhy] = useState(false);

  const questions = [
    { id: 1, key: 'question1' },
    { id: 2, key: 'question2' },
    { id: 3, key: 'question3' },
    { id: 4, key: 'question4' },
    { id: 5, key: 'question5' },
  ];

  const options = [
    { value: 'A', label: 'option_a' },
    { value: 'B', label: 'option_b' },
    { value: 'C', label: 'option_c' },
    { value: 'D', label: 'option_d' },
  ];

  const handleAnswer = async (answerValue: string) => {
    setSelected(answerValue);
    const newAnswers = [...answers, { question_id: currentStep, answer: answerValue }];

    // brief highlight before advancing
    setTimeout(async () => {
      setAnswers(newAnswers);
      if (currentStep < 5) {
        setIsTransitioning(true);
        setTimeout(() => {
          setCurrentStep(currentStep + 1);
          setSelected(null);
          setIsTransitioning(false);
        }, 200);
      } else {
        await submitQuiz(newAnswers);
      }
    }, 220);
  };

  // ---- Backend wiring: POST /api/risk-profile ----
  const submitQuiz = async (quizAnswers: QuizAnswer[]) => {
    setIsAnalyzing(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/risk-profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: quizAnswers, language: locale }),
      });
      if (!response.ok) throw new Error('Failed to submit quiz');
      const data = await response.json();
      setTimeout(() => {
        setResult(data);
        setIsAnalyzing(false);
      }, 1200);
    } catch {
      // Drop out of the analysing state and offer a retry, rather than
      // stranding the user on the last question with no feedback.
      setIsAnalyzing(false);
      toast({
        tone: 'error',
        message: t('submit_error'),
        action: { label: t('retry'), onClick: () => submitQuiz(quizAnswers) },
      });
    }
  };

  const retakeQuiz = () => {
    setCurrentStep(1);
    setAnswers([]);
    setSelected(null);
    setResult(null);
    setIsTransitioning(false);
    setShowWhy(false);
  };

  const getChartData = (allocation: { [key: string]: number }) =>
    Object.entries(allocation).map(([name, value]) => ({ name, value }));

  // ---------- Analysing state ----------
  if (isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[380px]">
        <div className="relative w-28 h-28 mb-6">
          <span className="absolute inset-0 rounded-full bg-idbi-green/40 animate-ping2" />
          <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center shadow-card">
            <div className="w-16 h-16 bg-idbi-green rounded-full flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
          </div>
        </div>
        <p className="text-base font-semibold text-idbi-muted animate-pulse">{t('analysing_label')}</p>
      </div>
    );
  }

  // ---------- Result state ----------
  if (result) {
    const chartData = getChartData(result.recommended_allocation);
    const profileKey = `result_${result.profile}`;

    return (
      <div className="space-y-5 animate-rise">
        <div className="text-center">
          <p className="text-xs font-semibold tracking-wide text-idbi-faint uppercase mb-2">
            {t('title')}
          </p>
          <div
            className={cn(
              'inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold capitalize',
              PROFILE_BADGE[result.profile] ?? PROFILE_BADGE.moderate,
            )}
          >
            {t(profileKey as 'result_conservative' | 'result_moderate' | 'result_aggressive')}
          </div>
        </div>

        <div className="bg-white rounded-card border border-idbi-line shadow-card p-6">
          <h3 className="text-base font-bold text-idbi-ink mb-4">{t('explanation_label')}</h3>
          <div className="grid md:grid-cols-2 gap-6 items-center">
            <div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={48}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              {/* HTML legend — always visible (inline SVG pie labels clipped
                  to invisibility on this small container) and localised. */}
              <div className="mt-3 space-y-1.5">
                {chartData.map((entry, index) => (
                  <div key={entry.name} className="flex items-center gap-2.5 text-sm">
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-idbi-slate flex-1">
                      {t((ALLOC_LABEL_KEY[entry.name] ?? 'alloc_debt') as 'alloc_debt')}
                    </span>
                    <span className="font-bold text-idbi-ink">{entry.value}%</span>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-sm leading-relaxed text-idbi-slate">{result.explanation}</p>
          </div>
        </div>

        {result.trace && (
          <div className="bg-white rounded-card border border-idbi-line shadow-card p-6">
            <button
              onClick={() => setShowWhy(!showWhy)}
              aria-expanded={showWhy}
              className={cn('w-full flex items-center gap-2 text-sm font-bold text-idbi-green', FOCUS_RING)}
            >
              <Info size={16} />
              {t('why_button')}
              <ChevronDown size={16} className={`ml-auto transition-transform ${showWhy ? 'rotate-180' : ''}`} />
            </button>
            {showWhy && (
              <div className="mt-4 space-y-3 text-sm text-idbi-slate">
                <div className="flex gap-3">
                  <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">
                    {t('why_step_data')}
                  </span>
                  <p>{t('why_data_text', { points: result.trace.answer_points.join(' + '), score: result.trace.score, max: result.trace.max_score })}</p>
                </div>
                <div className="flex gap-3">
                  <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">
                    {t('why_step_rule')}
                  </span>
                  <p>{t('why_rule_text', { conservative: t('result_conservative'), moderate: t('result_moderate'), aggressive: t('result_aggressive'), score: result.trace.score, profile: t(profileKey as 'result_conservative' | 'result_moderate' | 'result_aggressive') })}</p>
                </div>
                <div className="flex gap-3">
                  <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">
                    {t('why_step_result')}
                  </span>
                  <p>{t('why_result_text', { profile: t(profileKey as 'result_conservative' | 'result_moderate' | 'result_aggressive') })}</p>
                </div>
                <p className="text-xs text-idbi-faint border-t border-idbi-line pt-3">{t('why_note')}</p>
              </div>
            )}
          </div>
        )}

        <button
          onClick={retakeQuiz}
          className={cn('w-full py-3.5 rounded-field bg-idbi-green hover:bg-idbi-dark text-white font-bold transition-colors min-h-[54px]', FOCUS_RING)}
        >
          {t('retake_button')}
        </button>
      </div>
    );
  }

  // ---------- Question state ----------
  const currentQuestion = questions[currentStep - 1];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <span className="text-xs font-bold tracking-wide text-idbi-faint uppercase">{t('title')}</span>
        <span className="text-sm font-semibold text-idbi-muted">
          {t('step_label', { current: currentStep, total: 5 })}
        </span>
      </div>

      {/* Progress */}
      <div className="w-full bg-idbi-light rounded-full h-2">
        <div
          className="bg-gradient-to-r from-idbi-green to-idbi-teal h-2 rounded-full transition-all duration-300"
          style={{ width: `${(currentStep / 5) * 100}%` }}
        />
      </div>

      <div className={`transition-opacity duration-200 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`} key={currentStep}>
        <p className="text-lg font-semibold text-idbi-ink mb-6 text-balance">
          {t(currentQuestion.key as 'question1' | 'question2' | 'question3' | 'question4' | 'question5')}
        </p>

        <div className="space-y-3">
          {options.map((option) => {
            const isSel = selected === option.value;
            return (
              <button
                key={option.value}
                onClick={() => handleAnswer(option.value)}
                className={cn(
                  'group w-full text-left py-4 px-5 rounded-field border-2 font-medium transition-all duration-200 min-h-[56px] flex items-center gap-3',
                  FOCUS_RING,
                  isSel
                    ? 'border-idbi-green bg-idbi-light text-idbi-green'
                    : 'border-idbi-line bg-white hover:border-idbi-green/50 hover:bg-idbi-surface text-idbi-slate',
                )}
              >
                <span
                  className={cn(
                    'shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold transition-colors',
                    isSel ? 'bg-idbi-green text-white' : 'bg-idbi-light text-idbi-green group-hover:bg-idbi-green group-hover:text-white',
                  )}
                >
                  {isSel ? <Check size={15} /> : option.value}
                </span>
                {t(option.label as 'option_a' | 'option_b' | 'option_c' | 'option_d')}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
