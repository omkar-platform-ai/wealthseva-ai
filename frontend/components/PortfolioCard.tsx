'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useDropzone } from 'react-dropzone';
import { useState } from 'react';
import * as Papa from 'papaparse';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { UploadCloud, Zap, Check, FileText } from 'lucide-react';
import { cn, FOCUS_RING } from '@/lib/utils';

interface PortfolioData { Ticker: string; Category: string; Value: number; Units: number; }
interface AnalysisResult { summary: string; recommendations: string[]; sip_suggestion: string; }

// On-brand chart palette (green / teal / orange family).
const COLORS = ['#00836C', '#4FA9A7', '#F37021', '#F5C36B', '#307360'];

// Sample portfolio variants — value is the backend ?variant= key, labelKey the i18n key.
const SAMPLE_VARIANTS = [
  { variant: 'balanced', labelKey: 'sample_balanced' },
  { variant: 'conservative', labelKey: 'sample_conservative' },
  { variant: 'aggressive', labelKey: 'sample_aggressive' },
  { variant: 'idle_cash', labelKey: 'sample_idle_cash' },
  { variant: 'beginner', labelKey: 'sample_beginner' },
] as const;

export default function PortfolioCard() {
  const t = useTranslations('portfolio');
  const locale = useLocale();
  const [analyzing, setAnalyzing] = useState(false);
  const [sampleMenuOpen, setSampleMenuOpen] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [allocationData, setAllocationData] = useState<Array<{ category: string; value: number }>>([]);
  const [error, setError] = useState<string>('');

  const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2MB

  const parseCSVForChart = (file: File) => {
    Papa.parse(file, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        const data = results.data as PortfolioData[];
        const categoryMap = new Map<string, number>();
        data.forEach((row) => {
          const category = row.Category;
          const value = row.Value || 0;
          categoryMap.set(category, (categoryMap.get(category) || 0) + value);
        });
        const chartData = Array.from(categoryMap.entries())
          .map(([category, value]) => ({ category, value }))
          .sort((a, b) => b.value - a.value);
        setAllocationData(chartData);
      },
      error: (err) => console.error('CSV parsing error:', err),
    });
  };

  // ---- Backend wiring: POST /api/portfolio ----
  const handleFileUpload = async (file: File) => {
    setError('');
    setAnalysis(null);
    setAllocationData([]);

    if (file.size > MAX_FILE_SIZE) {
      setError(t('file_too_large'));
      return;
    }

    parseCSVForChart(file);

    setAnalyzing(true);
    const form = new FormData();
    form.append('file', file);
    form.append('language', locale);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio`, { method: 'POST', body: form });
      if (!res.ok) {
        const errorData = await res.json();
        setError(errorData.detail || t('sample_upload_error'));
        return;
      }
      const data = await res.json();
      setAnalysis(data);
    } catch (err) {
      setError(t('sample_upload_error'));
    } finally {
      setAnalyzing(false);
    }
  };

  // ---- Backend wiring: GET /api/portfolio/sample ----
  const handleSampleUpload = async (variant: string) => {
    setError('');
    setAnalyzing(true);
    setAnalysis(null);
    setAllocationData([]);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio/sample?variant=${variant}`);
      if (!res.ok) throw new Error('Failed to fetch sample portfolio');
      const blob = await res.blob();
      const file = new File([blob], 'sample_portfolio.csv', { type: 'text/csv' });
      await handleFileUpload(file);
    } catch (err) {
      setError(t('sample_upload_error'));
      setAnalyzing(false);
    }
  };

  // ---- Backend wiring: GET /api/portfolio/cas-sample (WEA-73) ----
  // Demo-safe: the backend analyses a known, hardcoded set of holdings for the
  // bundled sample CAS — no client-side PDF parsing, so the flow can't fail.
  const handleCasSample = async () => {
    setError('');
    setAnalyzing(true);
    setAnalysis(null);
    setAllocationData([]);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio/cas-sample?language=${locale}`);
      if (!res.ok) throw new Error('Failed to fetch sample CAS');
      const data = await res.json();
      const holdings = (data.holdings || []) as PortfolioData[];
      const categoryMap = new Map<string, number>();
      holdings.forEach((row) => {
        categoryMap.set(row.Category, (categoryMap.get(row.Category) || 0) + (row.Value || 0));
      });
      const chartData = Array.from(categoryMap.entries())
        .map(([category, value]) => ({ category, value }))
        .sort((a, b) => b.value - a.value);
      setAllocationData(chartData);
      setAnalysis(data.analysis);
    } catch (err) {
      setError(t('sample_upload_error'));
    } finally {
      setAnalyzing(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxSize: MAX_FILE_SIZE,
    onDrop: (files) => { if (files.length > 0) handleFileUpload(files[0]); },
    onDropRejected: (rejections) => {
      const rejection = rejections[0];
      if (rejection.errors.some(e => e.code === 'file-too-large')) setError(t('file_too_large'));
      else if (rejection.errors.some(e => e.code === 'file-invalid-type')) setError(t('invalid_format'));
    },
  });

  return (
    <div className="bg-white rounded-card border border-idbi-line shadow-card p-6">
      <div className="flex justify-between items-center mb-4 gap-4 flex-wrap">
        <div>
          <h2 className="text-lg font-bold text-idbi-ink">{t('title')}</h2>
          <p className="mt-1 text-sm text-idbi-muted">{t('subtitle')}</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <button
              onClick={handleCasSample}
              disabled={analyzing}
              title={t('cas_sample_note')}
              className={cn('inline-flex items-center gap-1.5 px-4 py-2.5 bg-white text-idbi-green border border-idbi-green rounded-tile hover:bg-idbi-light disabled:opacity-50 disabled:cursor-not-allowed text-sm font-bold transition-colors', FOCUS_RING)}
            >
              <FileText size={15} strokeWidth={2.2} />
              {t('cas_sample_button')}
            </button>

            <div className="relative">
              <button
                onClick={() => setSampleMenuOpen((o) => !o)}
                disabled={analyzing}
                aria-label={t('sample_menu_label')}
                aria-haspopup="menu"
                aria-expanded={sampleMenuOpen}
                className={cn('inline-flex items-center gap-1.5 px-4 py-2.5 bg-idbi-orange text-white rounded-tile hover:bg-idbi-orangeDark disabled:opacity-50 disabled:cursor-not-allowed text-sm font-bold transition-colors shadow-glowOrange', FOCUS_RING)}
              >
                <Zap size={15} strokeWidth={2.2} />
                {t('sample_button')}
                <span className="text-xs">▼</span>
              </button>

              {sampleMenuOpen && (
                <div
                  role="menu"
                  className="absolute right-0 mt-2 w-52 max-w-[calc(100vw-2rem)] bg-white rounded-field shadow-pop border border-idbi-line z-50 overflow-hidden"
                >
                  {SAMPLE_VARIANTS.map(({ variant, labelKey }) => (
                    <button
                      key={variant}
                      role="menuitem"
                      onClick={() => {
                        setSampleMenuOpen(false);
                        handleSampleUpload(variant);
                      }}
                      className={cn('w-full text-left px-4 py-2.5 text-sm text-idbi-ink hover:bg-idbi-light hover:text-idbi-green transition-colors', FOCUS_RING)}
                    >
                      {t(labelKey)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <a
            href={`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio/cas-sample/pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className={cn('text-xs text-idbi-muted hover:text-idbi-green underline underline-offset-2 rounded-field', FOCUS_RING)}
          >
            <span aria-hidden="true">📄</span> {t('cas_view_pdf')}
          </a>
        </div>
      </div>

      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-card px-5 py-10 text-center cursor-pointer transition-all',
          FOCUS_RING,
          isDragActive ? 'border-idbi-green bg-idbi-light' : 'border-idbi-line bg-idbi-surface hover:border-idbi-green/60 hover:bg-idbi-mintSoft',
        )}
      >
        <input {...getInputProps()} />
        <div className="w-12 h-12 mx-auto mb-3.5 rounded-field bg-idbi-light flex items-center justify-center">
          <UploadCloud size={22} className="text-idbi-green" strokeWidth={2} />
        </div>
        <p className="text-base font-semibold text-idbi-slate">{t('upload_prompt')}</p>
        <p className="mt-1.5 text-xs text-idbi-faint font-medium">{t('upload_hint')}</p>
      </div>

      {analyzing && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <span className="w-2 h-2 bg-idbi-green rounded-full animate-bounce" />
          <span className="w-2 h-2 bg-idbi-green rounded-full animate-bounce delay-100" />
          <span className="w-2 h-2 bg-idbi-green rounded-full animate-bounce delay-200" />
          <p className="ml-1 text-sm text-idbi-muted">{t('analyzing')}</p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {analysis && (
        <div className="mt-6 space-y-6 animate-rise">
          {/* Summary */}
          <div className="p-5 rounded-card bg-gradient-to-br from-idbi-light to-idbi-mintSoft border border-idbi-green/15">
            <h3 className="font-bold text-idbi-green mb-1.5">{t('summary_label')}</h3>
            <p className="text-sm leading-relaxed text-idbi-slate">{analysis.summary}</p>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="font-bold text-idbi-ink mb-3">{t('recommendations_label')}</h3>
            <ul className="space-y-2.5">
              {analysis.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2.5">
                  <span className="mt-0.5 text-idbi-green shrink-0"><Check size={16} strokeWidth={2.6} /></span>
                  <span className="text-sm text-idbi-slate leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* SIP suggestion */}
          <div className="p-5 rounded-card bg-gradient-to-br from-idbi-warmSoft to-idbi-warm border border-idbi-orange/20">
            <h3 className="font-bold text-idbi-orange mb-1.5">{t('sip_suggestion_label')}</h3>
            <p className="text-sm leading-relaxed text-idbi-slate">{analysis.sip_suggestion}</p>
          </div>

          {/* Allocation chart */}
          {allocationData.length > 0 && (
            <div>
              <h3 className="font-bold text-idbi-ink mb-3">{t('allocation_chart_label')}</h3>
              <div className="bg-idbi-surfaceAlt border border-idbi-line rounded-card p-3">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={allocationData} margin={{ top: 6, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#EEF3F1" vertical={false} />
                    <XAxis dataKey="category" tick={{ fill: '#9AAAA5', fontSize: 12 }} stroke="#E1EAE7" />
                    <YAxis tick={{ fill: '#9AAAA5', fontSize: 12 }} stroke="#E1EAE7" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#122622', border: 'none', borderRadius: '10px', color: '#fff' }}
                      formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, t('chart_value_label')]}
                      cursor={{ fill: 'rgba(0,131,108,.06)' }}
                    />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {allocationData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
