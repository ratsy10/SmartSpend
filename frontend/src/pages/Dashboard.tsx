import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { api } from '../lib/api';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';
import { formatCurrency } from '../lib/utils';
import CategoryIcon from '../components/CategoryIcon';

interface MonthlySummary {
  total_spent: number;
  total_budget: number;
  budget_used_pct: number;
  vs_last_month: number;
  by_category: any[];
}

interface LatestInsight {
  id: string;
  content: string;
  title?: string;
  top_category?: string;
}

interface Expense {
  id: string;
  amount: number;
  currency: string;
  category: { id: string, name: string, icon: string, color: string };
  merchant?: string;
  expense_date: string;
}

export default function Dashboard() {
  const user = useAuthStore(state => state.user);
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [recent, setRecent] = useState<Expense[]>([]);
  const [latestInsight, setLatestInsight] = useState<LatestInsight | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    const fetchDashboardData = async () => {
      try {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        
        const [sumRes, expRes] = await Promise.all([
          api.get(`/analytics/summary?year=${year}&month=${month}`, { signal: controller.signal }),
          api.get(`/expenses?limit=5`, { signal: controller.signal })
        ]);

        // Normalize decimal strings to numbers
        const s = sumRes.data;
        setSummary({
          ...s,
          total_spent: Number(s.total_spent),
          total_budget: Number(s.total_budget),
          budget_used_pct: Number(s.budget_used_pct),
          vs_last_month: Number(s.vs_last_month),
        });
        setRecent(expRes.data.data || expRes.data.items || []);

        // Fetch latest insight (non-blocking) - prefer the deep localStorage insights generated in Analytics
        try {
          const cachedInsightsStr = localStorage.getItem(`smartSpendAiInsights_${user?.id}`);
          if (cachedInsightsStr) {
            const parsed = JSON.parse(cachedInsightsStr);
            if (Array.isArray(parsed) && parsed.length > 0) {
              setLatestInsight({
                id: 'local',
                content: parsed[0].message,
                title: parsed[0].title
              });
            }
          } else {
            const insightRes = await api.get('/insights/latest', { signal: controller.signal });
            if (insightRes.data && insightRes.data.content) {
              setLatestInsight(insightRes.data);
            }
          }
        } catch { /* no insights yet */ }

      } catch (err: any) {
        if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return; // StrictMode cleanup
        console.error("Failed to fetch dashboard data", err);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };

    fetchDashboardData();
    return () => controller.abort();
  }, []);

  const currencyCode = user?.currency || 'USD';
  const isBudgetExceeded = summary ? Number(summary.total_spent) > Number(summary.total_budget) : false;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      <header className="mb-6 flex justify-between items-center hidden">
        <h1 className="text-3xl font-bold mb-1">Overview</h1>
        <p className="text-textMuted">{format(new Date(), 'MMMM yyyy')}</p>
      </header>

      {/* Monthly Budget Preview */}
      <div className="mb-8">
        <div className="flex justify-between items-end mb-4 px-1">
          <h3 className="text-xl font-bold text-textMain">Monthly Budget</h3>
          <span className="text-sm text-textMuted font-medium">{format(new Date(), 'MMMM yyyy')}</span>
        </div>
        <div className="bg-surface rounded-2xl p-5 shadow-sm border border-border/50">
          <div className="flex justify-between items-baseline mb-3">
            <span className="text-textMuted font-medium text-sm border-b border-transparent">Spending vs. Limit</span>
            <span className="font-bold text-textMain">
              {formatCurrency(summary?.total_spent || 0, currencyCode)} 
              <span className="text-textMuted font-normal">
                {summary && summary.total_budget > 0 ? ` / ${formatCurrency(summary.total_budget, currencyCode)}` : ' (No limit)'}
              </span>
            </span>
          </div>
          
          {summary && summary.total_budget > 0 && (
            <>
              <div className="h-3 w-full bg-border rounded-full overflow-hidden mb-3">
                <div 
                  className={`h-full rounded-full transition-all ${isBudgetExceeded ? 'bg-red-500' : 'bg-[#00E676]'}`} 
                  style={{ width: `${Math.min(summary.budget_used_pct, 100)}%` }}
                />
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span className={`${isBudgetExceeded ? 'text-red-500' : 'text-[#00E676]'} font-semibold italic`}>
                  {summary.budget_used_pct}% of budget used
                </span>
                <span className="text-textMuted font-medium">
                  {isBudgetExceeded 
                    ? `Exceeded by ${formatCurrency(summary.total_spent - summary.total_budget, currencyCode)}`
                    : `${formatCurrency(summary.total_budget - summary.total_spent, currencyCode)} remaining`}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* AI Insight Card */}
      <div className="rounded-2xl p-6 shadow-lg mb-8 relative overflow-hidden transition-colors" style={{ backgroundColor: 'var(--insight-bg)' }}>
        {/* Decorative background elements */}
        <div className="absolute right-0 bottom-0 opacity-20 pointer-events-none">
          <svg width="150" height="100" viewBox="0 0 150 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 100L30 70L60 90L100 40L150 80V100H0Z" fill="currentColor" style={{ color: 'var(--insight-icon)' }} className="opacity-50" />
            <path d="M40 100L70 60L100 80L140 20L150 30V100H40Z" fill="currentColor" style={{ color: 'var(--insight-icon)' }} />
          </svg>
        </div>
        <div className="absolute top-4 right-4 pointer-events-none transition-colors" style={{ color: 'var(--insight-icon)' }}>
           <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L14 10L22 12L14 14L12 22L10 14L2 12L10 10L12 2Z"></path>
           </svg>
        </div>

        <div className="flex items-center gap-2 mb-3 relative z-10">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L13.5 9.5L21 11L13.5 12.5L12 20L10.5 12.5L3 11L10.5 9.5L12 2Z" fill="#00E676" />
            <path d="M5 4L5.5 6.5L8 7L5.5 7.5L5 10L4.5 7.5L2 7L4.5 6.5L5 4Z" fill="#00E676" />
          </svg>
          <span className="text-[11px] font-bold tracking-widest uppercase transition-colors" style={{ color: 'var(--insight-text)' }}>
            {latestInsight?.title ? `Insight • ${latestInsight.title}` : 'AI Insight'}
          </span>
        </div>
        
        <p className="text-[15px] font-medium leading-relaxed mb-5 relative z-10 transition-colors" style={{ color: 'var(--insight-text-muted)' }}>
          {latestInsight ? latestInsight.content : (
            summary && summary.by_category.length > 0 
              ? `Your top spending category this month is ${summary.by_category[0]?.category_name || 'unknown'}. Head to the Analytics tab to generate deep behavioral insights!`
              : 'Add some expenses and visit the Analytics tab to get personalized AI insights!'
          )}
        </p>
        
        <Link to="/analytics" className="inline-block bg-[#00E676] hover:bg-[#00D16B] text-black font-bold text-sm px-5 py-2.5 rounded-full transition relative z-10">
          View Spending Trends
        </Link>
      </div>




      {/* Top Categories / Recent */}
      <div>
        <div className="flex justify-between items-center mb-4 px-1">
          <h3 className="text-xl font-bold text-textMain">Recent Transactions</h3>
          <Link to="/history" className="text-[#00E676] text-sm font-bold flex items-center gap-1 hover:underline">
            View all
          </Link>
        </div>
        
        {recent.length === 0 ? (
          <div className="bg-surface border border-border/50 rounded-2xl p-8 text-center shadow-sm">
            <p className="text-textMuted mb-4">No expenses yet</p>
            <Link to="/add" className="text-[#00E676] font-bold hover:underline">Add your first expense</Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recent.map((exp) => (
              <div key={exp.id} className="bg-surface p-4 rounded-2xl flex items-center justify-between border border-border/50 shadow-sm hover:shadow-md transition cursor-pointer">
                <div className="flex items-center gap-4">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-xl"
                    style={{ backgroundColor: `${exp.category.color}1a`, color: exp.category.color }}
                  >
                    <CategoryIcon name={exp.category.icon} className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-bold text-textMain text-[15px]">{exp.merchant || exp.category.name}</h4>
                    <p className="text-[13px] text-textMuted mt-0.5">{format(new Date(exp.expense_date), 'MMM dd, yyyy')}</p>
                  </div>
                </div>
                <div className="font-bold text-textMain text-right">
                  {formatCurrency(exp.amount, exp.currency)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
