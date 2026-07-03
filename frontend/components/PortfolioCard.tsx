'use client';
import { useTranslations, useLocale } from 'next-intl';
import { useDropzone } from 'react-dropzone';
import { useState } from 'react';
import * as Papa from 'papaparse';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface PortfolioData {
  Ticker: string;
  Category: string;
  Value: number;
  Units: number;
}

interface AnalysisResult {
  summary: string;
  recommendations: string[];
  sip_suggestion: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

export default function PortfolioCard() {
  const t = useTranslations('portfolio');
  const locale = useLocale();
  const [analyzing, setAnalyzing] = useState(false);
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

        // Group by category and sum values
        const categoryMap = new Map<string, number>();
        data.forEach((row) => {
          const category = row.Category;
          const value = row.Value || 0;
          categoryMap.set(category, (categoryMap.get(category) || 0) + value);
        });

        // Convert to array and sort by value
        const chartData = Array.from(categoryMap.entries())
          .map(([category, value]) => ({ category, value }))
          .sort((a, b) => b.value - a.value);

        setAllocationData(chartData);
      },
      error: (err) => {
        console.error('CSV parsing error:', err);
      }
    });
  };

  const handleFileUpload = async (file: File) => {
    // Reset state
    setError('');
    setAnalysis(null);
    setAllocationData([]);

    // Validate file size
    if (file.size > MAX_FILE_SIZE) {
      setError(t('file_too_large'));
      return;
    }

    // Parse CSV for chart
    parseCSVForChart(file);

    // Upload to backend for analysis
    setAnalyzing(true);
    const form = new FormData();
    form.append('file', file);
    form.append('language', locale);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio`, {
        method: 'POST',
        body: form
      });

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

  const handleSampleUpload = async () => {
    setError('');
    setAnalyzing(true);
    setAnalysis(null);
    setAllocationData([]);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio/sample`);
      if (!res.ok) {
        throw new Error('Failed to fetch sample portfolio');
      }

      const blob = await res.blob();
      const file = new File([blob], 'sample_portfolio.csv', { type: 'text/csv' });

      // Trigger analysis with sample file
      await handleFileUpload(file);
    } catch (err) {
      setError(t('sample_upload_error'));
      setAnalyzing(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxSize: MAX_FILE_SIZE,
    onDrop: (files) => {
      if (files.length > 0) {
        handleFileUpload(files[0]);
      }
    },
    onDropRejected: (rejections) => {
      const rejection = rejections[0];
      if (rejection.errors.some(e => e.code === 'file-too-large')) {
        setError(t('file_too_large'));
      } else if (rejection.errors.some(e => e.code === 'file-invalid-type')) {
        setError(t('invalid_format'));
      }
    }
  });

  return (
    <div className="bg-white rounded-2xl shadow p-6 col-span-2">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-idbi-green">{t('title')}</h2>
        <button
          onClick={handleSampleUpload}
          disabled={analyzing}
          className="px-4 py-2 bg-idbi-orange text-white rounded-lg hover:bg-idbi-orange/90 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
        >
          {t('sample_button')}
        </button>
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-idbi-green bg-idbi-light' : 'border-gray-200'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-gray-500 text-sm">{t('upload_prompt')}</p>
        <p className="text-gray-400 text-xs mt-2">Max 2MB • CSV only</p>
      </div>

      {analyzing && (
        <div className="mt-4 flex items-center justify-center">
          <div className="animate-pulse flex items-center space-x-2">
            <div className="w-2 h-2 bg-idbi-green rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-idbi-green rounded-full animate-bounce delay-100" />
            <div className="w-2 h-2 bg-idbi-green rounded-full animate-bounce delay-200" />
          </div>
          <p className="ml-2 text-sm text-gray-500">{t('analyzing')}</p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {analysis && (
        <div className="mt-6 space-y-6">
          {/* Summary Card */}
          <div className="bg-gradient-to-br from-idbi-light to-teal-50 p-4 rounded-xl border border-idbi-green/20">
            <h3 className="font-semibold text-idbi-green mb-2">{t('summary_label')}</h3>
            <p className="text-sm text-gray-700">{analysis.summary}</p>
          </div>

          {/* Recommendations */}
          <div>
            <h3 className="font-semibold text-idbi-green mb-3">{t('recommendations_label')}</h3>
            <ul className="space-y-2">
              {analysis.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <span className="text-sm text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* SIP Suggestion */}
          <div className="bg-gradient-to-br from-yellow-50 to-amber-50 p-4 rounded-xl border-2 border-idbi-orange/30">
            <h3 className="font-semibold text-idbi-orange mb-2">{t('sip_suggestion_label')}</h3>
            <p className="text-sm text-gray-700">{analysis.sip_suggestion}</p>
          </div>

          {/* Allocation Chart */}
          {allocationData.length > 0 && (
            <div>
              <h3 className="font-semibold text-idbi-green mb-3">{t('allocation_chart_label')}</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={allocationData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="category"
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    stroke="#9CA3AF"
                  />
                  <YAxis
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    stroke="#9CA3AF"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#fff'
                    }}
                    formatter={(value: number) => [`₹${value.toLocaleString()}`, 'Value']}
                  />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {allocationData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
