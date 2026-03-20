import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, FileImage, PenLine, ChevronRight } from 'lucide-react';
import VoiceModal from '../components/VoiceModal';
import ReceiptUpload from '../components/ReceiptUpload';
import type { ExpenseData } from '../components/ExpenseReviewCard';
import ExpenseReviewCard from '../components/ExpenseReviewCard';
import { api } from '../lib/api';
import { format } from 'date-fns';
import { useAuthStore } from '../store/useAuthStore';
import { formatCurrency, getCurrencySymbol } from '../lib/utils';

type LayoutState = 'overview' | 'voice' | 'receipt' | 'manual';

export default function AddExpense() {
  const [activeTab, setActiveTab] = useState<LayoutState>('overview');
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const currencyCode = user?.currency || 'USD';

  const handleManualSave = async (data: ExpenseData) => {
    try {
      await api.post('/expenses', {
        ...data,
        category_id: data.category_id,
        input_method: "manual"
      });
      navigate('/');
    } catch (err) {
      alert("Failed to save manual expense");
    }
  };

  const emptyExpense: ExpenseData = {
    amount: '',
    currency: currencyCode,
    category: 'Food',
    description: '',
    merchant: '',
    expense_date: format(new Date(), 'yyyy-MM-dd')
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10 mt-6">
      
      {activeTab === 'overview' && (
        <>
          <div className="text-center mb-10">
            <h1 className="text-[28px] font-bold text-[#0F172A] tracking-tight mb-2">SmartSpend AI</h1>
            <p className="text-slate-500 text-[15px] px-4 leading-relaxed">
              How would you like to track your expense today?
            </p>
          </div>

          <div className="space-y-4 mb-10">
            {/* Speak Card */}
            <button 
              onClick={() => setIsVoiceModalOpen(true)}
              className="w-full bg-[#00E676] hover:bg-[#00D16B] rounded-2xl p-4 flex items-center justify-between transition-colors shadow-sm text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-[#33EDA2] rounded-xl flex items-center justify-center text-[#0F172A] shadow-inner">
                  <Mic className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-[#0F172A] text-lg">Speak</h3>
                  <p className="text-[#0F172A]/70 text-sm font-medium">"I spent {getCurrencySymbol(currencyCode).replace('$', '')}12 on coffee"</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#0F172A]" />
            </button>

            {/* Type Card */}
            <button 
              onClick={() => setActiveTab('manual')}
              className="w-full bg-white rounded-2xl p-4 flex items-center justify-between border border-emerald-100 hover:border-[#00E676] transition-colors shadow-sm text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-[#E6F9EC] rounded-xl flex items-center justify-center text-[#00E676]">
                  <PenLine className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-[#0F172A] text-lg">Type</h3>
                  <p className="text-slate-400 text-sm font-medium">Enter details manually</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#00E676]" />
            </button>

            {/* Scan Card */}
            <button 
              onClick={() => setActiveTab('receipt')}
              className="w-full bg-white rounded-2xl p-4 flex items-center justify-between border border-emerald-100 hover:border-[#00E676] transition-colors shadow-sm text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-[#E6F9EC] rounded-xl flex items-center justify-center text-[#00E676]">
                  <FileImage className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-[#0F172A] text-lg">Scan Receipt</h3>
                  <p className="text-slate-400 text-sm font-medium">AI auto-extracts data</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-[#00E676]" />
            </button>
          </div>

          {/* Recent Scans Dummy View */}
          <div>
            <div className="flex justify-between items-center mb-4 px-1">
              <h3 className="text-[17px] font-bold text-[#0F172A]">Recent Scans</h3>
              <button className="text-[#00E676] text-sm font-bold hover:underline">View all</button>
            </div>
            <div className="flex gap-4 overflow-x-auto pb-4 px-1 hide-scrollbar">
              {/* Scan 1 */}
              <div className="bg-white rounded-2xl p-3 min-w-[160px] border border-slate-100 shadow-sm">
                <div className="h-32 bg-[#EBBBAC] rounded-xl mb-3 relative overflow-hidden flex items-center justify-center">
                  <div className="w-16 h-24 bg-white opacity-80 shadow-md transform rotate-2"></div>
                  <div className="absolute top-2 right-2 bg-[#00E676] text-[#0F172A] text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                    Processed
                  </div>
                </div>
                <h4 className="font-bold text-[#0F172A] text-sm truncate">Whole Foods M...</h4>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-slate-400">Oct 24</span>
                  <span className="text-sm font-bold text-[#00E676]">{formatCurrency(42.50, currencyCode)}</span>
                </div>
              </div>

              {/* Scan 2 */}
              <div className="bg-white rounded-2xl p-3 min-w-[160px] border border-slate-100 shadow-sm">
                <div className="h-32 bg-[#EABFB9] rounded-xl mb-3 relative overflow-hidden flex items-center justify-center">
                  <div className="w-16 h-28 bg-white opacity-90 shadow-md transform -rotate-1"></div>
                  <div className="absolute top-2 right-2 bg-[#A7F3D0] text-[#047857] text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                    Draft
                  </div>
                </div>
                <h4 className="font-bold text-[#0F172A] text-sm truncate">Blue Bottle Cof...</h4>
                <div className="flex justify-between items-center mt-1">
                  <span className="text-xs text-slate-400">Oct 23</span>
                  <span className="text-sm font-bold text-[#00E676]">{formatCurrency(8.75, currencyCode)}</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {activeTab !== 'overview' && (
        <div className="relative min-h-[400px]">
          <button 
            onClick={() => setActiveTab('overview')}
            className="mb-6 font-semibold text-slate-500 hover:text-[#0F172A] flex items-center gap-1"
          >
            ← Back
          </button>

          {activeTab === 'voice' && (
            <div className="flex flex-col items-center justify-center p-8 bg-surface border border-slate-100 rounded-3xl min-h-[300px] shadow-sm">
              <div className="w-20 h-20 bg-[#E6F9EC] text-[#00E676] rounded-full flex items-center justify-center mb-6 shadow-inner">
                <Mic className="w-10 h-10" />
              </div>
              <h3 className="text-xl font-bold text-[#0F172A] mb-2">Speak your expense</h3>
              <p className="text-slate-400 text-center text-sm mb-8">
                "I spent 15 dollars on lunch at Subway"
              </p>
              <button 
                onClick={() => setIsVoiceModalOpen(true)}
                className="w-full max-w-[200px] flex items-center justify-center gap-2 bg-[#00E676] hover:bg-[#00D16B] text-[#0F172A] font-bold py-4 rounded-xl transition shadow-sm"
              >
                Start Recording
              </button>
            </div>
          )}

          {activeTab === 'receipt' && (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <ReceiptUpload 
                onSuccess={() => navigate('/')}
                onCancel={() => setActiveTab('manual')}
              />
            </div>
          )}

          {activeTab === 'manual' && (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <ExpenseReviewCard 
                initialData={emptyExpense}
                onSave={handleManualSave}
                onCancel={() => navigate('/')}
              />
            </div>
          )}
        </div>
      )}

      <VoiceModal 
        isOpen={isVoiceModalOpen} 
        onClose={() => setIsVoiceModalOpen(false)} 
        onSuccess={() => navigate('/')} 
      />
    </div>
  );
}
