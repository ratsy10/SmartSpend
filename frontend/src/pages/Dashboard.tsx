import { useState, useEffect } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { api } from '../lib/api';
import { format } from 'date-fns';
import { TrendingUp } from 'lucide-react';
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

        // Fetch latest insight (non-blocking)
        try {
          const insightRes = await api.get('/insights/latest', { signal: controller.signal });
          setLatestInsight(insightRes.data);
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
  const isBudgetExceeded = summary ? summary.total_spent > summary.total_budget : false;

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

      {/* Main Balance Card */}
      <div className="bg-[#E6F9EC] rounded-2xl p-6 mb-6 shadow-sm border border-[#D1FAE5]">
        <div className="text-sm font-medium text-slate-500 mb-2 uppercase tracking-wide">
          Total Balance
        </div>
        <div className="text-4xl font-extrabold text-[#0F172A] mb-2 tracking-tight">
          {formatCurrency(summary?.total_spent || 0, currencyCode)}
        </div>
        {summary && Number(summary.vs_last_month) !== 0 ? (
          <div className={`flex items-center text-sm font-semibold ${Number(summary.vs_last_month) > 0 ? 'text-red-500' : 'text-[#10B981]'}`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            {Number(summary.vs_last_month) > 0 ? '+' : ''}{Number(summary.vs_last_month).toFixed(1)}% from last month
          </div>
        ) : (
          <div className="flex items-center text-sm font-semibold text-slate-400">
            First month tracked
          </div>
        )}
      </div>

      {/* AI Insight Card */}
      <div className="bg-[#0F172A] rounded-2xl p-6 shadow-lg mb-8 relative overflow-hidden">
        {/* Decorative background elements */}
        <div className="absolute right-0 bottom-0 opacity-20 pointer-events-none">
          <svg width="150" height="100" viewBox="0 0 150 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0 100L30 70L60 90L100 40L150 80V100H0Z" fill="#334155"/>
            <path d="M40 100L70 60L100 80L140 20L150 30V100H40Z" fill="#1E293B"/>
          </svg>
        </div>
        <div className="absolute top-4 right-4 text-[#334155] pointer-events-none">
           <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L14 10L22 12L14 14L12 22L10 14L2 12L10 10L12 2Z"></path>
           </svg>
        </div>

        <div className="flex items-center gap-2 mb-3 relative z-10">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L13.5 9.5L21 11L13.5 12.5L12 20L10.5 12.5L3 11L10.5 9.5L12 2Z" fill="#00E676" />
            <path d="M5 4L5.5 6.5L8 7L5.5 7.5L5 10L4.5 7.5L2 7L4.5 6.5L5 4Z" fill="#00E676" />
          </svg>
          <span className="text-white text-xs font-bold tracking-widest uppercase">AI Insight</span>
        </div>
        
        <p className="text-white text-lg font-medium leading-relaxed mb-5 relative z-10">
          {latestInsight ? latestInsight.content : (
            summary && summary.by_category.length > 0 
              ? `Your top spending category this month is ${summary.by_category[0]?.category_name || 'unknown'}.`
              : 'Start tracking expenses to get personalized insights!'
          )}
        </p>
        
        <Link to="/analytics" className="inline-block bg-[#00E676] hover:bg-[#00D16B] text-black font-bold text-sm px-5 py-2.5 rounded-full transition relative z-10">
          View Spending Trends
        </Link>
      </div>



      {/* Monthly Budget Preview */}
      <div className="mb-8">
        <div className="flex justify-between items-end mb-4 px-1">
          <h3 className="text-xl font-bold text-[#0F172A]">Monthly Budget</h3>
          <span className="text-sm text-slate-500 font-medium">{format(new Date(), 'MMMM yyyy')}</span>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
          <div className="flex justify-between items-baseline mb-3">
            <span className="text-slate-600 font-medium text-sm border-b border-transparent">Spending vs. Limit</span>
            <span className="font-bold text-[#0F172A]">
              {formatCurrency(summary?.total_spent || 0, currencyCode)} 
              <span className="text-slate-400 font-normal">
                {summary && summary.total_budget > 0 ? ` / ${formatCurrency(summary.total_budget, currencyCode)}` : ' (No limit)'}
              </span>
            </span>
          </div>
          
          {summary && summary.total_budget > 0 && (
            <>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden mb-3">
                <div 
                  className={`h-full rounded-full transition-all ${isBudgetExceeded ? 'bg-red-500' : 'bg-[#00E676]'}`} 
                  style={{ width: `${Math.min(summary.budget_used_pct, 100)}%` }}
                />
              </div>
              
              <div className="flex justify-between items-center text-xs">
                <span className={`${isBudgetExceeded ? 'text-red-500' : 'text-[#00E676]'} font-semibold italic`}>
                  {summary.budget_used_pct}% of budget used
                </span>
                <span className="text-slate-400 font-medium">
                  {isBudgetExceeded 
                    ? `Exceeded by ${formatCurrency(summary.total_spent - summary.total_budget, currencyCode)}`
                    : `${formatCurrency(summary.total_budget - summary.total_spent, currencyCode)} remaining`}
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Top Categories / Recent */}
      <div>
        <div className="flex justify-between items-center mb-4 px-1">
          <h3 className="text-xl font-bold text-[#0F172A]">Recent Transactions</h3>
          <Link to="/history" className="text-[#00E676] text-sm font-bold flex items-center gap-1 hover:underline">
            View all
          </Link>
        </div>
        
        {recent.length === 0 ? (
          <div className="bg-white border border-slate-100 rounded-2xl p-8 text-center shadow-sm">
            <p className="text-slate-400 mb-4">No expenses yet</p>
            <Link to="/add" className="text-[#00E676] font-bold hover:underline">Add your first expense</Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recent.map((exp) => (
              <div key={exp.id} className="bg-white p-4 rounded-2xl flex items-center justify-between border border-slate-100 shadow-sm hover:shadow-md transition cursor-pointer">
                <div className="flex items-center gap-4">
                  <div 
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-xl"
                    style={{ backgroundColor: `${exp.category.color}15`, color: exp.category.color }}
                  >
                    <CategoryIcon name={exp.category.icon} className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-bold text-[#0F172A] text-[15px]">{exp.merchant || exp.category.name}</h4>
                    <p className="text-[13px] text-slate-400 mt-0.5">{format(new Date(exp.expense_date), 'MMM dd, yyyy')}</p>
                  </div>
                </div>
                <div className="font-bold text-[#0F172A] text-right">
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
