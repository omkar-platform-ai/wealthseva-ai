'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { ChevronDown, Info, Palmtree, Home, GraduationCap, Gem, Target, LucideIcon } from 'lucide-react';
import { formatINR } from '@/lib/format';
import FadeIn from '@/components/FadeIn';
import { cn, FOCUS_RING } from '@/lib/utils';

interface Preset {
  id: string;
  label_key: string;
  target_amount: number;
  years: number;
  icon: string;
}
interface Projection {
  name: string;
  target_amount: number;
  monthly_sip: number;
  projected_corpus: number;
  yearly_data: { year: number; corpus: number }[];
  trace?: {
    target_amount: number;
    current_savings: number;
    months: number;
    annual_return_pct: number;
    fv_savings: number;
    gap: number;
    monthly_sip: number;
  } | null;
}
interface GoalResult {
  projections: Projection[];
  summary: string;
  total_monthly_required: number;
}

const PRESET_KEY_MAP: Record<string, 'preset_retirement' | 'preset_house' | 'preset_education' | 'preset_wedding'> = {
  retirement: 'preset_retirement',
  house: 'preset_house',
  education: 'preset_education',
  wedding: 'preset_wedding',
};

const PRESET_ICONS: Record<string, LucideIcon> = {
  retirement: Palmtree,
  house: Home,
  education: GraduationCap,
  wedding: Gem,
};

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const inputCls = cn(
  'w-full border-2 border-idbi-line rounded-field px-3.5 py-3 text-sm bg-idbi-surface text-idbi-ink transition-colors focus-visible:border-idbi-green focus-visible:bg-white',
  FOCUS_RING,
);
const labelCls = 'block text-sm font-semibold text-idbi-muted mb-1.5';

