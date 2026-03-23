import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { format } from 'date-fns';
import { Filter, Search } from 'lucide-react';
import { formatCurrency } from '../lib/utils';
import CategoryIcon from '../components/CategoryIcon';

interface Expense {
  id: string;
  amount: number;
  currency: string;
  category: { id: string, name: string, icon: string, color: string };
  merchant?: string;
  expense_date: string;
  description?: string;
}

export default function TransactionHistory() {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchExpenses = async (pageNum: number, isInitial = false) => {
    if (isInitial) setLoading(true);
    else setLoadingMore(true);

    try {
      const { data } = await api.get(`/expenses?limit=30&page=${pageNum}`);
      const newExpenses = data.data || data.items || [];
      
      if (isInitial) {
        setExpenses(newExpenses);
      } else {
        setExpenses(prev => [...prev, ...newExpenses]);
      }
      setHasMore(pageNum < data.pages);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') return;
      console.error("Failed to fetch expenses", err);
    } finally {
      if (isInitial) setLoading(false);
      else setLoadingMore(false);
    }
  };

  useEffect(() => {
    fetchExpenses(1, true);
  }, []);

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchExpenses(nextPage, false);
    }
  };

  const filteredExpenses = expenses.filter(exp => 
    exp.merchant?.toLowerCase().includes(search.toLowerCase()) || 
    exp.category.name.toLowerCase().includes(search.toLowerCase()) ||
    exp.description?.toLowerCase().includes(search.toLowerCase())
  );

  // Group by date
  const grouped = filteredExpenses.reduce((acc, exp) => {
    const dateStr = format(new Date(exp.expense_date), 'yyyy-MM-dd');
    if (!acc[dateStr]) acc[dateStr] = [];
    acc[dateStr].push(exp);
    return acc;
  }, {} as Record<string, Expense[]>);

  const sortedDates = Object.keys(grouped).sort((a, b) => new Date(b).getTime() - new Date(a).getTime());

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-4">Transactions</h1>
        
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-5 w-5 text-textMuted" />
            <input 
              type="text" 
              placeholder="Search merchants, categories..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            />
          </div>
          <button className="bg-surface border border-border rounded-xl p-2.5 text-textMuted hover:text-textMain transition">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </header>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
        </div>
      ) : sortedDates.length === 0 ? (
        <div className="text-center py-20 text-textMuted">
          No transactions found.
        </div>
      ) : (
        <div className="space-y-6">
          {sortedDates.map(date => (
            <div key={date}>
              <h3 className="text-sm font-semibold text-textMuted uppercase tracking-wider mb-3 px-2">
                {format(new Date(date), 'MMMM dd, yyyy')}
              </h3>
              <div className="bg-surface border border-border/50 rounded-2xl overflow-hidden">
                {grouped[date].map((exp, idx) => (
                  <div 
                    key={exp.id} 
                    className={`p-4 flex items-center justify-between hover:bg-black/5 transition cursor-pointer ${
                      idx !== grouped[date].length - 1 ? 'border-b border-border' : ''
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div 
                        className="w-12 h-12 rounded-xl flex items-center justify-center text-xl"
                        style={{ backgroundColor: `${exp.category.color}1a`, color: exp.category.color }}
                      >
                        <CategoryIcon name={exp.category.icon} className="w-6 h-6" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-textMain">{exp.merchant || exp.category.name}</h4>
                        {exp.description && (
                          <p className="text-xs text-textMuted truncate max-w-[150px]">{exp.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="font-bold text-textMain">
                      {formatCurrency(exp.amount, exp.currency)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          
          {hasMore && (
            <div className="pt-4 pb-8 flex justify-center">
              <button 
                onClick={loadMore}
                disabled={loadingMore}
                className="bg-surface border border-border/50 text-textMain px-6 py-3 rounded-xl font-semibold shadow-sm hover:opacity-80 transition disabled:opacity-50"
              >
                {loadingMore ? 'Loading...' : 'Load More Transactions'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
