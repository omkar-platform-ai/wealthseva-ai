'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChevronDown, Info, Palmtree, Home, GraduationCap, Gem, Target, LucideIcon } from 'lucide-react';
import { formatINR } from '@/lib/format';
import FadeIn from '@/components/FadeIn';

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

// Lucide icons replace the emoji the backend sends in preset.icon
const PRESET_ICONS: Record<string, LucideIcon> = {
  retirement: Palmtree,
  house: Home,
  education: GraduationCap,
  wedding: Gem,
};

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

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
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-idbi-green">{t('title')}</h2>

      {/* Preset Cards */}
      {presets.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {presets.map(preset => {
            const Icon = PRESET_ICONS[preset.id] ?? Target;
            return (
            <button
              key={preset.id}
              onClick={() => selectPreset(preset)}
              className={`rounded-xl p-4 text-left border-2 transition-all ${
                selectedPreset === preset.id
                  ? 'border-idbi-green bg-idbi-light'
                  : 'border-gray-200 bg-white hover:border-idbi-green/50'
              }`}
            >
              <div className="w-9 h-9 rounded-lg bg-idbi-green/10 flex items-center justify-center mb-2">
                <Icon size={18} className="text-idbi-green" />
              </div>
              <div className="font-semibold text-sm text-gray-800">
                {PRESET_KEY_MAP[preset.id] ? t(PRESET_KEY_MAP[preset.id]) : preset.id}
              </div>
              <div className="text-xs text-idbi-green font-medium mt-1">
                {formatINR(preset.target_amount, locale)}
              </div>
              <div className="text-xs text-gray-400">
                {preset.years} {t('years_away')}
              </div>
            </button>
            );
          })}
        </div>
      )}

      {/* Form */}
      <div className="bg-white rounded-2xl shadow p-6 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600 mb-1 block">{t('goal_name_label')}</label>
            <input
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-idbi-green/50"
              placeholder={t('preset_retirement')}
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">{t('target_amount')}</label>
            <input
              type="number"
              value={form.target_amount}
              onChange={e => setForm(f => ({ ...f, target_amount: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-idbi-green/50"
              placeholder="1000000"
              min="1"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">{t('target_date')}</label>
            <input
              type="number"
              value={form.years}
              onChange={e => setForm(f => ({ ...f, years: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-idbi-green/50"
              placeholder="Years to goal"
              min="1"
              max="40"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">{t('current_savings')}</label>
            <input
              type="number"
              value={form.current_savings}
              onChange={e => setForm(f => ({ ...f, current_savings: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-idbi-green/50"
              placeholder="0"
              min="0"
            />
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full bg-idbi-green text-white rounded-xl py-3 font-semibold hover:bg-idbi-green/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? tCommon('loading') : t('calculate_button')}
        </button>

        {error && <p className="text-sm text-red-500 text-center">{error}</p>}
      </div>

      {/* Results */}
      {result && (
        <FadeIn className="space-y-4">
          {(result.projections ?? []).map((proj, i) => (
            <div key={i} className="bg-white rounded-2xl shadow p-6">
              <h3 className="font-bold text-idbi-green text-lg mb-4">{proj.name}</h3>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-idbi-light rounded-xl p-4">
                  <div className="text-xs text-gray-500 mb-1">{t('monthly_sip_label')}</div>
                  <div className="text-xl font-bold text-idbi-green">
                    {formatINR(proj.monthly_sip, locale)}
                  </div>
                </div>
                <div className="bg-amber-50 rounded-xl p-4">
                  <div className="text-xs text-gray-500 mb-1">{t('projected_value_label')}</div>
                  <div className="text-xl font-bold text-idbi-orange">
                    {formatINR(proj.projected_corpus, locale)}
                  </div>
                </div>
              </div>

              {proj.yearly_data.length > 0 && (
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-3">
                    {t('corpus_chart_label')}
                  </div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={proj.yearly_data}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="year"
                        tick={{ fill: '#6B7280', fontSize: 11 }}
                        stroke="#9CA3AF"
                      />
                      <YAxis
                        tick={{ fill: '#6B7280', fontSize: 10 }}
                        stroke="#9CA3AF"
                        width={72}
                        tickFormatter={(v: number) => formatINR(v, locale)}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1F2937',
                          border: 'none',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '12px',
                        }}
                        formatter={(v: number) => [formatINR(v, locale), t('projected_value_label')]}
                        labelFormatter={(l: number) => `Year ${l}`}
                      />
                      <Line
                        type="monotone"
                        dataKey="corpus"
                        stroke="#00594C"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}

              {proj.trace && (
                <div className="mt-4 border-t pt-4">
                  <button
                    onClick={() => setOpenTrace(openTrace === i ? null : i)}
                    aria-expanded={openTrace === i}
                    className="w-full flex items-center gap-2 text-sm font-semibold text-idbi-green"
                  >
                    <Info size={16} />
                    {t('why_button')}
                    <ChevronDown
                      size={16}
                      className={`ml-auto transition-transform ${openTrace === i ? 'rotate-180' : ''}`}
                    />
                  </button>
                  {openTrace === i && (
                    <div className="mt-4 space-y-3 text-sm text-gray-700">
                      <div className="flex gap-3">
                        <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">
                          {t('why_step_data')}
                        </span>
                        <p>
                          {t('why_data_text', {
                            target: formatINR(proj.trace.target_amount, locale),
                            months: proj.trace.months,
                            savings: formatINR(proj.trace.current_savings, locale),
                          })}
                        </p>
                      </div>
                      <div className="flex gap-3">
                        <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">
                          {t('why_step_assumption')}
                        </span>
                        <p>{t('why_assumption_text', { rate: proj.trace.annual_return_pct })}</p>
                      </div>
                      <div className="flex gap-3">
                        <span className="shrink-0 h-fit px-2 py-0.5 rounded-full bg-idbi-light text-idbi-green text-xs font-semibold">
                          {t('why_step_calc')}
                        </span>
                        <p>
                          {t('why_calc_text', {
                            fv: formatINR(proj.trace.fv_savings, locale),
                            gap: formatINR(proj.trace.gap, locale),
                            sip: formatINR(proj.trace.monthly_sip, locale),
                          })}
                        </p>
                      </div>
                      <p className="text-xs text-gray-500 border-t pt-3">{t('why_note')}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Total + Shreya's Advice */}
          <div className="bg-white rounded-2xl shadow p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">{t('total_monthly_label')}</span>
              <span className="text-2xl font-bold text-idbi-green">
                {formatINR(result.total_monthly_required, locale)}
              </span>
            </div>

            {result.summary && (
              <div className="border-t pt-4">
                <div className="text-sm font-semibold text-idbi-orange mb-2">{t('advice_label')}</div>
                <p className="text-sm text-gray-700 leading-relaxed">{result.summary}</p>
              </div>
            )}
          </div>
        </FadeIn>
      )}
    </div>
  );
}
