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
  content: string;
  top_category?: string;
  category?: { name: string, icon: string, color: string };
}



export default function Analytics() {
  const user = useAuthStore(state => state.user);
  const [budgetItems, setBudgetItems] = useState<BudgetItem[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [trendData, setTrendData] = useState<{name: string, value: number}[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Overview'); // Changed default to Overview per normal UX conventions
  const [isAddBudgetOpen, setIsAddBudgetOpen] = useState(false);
  const [aiInsights, setAiInsights] = useState<{type: string, title: string, message: string}[]>([]);
  const [generatingInsights, setGeneratingInsights] = useState(false);
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

      // AI Auto-Refresh Logic
      const currentTxCount = Number(s2.transaction_count || 0);
      const cachedInsights = localStorage.getItem(`smartSpendAiInsights_${user?.id}`);
      const cachedTxCount = Number(localStorage.getItem(`smartSpendAiTxCount_${user?.id}`) || 0);

      if (cachedInsights) {
        setAiInsights(JSON.parse(cachedInsights));
      }

      if (!cachedInsights || currentTxCount >= cachedTxCount + 10) {
        generateAIInsightsLocal(currentTxCount);
      }
      
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return;
      console.error("Failed to fetch analytics", err);
    } finally {
      setLoading(false);
    }
  };

  const generateAIInsightsLocal = async (txCountToCache: number) => {
    setGeneratingInsights(true);
    try {
      const { data } = await api.post('/insights/generate');
      setAiInsights(data);
      localStorage.setItem(`smartSpendAiInsights_${user?.id}`, JSON.stringify(data));
      localStorage.setItem(`smartSpendAiTxCount_${user?.id}`, txCountToCache.toString());
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingInsights(false);
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

  const generateAIInsights = async () => {
    setGeneratingInsights(true);
    try {
      const { data } = await api.post('/insights/generate');
      setAiInsights(data);
      localStorage.setItem('smartSpendAiInsights', JSON.stringify(data));
      localStorage.setItem('smartSpendAiTxCount', summary?.total_spent?.toString() || '0'); // Fallback
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingInsights(false);
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


      {/* Tabs */}
      <div className="flex gap-8 border-b border-border/50 mb-8 px-2">
        {['Overview', 'Budget', 'Insights'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 font-semibold text-[15px] transition-colors relative ${
              activeTab === tab ? 'text-textMain' : 'text-textMuted'
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
          <div className="mb-8">
            <h3 className="text-xl font-bold text-textMain mb-4 px-1">Budget Goals</h3>
            <div className="grid grid-cols-2 gap-4">
              {budgetItems.length === 0 ? (
                 <div className="col-span-2 bg-surface rounded-3xl p-8 border border-border/50 text-center text-textMuted">
                    No categories found.
                 </div>
              ) : budgetItems.map(item => (
              <div 
                key={item.category_id} 
                onClick={() => openBudgetModal(item)}
                className="bg-surface rounded-3xl p-5 shadow-sm border border-border/50 flex flex-col justify-center items-center cursor-pointer hover:border-primary/30 transition-colors"
                title="Tap to edit budget"
              >
                <div className="relative w-20 h-20 mb-4 flex items-center justify-center">
                  {item.limit > 0 ? (
                    <>
                    {/* Circular Progress */}
                    <svg className="absolute inset-0 w-full h-full transform -rotate-90" viewBox="0 0 80 80">
                      <circle 
                        cx="40" cy="40" r="36" 
                        stroke="rgba(148, 163, 184, 0.15)" strokeWidth="8" fill="none" 
                      />
                      <circle 
                        cx="40" cy="40" r="36" 
                        stroke={item.percentage > 85 ? '#EF4444' : item.percentage > 50 ? '#F59E0B' : '#00E676'} 
                        strokeWidth="8" fill="transparent" 
                        strokeDasharray={226}
                        strokeDashoffset={226 - (226 * Math.min(item.percentage, 100)) / 100}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out drop-shadow-sm"
                      />
                    </svg>
                    {/* Centered Percentage */}
                      <div className="font-bold text-textMain text-sm z-10">
                        {Math.round(item.percentage)}%
                      </div>
                    </>
                  ) : (
                    <>
                      <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                        <circle cx="40" cy="40" r="36" stroke="rgba(148, 163, 184, 0.2)" strokeWidth="6" fill="none" strokeDasharray="5 5" />
                      </svg>
                      <div className="z-10 text-textMuted flex flex-col items-center">
                        <div 
                          className="w-10 h-10 rounded-full flex items-center justify-center mb-1"
                          style={{ backgroundColor: `${item.color}1a`, color: item.color }}
                        >
                          <CategoryIcon name={item.icon} className="w-5 h-5" />
                        </div>
                      </div>
                    </>
                  )}
                </div>
                <h4 className="font-bold text-textMain text-[15px] mb-1 text-center truncate w-full">{item.category_name}</h4>
                <p className="text-xs text-textMuted font-medium">
                  {item.limit > 0 
                    ? `${formatCurrency(item.spent, currencyCode)} / ${formatCurrency(item.limit, currencyCode)}`
                    : 'Not Set'}
                </p>
              </div>
              ))}
            </div>
          </div>

        </>
      )}

      {activeTab === 'Overview' && (
        <div className="space-y-8">
          {/* Main Chart Card */}
          <div className="bg-surface rounded-3xl p-6 shadow-sm border border-border/50">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h3 className="text-xs font-bold text-textMuted uppercase tracking-widest mb-1">Monthly Spending</h3>
                <div className="text-[32px] font-extrabold text-textMain leading-tight">{formatCurrency(summary?.total_spent || 0, currencyCode)}</div>
              </div>
              {summary && summary.vs_last_month !== 0 && (
                <div className={`${summary.vs_last_month > 0 ? 'bg-red-50 text-red-500' : 'bg-green-50 text-[#00E676]'} font-bold text-xs px-2.5 py-1 rounded-md flex items-center gap-1`}>
                  {summary.vs_last_month > 0 ? '↗' : '↘'} {Math.abs(summary.vs_last_month)}%
                </div>
              )}
            </div>

            <div className="h-40 w-full ml-[-10px] mt-4">
              <ResponsiveContainer width="100%" height={160}>
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

          <div className="bg-surface rounded-3xl p-6 shadow-sm border border-border/50">
            <h3 className="text-xl font-bold text-textMain mb-6">Top Spending Categories</h3>
            {budgetItems.filter(b => b.spent > 0).length === 0 ? (
              <div className="py-10 text-center text-textMuted">No spending data yet.</div>
            ) : (
                <div className="space-y-6">
                    {budgetItems.filter(b => b.spent > 0).sort((a,b) => b.spent - a.spent).slice(0, 5).map(item => (
                        <div key={item.category_id} className="w-full relative group cursor-pointer">
                            <div className="flex justify-between items-center mb-2.5">
                                <div className="flex items-center gap-3">
                                    <div 
                                      className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm"
                                      style={{ backgroundColor: `${item.color}1a`, color: item.color }}
                                    >
                                        <CategoryIcon name={item.icon} className="w-5 h-5" />
                                    </div>
                                    <span className="font-bold text-[15px] text-textMain group-hover:text-primary transition-colors">{item.category_name}</span>
                                </div>
                                <div className="text-right">
                                    <span className="font-extrabold text-[15px] text-textMain block mb-0.5">{formatCurrency(item.spent, currencyCode)}</span>
                                    {item.limit > 0 && <span className="text-[11px] text-textMuted font-bold uppercase tracking-wide">{Math.round((item.spent / item.limit)*100)}% of limit</span>}
                                </div>
                            </div>
                            <div className="w-full h-2.5 bg-border/40 rounded-full overflow-hidden relative">
                                <div 
                                    className={`h-full rounded-full transition-all duration-1000 ease-out relative z-10 ${item.limit > 0 ? ((item.spent / item.limit) > 0.85 ? 'bg-red-500' : (item.spent / item.limit) > 0.50 ? 'bg-amber-400' : 'bg-[#00E676]') : 'bg-[#00E676]'}`}
                                    style={{ 
                                        width: item.limit > 0 ? `${Math.min((item.spent / item.limit)*100, 100)}%` : '100%'
                                    }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'Insights' && (
        <div className="space-y-6">
           <div className="flex justify-between items-center px-1">
              <h3 className="text-xl font-bold text-textMain">AI Financial Advisor</h3>
              <button 
                onClick={generateAIInsights} 
                disabled={generatingInsights} 
                className="bg-primary hover:opacity-90 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md transition disabled:opacity-50 flex items-center gap-2"
              >
                 {generatingInsights ? 'Analyzing Data...' : 'Generate Insights'}
              </button>
           </div>
           
           {aiInsights.length === 0 && !generatingInsights && (
              <div className="bg-surface rounded-3xl p-10 border border-border/50 text-center flex flex-col items-center">
                 <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-4 shadow-inner">
                    <AlertCircle className="w-8 h-8" />
                 </div>
                 <h4 className="text-lg font-bold text-textMain mb-2">Ready to Analyze</h4>
                 <p className="text-textMuted max-w-sm">Tap the generate button above to securely analyze your recent transactions and receive highly personalized financial advice.</p>
              </div>
           )}

           {generatingInsights && (
              <div className="space-y-4">
                 {[1,2,3].map(i => (
                   <div key={i} className="bg-surface rounded-3xl p-6 border border-border/50 shadow-sm animate-pulse">
                     <div className="h-6 bg-border rounded w-1/3 mb-4"></div>
                     <div className="h-4 bg-border rounded w-full mb-2"></div>
                     <div className="h-4 bg-border rounded w-5/6"></div>
                   </div>
                 ))}
              </div>
           )}
           
           {!generatingInsights && aiInsights.length > 0 && (
             <div className="grid gap-4">
                {aiInsights.map((insight, idx) => (
                   <div key={idx} className="bg-surface rounded-3xl p-6 shadow-sm border border-border/50 hover:shadow-md transition">
                      <div className="flex items-center gap-3 mb-3">
                         <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${insight.type === 'praise' || insight.type === 'positive' || insight.title.includes('Excellent') || insight.title.includes('Down') ? 'bg-[#00E676]/10 text-[#00E676]' : insight.type === 'optimization' || insight.title.includes('Velocity') || insight.title.includes('Splurge') ? 'bg-amber-500/10 text-amber-500' : 'bg-red-500/10 text-red-500'}`}>
                           <AlertCircle className="w-5 h-5" />
                         </div>
                         <h4 className="font-bold text-textMain text-lg">{insight.title}</h4>
                      </div>
                      <p className="text-textMuted text-[15px] leading-relaxed pl-13">{insight.message}</p>
                   </div>
                ))}
             </div>
           )}
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
