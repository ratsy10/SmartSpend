import { useState, useEffect } from 'react';
import { Calendar, Tag, FileText, Store } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { getCurrencySymbol } from '../lib/utils';

export interface ExpenseData {
  amount: number | string;
  currency: string;
  category: string;
  category_id?: string; // Newly added
  description: string;
  merchant?: string;
  expense_date: string;
  notes?: string;
  confidence?: number;
}

interface ExpenseReviewCardProps {
  initialData: ExpenseData;
  onSave: (data: ExpenseData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function ExpenseReviewCard({ initialData, onSave, onCancel, isLoading }: ExpenseReviewCardProps) {
  const [data, setData] = useState<ExpenseData>(initialData);
  const [categories, setCategories] = useState<{id: string, name: string}[]>([]);
  const user = useAuthStore(state => state.user);

  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  useEffect(() => {
    import('../lib/api').then(({ api }) => {
      api.get('/categories').then(res => setCategories(res.data)).catch(console.error);
    });
  }, []);

  const handleChange = (field: keyof ExpenseData, value: string | number) => {
    setData(prev => ({ ...prev, [field]: value }));
  };

  const handleSaveWrapper = () => {
    let category_id = categories.find(c => c.name === data.category)?.id;
    if (!category_id && categories.length > 0) {
       category_id = categories.find(c => c.name === 'Miscellaneous')?.id || categories[0].id;
    }
    onSave({ ...data, category_id });
  };

  const isLowConfidence = data.confidence !== undefined && data.confidence < 0.7;

  return (
    <div className="bg-surface rounded-3xl p-6 shadow-xl border border-border">
      {isLowConfidence && (
        <div className="mb-4 bg-danger/20 border border-danger text-danger px-4 py-2 rounded-xl text-sm font-medium">
          Please verify the details. Some fields might be inaccurate.
        </div>
      )}

      <div className="flex flex-col items-center mb-6">
        <span className="text-textMuted text-sm mb-1 uppercase tracking-wider font-semibold">Amount</span>
        <div className="flex items-center gap-1 text-4xl font-bold text-textMain">
          <span className="text-primary">{data.currency ? getCurrencySymbol(data.currency) : getCurrencySymbol(user?.currency || 'USD')}</span>
          <input 
            type="number"
            value={data.amount}
            onChange={(e) => handleChange('amount', parseFloat(e.target.value) || 0)}
            className="w-32 bg-transparent border-b-2 border-transparent hover:border-border focus:border-primary outline-none text-center appearance-none"
            min="0"
            step="0.01"
            placeholder="0.00"
          />
        </div>
      </div>

      <div className="space-y-4">
        {/* Category */}
        <div className="flex items-center gap-3 bg-background p-3 rounded-xl border border-border focus-within:ring-2 focus-within:ring-primary">
          <Tag className="w-5 h-5 text-textMuted" />
          <select 
            value={data.category} 
            onChange={(e) => handleChange('category', e.target.value)}
            className="flex-1 bg-transparent outline-none text-textMain appearance-none"
          >
            {categories.map(cat => (
              <option key={cat.id} value={cat.name} className="bg-surface">{cat.name}</option>
            ))}
          </select>
        </div>

        {/* Merchant */}
        <div className="flex items-center gap-3 bg-background p-3 rounded-xl border border-border focus-within:ring-2 focus-within:ring-primary">
          <Store className="w-5 h-5 text-textMuted" />
          <input 
            type="text" 
            placeholder="Merchant (Optional)"
            value={data.merchant || ''}
            onChange={(e) => handleChange('merchant', e.target.value)}
            className="flex-1 bg-transparent outline-none text-textMain"
          />
        </div>

        {/* Date */}
        <div className="flex items-center gap-3 bg-background p-3 rounded-xl border border-border focus-within:ring-2 focus-within:ring-primary">
          <Calendar className="w-5 h-5 text-textMuted" />
          <input 
            type="date" 
            value={data.expense_date}
            onChange={(e) => handleChange('expense_date', e.target.value)}
            className="flex-1 bg-transparent outline-none text-textMain"
          />
        </div>

        {/* Notes/Description */}
        <div className="flex items-start gap-3 bg-background p-3 rounded-xl border border-border focus-within:ring-2 focus-within:ring-primary">
          <FileText className="w-5 h-5 text-textMuted mt-1" />
          <textarea 
            placeholder="Description or notes"
            value={data.description || ''}
            onChange={(e) => handleChange('description', e.target.value)}
            className="flex-1 bg-transparent outline-none text-textMain resize-none h-16"
          />
        </div>
      </div>

      <div className="flex gap-3 mt-8">
        <button 
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 py-3 rounded-xl border border-border text-textMain font-semibold hover:bg-background transition disabled:opacity-50"
        >
          Cancel
        </button>
        <button 
          onClick={handleSaveWrapper}
          disabled={isLoading || categories.length === 0}
          className="flex-1 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition shadow-lg shadow-primary/20 disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : 'Save Expense'}
        </button>
      </div>
    </div>
  );
}
