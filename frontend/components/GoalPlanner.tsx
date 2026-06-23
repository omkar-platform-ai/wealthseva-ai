'use client';
import { useTranslations } from 'next-intl';
import { useState } from 'react';

export default function GoalPlanner() {
  const t = useTranslations('goals');
  const [goals, setGoals] = useState([{ name: '', target_amount: '', target_date: '', monthly_contribution: '' }]);

  return (
    <div className="space-y-4">
      {goals.map((goal, i) => (
        <div key={i} className="bg-white rounded-2xl shadow p-6 grid grid-cols-2 gap-4">
          <input placeholder={t('retirement')} value={goal.name} onChange={e => { const g = [...goals]; g[i].name = e.target.value; setGoals(g); }} className="col-span-2 border rounded-lg px-3 py-2 text-sm" />
          <input placeholder={t('targetAmount')} type="number" value={goal.target_amount} onChange={e => { const g = [...goals]; g[i].target_amount = e.target.value; setGoals(g); }} className="border rounded-lg px-3 py-2 text-sm" />
          <input placeholder={t('monthly')} type="number" value={goal.monthly_contribution} onChange={e => { const g = [...goals]; g[i].monthly_contribution = e.target.value; setGoals(g); }} className="border rounded-lg px-3 py-2 text-sm" />
        </div>
      ))}
      <button onClick={() => setGoals([...goals, { name: '', target_amount: '', target_date: '', monthly_contribution: '' }])} className="text-idbi-blue text-sm font-medium hover:underline">
        + {t('addGoal')}
      </button>
    </div>
  );
}