export default function GoalPlanner() {
  const t = useTranslations('goals');
  const tCommon = useTranslations('common');
  const locale = useLocale();

  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', target_amount: '', years: '', current_savings: '' });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<GoalResult | null>(null);
  const [error, setError] = useState('');
  const [openTrace, setOpenTrace] = useState<number | null>(null);

  // ---- Backend wiring: GET /api/goals/presets ----
  useEffect(() => {
    fetch(`${BACKEND}/api/goals/presets`)
      .then(r => r.json())
      .then(data => setPresets(data.presets ?? []))
      .catch(() => {});
  }, []);

  const selectPreset = (preset: Preset) => {
    setSelectedPreset(preset.id);
    const labelKey = PRESET_KEY_MAP[preset.id];
    setForm(f => ({
      ...f,
      name: labelKey ? t(labelKey) : preset.id,
      target_amount: String(preset.target_amount),
      years: String(preset.years),
    }));
  };

  // ---- Backend wiring: POST /api/goals ----
  const handleSubmit = async () => {
    const years = parseInt(form.years);
    if (!form.name || !form.target_amount || !years) return;

    const targetDate = new Date();
    targetDate.setFullYear(targetDate.getFullYear() + years);
    const target_date = targetDate.toISOString().split('T')[0];

    setSubmitting(true);
    setError('');
    setResult(null);
    setOpenTrace(null);

    try {
      const res = await fetch(`${BACKEND}/api/goals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goals: [{
            name: form.name,
            target_amount: parseFloat(form.target_amount),
            target_date,
            current_savings: parseFloat(form.current_savings || '0'),
            monthly_contribution: 0,
          }],
          language: locale,
        }),
      });
      if (!res.ok) throw new Error('failed');
      const data = await res.json();
      setResult(data);
    } catch {
      setError(tCommon('error_generic'));
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = !submitting && !!form.name && !!form.target_amount && !!form.years;

  return (
    <div className="space-y-5">
      {/* Preset cards */}
      {presets.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
          {presets.map(preset => {
            const Icon = PRESET_ICONS[preset.id] ?? Target;
            const active = selectedPreset === preset.id;
            return (
              <button
                key={preset.id}
                onClick={() => selectPreset(preset)}
                className={cn(
                  'text-left rounded-card p-4 border-2 transition-all',
                  FOCUS_RING,
                  active
                    ? 'border-idbi-green bg-idbi-mintSoft shadow-card'
                    : 'border-idbi-line bg-white hover:border-idbi-green/50',
                )}
              >
                <div className="w-[38px] h-[38px] rounded-tile bg-idbi-light flex items-center justify-center mb-3">
                  <Icon size={19} className="text-idbi-green" />
                </div>
                <div className="font-bold text-sm text-idbi-ink">
                  {PRESET_KEY_MAP[preset.id] ? t(PRESET_KEY_MAP[preset.id]) : preset.id}
                </div>
                <div className="text-sm text-idbi-green font-bold mt-0.5">
                  {formatINR(preset.target_amount, locale)}
                </div>
                <div className="text-xs text-idbi-faint font-medium">
                  {preset.years} {t('years_away')}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* Form */}
      <div className="bg-white rounded-card border border-idbi-line shadow-card p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>{t('goal_name_label')}</label>
            <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className={inputCls} placeholder={t('preset_retirement')} />
          </div>
          <div>
            <label className={labelCls}>{t('target_amount')}</label>
            <input type="number" value={form.target_amount} onChange={e => setForm(f => ({ ...f, target_amount: e.target.value }))} className={inputCls} placeholder="1000000" min="1" />
          </div>
          <div>
            <label className={labelCls}>{t('target_horizon')}</label>
            <input type="number" value={form.years} onChange={e => setForm(f => ({ ...f, years: e.target.value }))} className={inputCls} placeholder={t('years_placeholder')} min="1" max="40" />
          </div>
          <div>
            <label className={labelCls}>{t('current_savings')}</label>
            <input type="number" value={form.current_savings} onChange={e => setForm(f => ({ ...f, current_savings: e.target.value }))} className={inputCls} placeholder="0" min="0" />
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={cn(
            'w-full rounded-field py-3.5 font-bold text-base text-white transition-all',
            FOCUS_RING,
            canSubmit
              ? 'bg-gradient-to-r from-idbi-green to-idbi-dark shadow-glow hover:brightness-95'
              : 'bg-idbi-mintDim cursor-not-allowed',
          )}
        >
          {submitting ? tCommon('loading') : t('calculate_button')}
        </button>

        {error && <p className="text-sm text-red-500 text-center">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <FadeIn className="space-y-4">
          {(result.projections ?? []).map((proj, i) => (
            <div key={i} className="bg-white rounded-card border border-idbi-line shadow-card p-6">
              <h3 className="font-extrabold text-idbi-ink text-lg mb-4">{proj.name}</h3>

              <div className="grid grid-cols-2 gap-3.5 mb-6">
                <div className="bg-idbi-light rounded-card p-[18px]">
                  <div className="text-xs font-semibold text-idbi-muted mb-1.5">{t('monthly_sip_label')}</div>
                  <div className="text-xl font-extrabold text-idbi-green tracking-tight tabular-nums">
                    {formatINR(proj.monthly_sip, locale)}
                  </div>
                </div>
                <div className="bg-idbi-warm rounded-card p-[18px]">
                  <div className="text-xs font-semibold text-idbi-muted mb-1.5">{t('projected_value_label')}</div>
                  <div className="text-xl font-extrabold text-idbi-orange tracking-tight tabular-nums">
                    {formatINR(proj.projected_corpus, locale)}
                  </div>
                </div>
              </div>

              {proj.yearly_data.length > 0 && (
                <div>
                  <div className="text-sm font-bold text-idbi-slate mb-3">{t('corpus_chart_label')}</div>
                  <div className="bg-idbi-surfaceAlt border border-idbi-line rounded-card p-3">
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={proj.yearly_data} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="corpusGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#00836C" stopOpacity={0.18} />
                            <stop offset="100%" stopColor="#00836C" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#EEF3F1" vertical={false} />
                        <XAxis dataKey="year" tick={{ fill: '#9AAAA5', fontSize: 11 }} stroke="#E1EAE7" />
                        <YAxis tick={{ fill: '#9AAAA5', fontSize: 10 }} stroke="#E1EAE7" width={72} tickFormatter={(v: number) => formatINR(v, locale)} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#122622', border: 'none', borderRadius: '10px', color: '#fff', fontSize: '12px' }}
                          formatter={(v: number) => [formatINR(v, locale), t('projected_value_label')]}
                          labelFormatter={(l: number) => t('chart_year_label', { year: l })}
                        />
                        <Area type="monotone" dataKey="corpus" stroke="#00836C" strokeWidth={2.6} fill="url(#corpusGrad)" dot={false} activeDot={{ r: 4 }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {proj.trace && (
                <div className="mt-4 border-t border-idbi-line pt-4">
                  <button
                    onClick={() => setOpenTrace(openTrace === i ? null : i)}
                    aria-expanded={openTrace === i}
                    className={cn('w-full flex items-center gap-2 text-sm font-bold text-idbi-green', FOCUS_RING)}
                  >
                    <Info size={16} />
                    {t('why_button')}
                    <ChevronDown size={16} className={`ml-auto transition-transform ${openTrace === i ? 'rotate-180' : ''}`} />
                  </button>
                  {openTrace === i && (
                    <div className="mt-4 space-y-3 text-sm text-idbi-slate">
                      <div className="flex gap-3">
                        <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">{t('why_step_data')}</span>
                        <p>{t('why_data_text', { target: formatINR(proj.trace.target_amount, locale), months: proj.trace.months, savings: formatINR(proj.trace.current_savings, locale) })}</p>
                      </div>
                      <div className="flex gap-3">
                        <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">{t('why_step_assumption')}</span>
                        <p>{t('why_assumption_text', { rate: proj.trace.annual_return_pct })}</p>
                      </div>
                      <div className="flex gap-3">
                        <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">{t('why_step_calc')}</span>
                        <p>{t('why_calc_text', { fv: formatINR(proj.trace.fv_savings, locale), gap: formatINR(proj.trace.gap, locale), sip: formatINR(proj.trace.monthly_sip, locale) })}</p>
                      </div>
                      <p className="text-xs text-idbi-faint border-t border-idbi-line pt-3">{t('why_note')}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Total + advice */}
          <div className="bg-white rounded-card border border-idbi-line shadow-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-idbi-muted font-medium">{t('total_monthly_label')}</span>
              <span className="text-2xl font-extrabold text-idbi-green tracking-tight tabular-nums">
                {formatINR(result.total_monthly_required, locale)}
              </span>
            </div>
            {result.summary && (
              <div className="border-t border-idbi-line pt-4 flex gap-3">
                <div className="w-8 h-8 shrink-0 rounded-tile bg-idbi-orange flex items-center justify-center">
                  <Info size={16} className="text-white" />
                </div>
                <div>
                  <div className="text-sm font-bold text-idbi-orange mb-1">{t('advice_label')}</div>
                  <p className="text-sm text-idbi-slate leading-relaxed">{result.summary}</p>
                </div>
              </div>
            )}
          </div>
        </FadeIn>
      )}
    </div>
  );
}
