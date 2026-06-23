'use client';
import { useTranslations } from 'next-intl';
import { useDropzone } from 'react-dropzone';
import { useState } from 'react';

export default function PortfolioCard() {
  const t = useTranslations('dashboard');
  const [analysing, setAnalysing] = useState(false);
  const [result, setResult] = useState('');

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    onDrop: async (files) => {
      setAnalysing(true);
      const form = new FormData();
      form.append('file', files[0]);
      form.append('language', 'en');
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/portfolio`, { method: 'POST', body: form });
      const data = await res.json();
      setResult(data.analysis);
      setAnalysing(false);
    },
  });

  return (
    <div className="bg-white rounded-2xl shadow p-6 col-span-2">
      <h2 className="text-lg font-semibold text-idbi-blue mb-4">{t('portfolio')}</h2>
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${isDragActive ? 'border-idbi-blue bg-idbi-light' : 'border-gray-200'}`}>
        <input {...getInputProps()} />
        <p className="text-gray-500 text-sm">{t('uploadPortfolio')}</p>
      </div>
      {analysing && <p className="mt-4 text-sm text-gray-500 animate-pulse">Analysing your portfolio...</p>}
      {result && <p className="mt-4 text-sm text-gray-700 leading-relaxed">{result}</p>}
    </div>
  );
}
