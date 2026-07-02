'use client';
import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444'];

interface QuizAnswer {
  question_id: number;
  answer: string;
}

interface RiskProfile {
  profile: string;
  score: number;
  explanation: string;
  recommended_allocation: { [key: string]: number };
}

export default function RiskQuiz() {
  const t = useTranslations('risk');
  const [currentStep, setCurrentStep] = useState(1);
  const [answers, setAnswers] = useState<QuizAnswer[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<RiskProfile | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

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
    const newAnswers = [...answers, { question_id: currentStep, answer: answerValue }];
    setAnswers(newAnswers);

    if (currentStep < 5) {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentStep(currentStep + 1);
        setIsTransitioning(false);
      }, 200);
    } else {
      await submitQuiz(newAnswers);
    }
  };

  const submitQuiz = async (quizAnswers: QuizAnswer[]) => {
    setIsAnalyzing(true);

    try {
      const response = await fetch('http://localhost:8000/api/risk-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: quizAnswers, language: 'en' }),
      });

      if (!response.ok) throw new Error('Failed to submit quiz');

      const data = await response.json();
      setTimeout(() => {
        setResult(data);
        setIsAnalyzing(false);
      }, 1500);
    } catch (error) {
      console.error('Error submitting quiz:', error);
      setIsAnalyzing(false);
    }
  };

  const retakeQuiz = () => {
    setCurrentStep(1);
    setAnswers([]);
    setResult(null);
    setIsTransitioning(false);
  };

  const getChartData = (allocation: { [key: string]: number }) => {
    return Object.entries(allocation).map(([name, value]) => ({ name, value }));
  };

  if (isAnalyzing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="relative w-32 h-32 mb-6">
          <div className="absolute inset-0 bg-gradient-to-r from-idbi-blue to-idbi-darkBlue rounded-full animate-pulse opacity-50"></div>
          <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center">
            <div className="w-20 h-20 bg-idbi-blue rounded-full flex items-center justify-center animate-pulse">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>
        </div>
        <p className="text-lg font-medium text-gray-600 animate-pulse">{t('analysing_label')}</p>
      </div>
    );
  }

  if (result) {
    const chartData = getChartData(result.recommended_allocation);
    const profileKey = `result_${result.profile}`;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-idbi-blue mb-4">{t('title')}</h2>
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold capitalize ${result.profile === 'conservative' ? 'bg-green-100 text-green-800' : result.profile === 'moderate' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'}`}>
            {t(profileKey as 'result_conservative' | 'result_moderate' | 'result_aggressive')}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">{t('explanation_label')}</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry) => `${entry.name}: ${entry.value}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {chartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center">
              <p className="text-gray-600">{result.explanation}</p>
            </div>
          </div>
        </div>

        <button
          onClick={retakeQuiz}
          className="w-full py-3 px-4 bg-idbi-blue hover:bg-idbi-darkBlue text-white rounded-lg font-medium transition-colors min-h-[56px]"
        >
          {t('retake_button')}
        </button>
      </div>
    );
  }

  const currentQuestion = questions[currentStep - 1];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-idbi-blue">{t('title')}</h2>
        <span className="text-sm text-gray-500">
          {t('step_label', { current: currentStep, total: 5 })}
        </span>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
        <div
          className="bg-idbi-blue h-2 rounded-full transition-all duration-300"
          style={{ width: `${(currentStep / 5) * 100}%` }}
        />
      </div>

      <div
        className={`transition-opacity duration-200 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}
        key={currentStep}
      >
        <p className="text-lg text-gray-700 mb-6 font-medium">{t(currentQuestion.key as 'question1' | 'question2' | 'question3' | 'question4' | 'question5')}</p>

        <div className="space-y-3">
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => handleAnswer(option.value)}
              className="w-full text-left py-4 px-6 bg-white hover:bg-idbi-blue hover:text-white border-2 border-gray-200 hover:border-idbi-blue rounded-lg font-medium transition-all duration-200 min-h-[56px] flex items-center"
            >
              <span className="mr-3 font-bold">{option.value}.</span>
              {t(option.label as 'option_a' | 'option_b' | 'option_c' | 'option_d')}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
