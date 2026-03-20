import { useState, useEffect } from 'react';
import { X, Save, BellRing } from 'lucide-react';
import { api } from '../lib/api';
import { useAuthStore } from '../store/useAuthStore';
import { getCurrencySymbol } from '../lib/utils';

interface Category {
  id: string;
  name: string;
}

interface AddBudgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialData?: {
    categoryId: string;
    budgetId?: string;
    limit: number;
  } | null;
}

export default function AddBudgetModal({ isOpen, onClose, onSuccess, initialData }: AddBudgetModalProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState<string>('');
  const [amount, setAmount] = useState<number | string>('');
  const [alert80, setAlert80] = useState(true);
  const [alert100, setAlert100] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const user = useAuthStore(state => state.user);

  useEffect(() => {
    if (isOpen) {
      api.get('/categories').then(res => {
        setCategories(res.data);
        if (initialData?.categoryId) {
          setCategoryId(initialData.categoryId);
        } else if (res.data.length > 0) {
          setCategoryId(res.data[0].id);
        }
      }).catch(console.error);
      
      if (initialData?.limit) {
        setAmount(initialData.limit);
      } else {
        setAmount('');
      }
      setAlert80(true);
      setAlert100(true);
    }
  }, [isOpen, initialData]);

  const handleSave = async () => {
    if (!amount || !categoryId) return;
    setIsSubmitting(true);
    try {
      const payload = {
        category_id: categoryId,
        monthly_limit: Number(amount),
        alert_at_80: alert80,
        alert_at_100: alert100
      };
      
      if (initialData?.budgetId) {
        await api.put(`/budgets/${initialData.budgetId}`, payload);
      } else {
        await api.post('/budgets', payload);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to save budget');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] transition-opacity" onClick={onClose} />
      
      <div className="fixed bottom-0 left-0 w-full bg-surface z-[101] rounded-t-3xl shadow-2xl overflow-hidden transition-transform max-h-[90vh] overflow-y-auto pb-24">
        <div className="flex justify-between items-center p-4 border-b border-border/50">
          <h3 className="text-lg font-semibold">New Budget</h3>
          <button onClick={onClose} className="p-2 bg-background rounded-full hover:bg-black/5 transition">
            <X className="w-5 h-5 text-textMuted" />
          </button>
        </div>

        <div className="p-6">
          <div className="space-y-6">
            
            {/* Amount */}
            <div className="flex flex-col items-center">
              <span className="text-textMuted text-sm mb-1 uppercase tracking-wider font-semibold">Monthly Limit</span>
              <div className="flex items-center gap-1 text-4xl font-bold text-textMain">
                <span className="text-primary">{getCurrencySymbol(user?.currency || 'USD')}</span>
                <input 
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(parseFloat(e.target.value))}
                  className="w-32 bg-transparent border-b-2 border-transparent hover:border-border focus:border-primary outline-none text-center appearance-none"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                />
              </div>
            </div>

            {/* Category Dropdown */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-textMain px-1">Category</label>
              <div className="bg-background p-3 rounded-xl border border-border focus-within:ring-2 focus-within:ring-primary flex items-center">
                <select 
                  value={categoryId} 
                  onChange={(e) => setCategoryId(e.target.value)}
                  disabled={!!initialData?.categoryId}
                  className="w-full bg-transparent outline-none text-textMain appearance-none disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id} className="bg-surface">{cat.name}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Alerts */}
            <div className="space-y-3 pt-2">
              <label className="text-sm font-semibold text-textMain px-1 flex items-center gap-2">
                <BellRing className="w-4 h-4 text-textMuted" /> Notifications
              </label>
              <label className="flex items-center justify-between p-3 bg-background rounded-xl border border-border cursor-pointer">
                <span className="text-sm font-medium">Alert at 80% usage</span>
                <input type="checkbox" checked={alert80} onChange={e => setAlert80(e.target.checked)} className="w-5 h-5 accent-primary" />
              </label>
              <label className="flex items-center justify-between p-3 bg-background rounded-xl border border-border cursor-pointer">
                <span className="text-sm font-medium">Alert at 100% usage</span>
                <input type="checkbox" checked={alert100} onChange={e => setAlert100(e.target.checked)} className="w-5 h-5 accent-primary" />
              </label>
            </div>

            <button 
              onClick={handleSave}
              disabled={isSubmitting || !amount || parseFloat(String(amount)) <= 0}
              className="w-full py-3.5 rounded-xl bg-primary text-primary-foreground flex items-center justify-center gap-2 font-bold text-lg hover:opacity-90 transition shadow-lg shadow-primary/20 disabled:opacity-50 mt-4"
            >
              <Save className="w-5 h-5" />
              {isSubmitting ? 'Saving...' : 'Save Budget'}
            </button>

          </div>
        </div>
      </div>
    </>
  );
}
