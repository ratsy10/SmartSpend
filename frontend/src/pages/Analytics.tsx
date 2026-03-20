import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Bell, ArrowLeft, AlertCircle } from 'lucide-react';
import { AreaChart, Area, XAxis, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { formatCurrency } from '../lib/utils';
import AddBudgetModal from '../components/AddBudgetModal';
import CategoryIcon from '../components/CategoryIcon';



interface MonthlySummary {
  total_spent: number;
  total_budget: number;
  budget_used_pct: number;
  vs_last_month: number;
  by_category: any[];
}

interface BudgetStatus {
  id: string;
  category_id: string;
  category_name: string;
  limit: number;
  spent: number;
  remaining: number;
  percentage: number;
}

interface BudgetItem {
  category_id: string;
  category_name: string;
  budget_id?: string;
  icon?: string;
  color?: string;
  limit: number;
  spent: number;
  percentage: number;
}

interface Suggestion {
  id: string;
  type: string;
  category: { name: string, icon: string, color: string };
  message: string;
}



export default function Analytics() {
  const user = useAuthStore(state => state.user);
  const [budgetItems, setBudgetItems] = useState<BudgetItem[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [trendData, setTrendData] = useState<{name: string, value: number}[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Budget');
  const [isAddBudgetOpen, setIsAddBudgetOpen] = useState(false);
  const [modalInitialData, setModalInitialData] = useState<{
    categoryId: string;
    budgetId?: string;
    limit: number;
  } | null>(null);
  const currencyCode = user?.currency || 'USD';

  const fetchData = async () => {
    try {
      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth() + 1;
      const [budgetsRes, suggestionsRes, sumRes, trendRes, catsRes] = await Promise.all([
        api.get('/budgets/status'),
        api.get('/insights/suggestions'),
        api.get(`/analytics/summary?year=${year}&month=${month}`),
        api.get('/analytics/trend?months=6'),
        api.get('/categories')
      ]);
      setSuggestions(suggestionsRes.data);
      
      const activeBudgets = budgetsRes.data as BudgetStatus[];
      const cats = catsRes.data as any[];
      const items = cats.map(cat => {
        const b = activeBudgets.find(ab => ab.category_id === cat.id);
        if (b) {
            return {
                budget_id: b.id,
                category_id: cat.id,
                category_name: cat.name,
                icon: cat.icon,
                color: cat.color,
                limit: b.limit,
                spent: b.spent,
                percentage: b.percentage
            };
        }
        return {
                category_id: cat.id,
                category_name: cat.name,
                icon: cat.icon,
                color: cat.color,
                limit: 0,
                spent: 0,
                percentage: 0
        };
      });
      // Sort: budgeted categories first, then unset ones
      items.sort((a, b) => {
        if (a.limit > 0 && b.limit <= 0) return -1;
        if (a.limit <= 0 && b.limit > 0) return 1;
        return 0;
      });
      setBudgetItems(items);
      
      const s2 = sumRes.data;
      setSummary({
        ...s2,
        total_spent: Number(s2.total_spent),
        total_budget: Number(s2.total_budget),
        budget_used_pct: Number(s2.budget_used_pct),
        vs_last_month: Number(s2.vs_last_month),
      });
      const mapped = (trendRes.data || []).map((t: { month: string; total: number }) => ({
        name: t.month.split('-')[1] ? new Date(t.month + '-01').toLocaleString('default', { month: 'short' }).toUpperCase() : t.month,
        value: Number(t.total)
      }));
      setTrendData(mapped);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return;
      console.error("Failed to fetch analytics", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openBudgetModal = (item?: BudgetItem) => {
    if (item) {
      setModalInitialData({
        categoryId: item.category_id,
        budgetId: item.budget_id,
        limit: item.limit || 0
      });
    } else {
      setModalInitialData(null);
    }
    setIsAddBudgetOpen(true);
  };

  const dismissSuggestion = async (id: string) => {
    try {
      await api.post(`/insights/suggestions/${id}/dismiss`);
      setSuggestions(prev => prev.filter(s => s.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-6 relative z-10">
      <header className="flex items-center justify-between mb-8 px-1">
        <Link to="/" className="text-[#0F172A] hover:opacity-70 transition">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <h1 className="text-[22px] font-bold text-[#0F172A]">Budget & Insights</h1>
        <button className="relative text-[#0F172A] hover:opacity-70 transition">
          <Bell className="w-6 h-6" />
          <span className="absolute top-0.5 right-1 w-2 h-2 bg-[#00E676] rounded-full border border-background"></span>
        </button>
      </header>

      {/* Tabs */}
      <div className="flex gap-8 border-b border-slate-200 mb-8 px-2">
        {['Overview', 'Budget', 'Insights'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 font-semibold text-[15px] transition-colors relative ${
              activeTab === tab ? 'text-[#0F172A]' : 'text-slate-400'
            }`}
          >
            {tab}
            {activeTab === tab && (
              <div className="absolute bottom-0 left-0 w-full h-0.5 bg-[#00E676] rounded-t-full"></div>
            )}
          </button>
        ))}
      </div>

      {activeTab === 'Budget' && (
        <>
          {/* Main Chart Card */}
          <div className="bg-white rounded-3xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 mb-8">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Monthly Spending</h3>
                <div className="text-[32px] font-extrabold text-[#0F172A] leading-tight">{formatCurrency(summary?.total_spent || 0, currencyCode)}</div>
              </div>
              {summary && summary.vs_last_month !== 0 && (
                <div className={`${summary.vs_last_month > 0 ? 'bg-red-50 text-red-500' : 'bg-green-50 text-[#00E676]'} font-bold text-xs px-2.5 py-1 rounded-md flex items-center gap-1`}>
                  {summary.vs_last_month > 0 ? '↗' : '↘'} {Math.abs(summary.vs_last_month)}%
                </div>
              )}
            </div>

            <div className="h-40 w-full ml-[-10px] mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00E676" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#00E676" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 10, fontWeight: 600 }} dy={10} />
                  <Area type="monotone" dataKey="value" stroke="#00E676" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Budget Goals */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4 px-1">
              <h3 className="text-xl font-bold text-[#0F172A]">Budget Goals</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              {budgetItems.length === 0 ? (
                 <div className="col-span-2 bg-white rounded-3xl p-8 border border-slate-100 text-center text-slate-400">
                    No categories found.
                 </div>
              ) : budgetItems.map(item => (
              <div 
                key={item.category_id} 
                onClick={() => openBudgetModal(item)}
                className="bg-white rounded-3xl p-5 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col justify-center items-center cursor-pointer hover:border-primary/30 transition-colors"
                title="Tap to edit budget"
              >
                <div className="relative w-20 h-20 mb-4 flex items-center justify-center">
                  {item.limit > 0 ? (
                    <>
                      <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                        <circle cx="40" cy="40" r="36" stroke="#F1F5F9" strokeWidth="8" fill="none" />
                        <circle cx="40" cy="40" r="36" stroke={item.spent > item.limit ? "#EF4444" : "#00E676"} strokeWidth="8" fill="none" strokeDasharray="226" strokeDashoffset={226 - (226 * Math.min(item.percentage, 100) / 100)} className="drop-shadow-[0_2px_4px_rgba(0,230,118,0.3)]" />
                      </svg>
                      <div className="font-bold text-[#0F172A] text-sm z-10">
                        {Math.round(item.percentage)}%
                      </div>
                    </>
                  ) : (
                    <>
                      <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                        <circle cx="40" cy="40" r="36" stroke="#F1F5F9" strokeWidth="6" fill="none" strokeDasharray="5 5" />
                      </svg>
                      <div className="z-10 text-slate-300 flex flex-col items-center">
                        <div 
                          className="w-10 h-10 rounded-full flex items-center justify-center mb-1"
                          style={{ backgroundColor: `${item.color || '#94A3B8'}15`, color: item.color || '#94A3B8' }}
                        >
                          <CategoryIcon name={item.icon} className="w-5 h-5" />
                        </div>
                      </div>
                    </>
                  )}
                </div>
                <h4 className="font-bold text-[#0F172A] text-[15px] mb-1 text-center truncate w-full">{item.category_name}</h4>
                <p className="text-xs text-slate-400 font-medium">
                  {item.limit > 0 
                    ? `${formatCurrency(item.spent, currencyCode)} / ${formatCurrency(item.limit, currencyCode)}`
                    : 'Not Set'}
                </p>
              </div>
              ))}
            </div>
          </div>

          {suggestions.length > 0 && (
          <div className="bg-[#ECFDF5] rounded-3xl p-5 border border-[#D1FAE5]">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-full bg-[#00E676] flex items-center justify-center text-white">
                <AlertCircle className="w-3.5 h-3.5" />
              </div>
              <h3 className="text-[17px] font-bold text-[#0F172A]">Smart Suggestions</h3>
            </div>

            <div className="space-y-4">
              {suggestions.map((s) => (
              <div key={s.id} className="bg-white rounded-2xl p-4 shadow-sm relative overflow-hidden flex gap-4">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border border-slate-100"
                  style={{ backgroundColor: `${s.category?.color || '#00E676'}15`, color: s.category?.color || '#00E676' }}
                >
                  <CategoryIcon name={s.category?.icon} className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-[#0F172A] text-[15px] leading-tight mb-1 capitalize">{s.type.replace('_', ' ')}</h4>
                  <p className="text-[13px] text-slate-500 leading-relaxed mb-3 pr-2">
                    {s.message}
                  </p>
                  <div className="flex gap-2">
                    <button onClick={() => dismissSuggestion(s.id)} className="bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold text-xs px-4 py-2 rounded-lg transition">
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
              ))}
            </div>
          </div>
          )}
        </>
      )}

      {activeTab !== 'Budget' && (
        <div className="bg-white rounded-3xl p-8 border border-slate-100 text-center text-slate-400">
          This tab is under construction
        </div>
      )}

      <AddBudgetModal 
        isOpen={isAddBudgetOpen} 
        onClose={() => setIsAddBudgetOpen(false)} 
        onSuccess={() => fetchData()} 
        initialData={modalInitialData}
      />
    </div>
  );
}
