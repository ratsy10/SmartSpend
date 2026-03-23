import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, FileImage, PenLine, ChevronRight, Loader2, StopCircle } from 'lucide-react';
import ReceiptUpload from '../components/ReceiptUpload';
import type { ExpenseData } from '../components/ExpenseReviewCard';
import ExpenseReviewCard from '../components/ExpenseReviewCard';
import { api } from '../lib/api';
import { format } from 'date-fns';
import { useAuthStore } from '../store/useAuthStore';
import { formatCurrency, getCurrencySymbol } from '../lib/utils';
import { useVoiceRecognition } from '../hooks/useVoiceRecognition';

type LayoutState = 'overview' | 'receipt' | 'manual' | 'voice_review';

export default function AddExpense() {
  const [activeTab, setActiveTab] = useState<LayoutState>('overview');
  const [recentScans, setRecentScans] = useState<any[]>([]);
  
  const { isListening, transcript, startListening, stopListening } = useVoiceRecognition();
  const [voicePhase, setVoicePhase] = useState<'idle' | 'listening' | 'processing'>('idle');
  const [parsedVoiceData, setParsedVoiceData] = useState<ExpenseData | null>(null);
  const transcriptRef = useRef(transcript);

  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const currencyCode = user?.currency || 'USD';

  // Keep transcript ref in sync for timeouts
  useEffect(() => { transcriptRef.current = transcript; }, [transcript]);

  useEffect(() => {
    async function fetchScans() {
      try {
        const { data } = await api.get('/expenses?limit=25');
        // Handle pagination dictionary from backend
        const items = Array.isArray(data.data) ? data.data : (Array.isArray(data.items) ? data.items : (Array.isArray(data) ? data : []));
        const scans = items.filter((exp: any) => !!exp.receipt_url).slice(0, 5);
        setRecentScans(scans);
      } catch (err) {
        console.error("Failed to fetch recent scans", err);
      }
    }
    if (user && activeTab === 'overview') {
      fetchScans();
    }
  }, [user, activeTab]);

  const handleMicClick = () => {
    if (voicePhase === 'idle') {
      startListening();
      setVoicePhase('listening');
    } else if (voicePhase === 'listening') {
      stopListening();
      const finalTranscript = transcriptRef.current;
      handleProcessVoice(finalTranscript);
    }
  };

  // Auto-process when recognition ends naturally 
  useEffect(() => {
    if (voicePhase === 'listening' && !isListening) {
      const finalTranscript = transcriptRef.current;
      handleProcessVoice(finalTranscript);
    }
  }, [isListening, voicePhase]);

  const handleProcessVoice = async (finalTranscript: string) => {
    if (!finalTranscript || !finalTranscript.trim()) {
      setVoicePhase('idle');
      return;
    }
    
    setVoicePhase('processing');
    try {
      const formData = new FormData();
      formData.append('transcript', finalTranscript);
      
      const { data } = await api.post('/expenses/parse-voice', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      setParsedVoiceData(data);
      setVoicePhase('idle');
      setActiveTab('voice_review'); // Switch to review tab
    } catch (err) {
      console.error(err);
      alert('Failed to parse voice input');
      setVoicePhase('idle');
    }
  };

  const handleVoiceDataSave = async (finalData: ExpenseData) => {
    try {
      await api.post('/expenses', {
        amount: finalData.amount,
        currency: finalData.currency,
        category_id: finalData.category_id,
        description: finalData.description,
        merchant: finalData.merchant,
        expense_date: finalData.expense_date,
        input_method: "voice",
        ai_confidence: finalData.confidence
      });
      navigate('/');
    } catch (err) {
      alert('Failed to save expense');
    }
  };

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
            <h1 className="text-[28px] font-bold text-textMain tracking-tight mb-2">SmartSpend AI</h1>
            <p className="text-textMuted text-[15px] px-4 leading-relaxed">
              How would you like to track your expense today?
            </p>
          </div>

          <div className="flex flex-col items-center justify-center mb-12 mt-4">
            <div className="relative">
              {voicePhase === 'listening' && (
                <div className="absolute inset-0 bg-red-500 rounded-full animate-ping opacity-30"></div>
              )}
              {voicePhase === 'processing' && (
                <div className="absolute inset-0 bg-[#00E676] rounded-full animate-pulse opacity-50"></div>
              )}
              <button 
                onClick={handleMicClick}
                disabled={voicePhase === 'processing'}
                className={`relative w-32 h-32 rounded-full flex items-center justify-center transition-all hover:scale-105 active:scale-95 shadow-[0_8px_30px_rgb(0,230,118,0.4)] ${
                  voicePhase === 'listening' ? 'bg-red-500 hover:bg-red-600' : 'bg-[#00E676] hover:bg-[#00D16B]'
                } ${voicePhase === 'processing' ? 'opacity-70 cursor-wait' : ''}`}
              >
                <div className={`w-24 h-24 rounded-full flex items-center justify-center shadow-inner ${
                  voicePhase === 'listening' ? 'bg-red-400' : 'bg-[#33EDA2]'
                }`}>
                  {voicePhase === 'processing' ? (
                     <Loader2 className="w-12 h-12 text-[#0F172A] animate-spin" />
                  ) : voicePhase === 'listening' ? (
                    <StopCircle className="w-12 h-12 text-white" />
                  ) : (
                    <Mic className="w-12 h-12 text-[#0F172A]" />
                  )}
                </div>
              </button>
            </div>
            
            <p className="text-textMain font-bold mt-6 mb-1 text-center min-h-[24px]">
              {voicePhase === 'idle' && "Tap to speak"}
              {voicePhase === 'listening' && "Listening..."}
              {voicePhase === 'processing' && "AI is extracting data..."}
            </p>
            
            <p className="text-textMuted text-sm font-medium text-center min-h-[40px] px-4">
              {voicePhase === 'listening' && transcript ? (
                <span className="text-textMain italic">"{transcript}"</span>
              ) : voicePhase === 'idle' ? (
                `"I spent ${getCurrencySymbol(currencyCode).replace('$', '')}15 on lunch"`
              ) : (
                ""
              )}
            </p>
          </div>

          <div className="space-y-4 mb-10">
            {/* Type Card */}
            <button 
              onClick={() => setActiveTab('manual')}
              className="w-full bg-surface rounded-2xl p-4 flex items-center justify-between border border-border/60 hover:border-primary transition-colors shadow-sm text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                  <PenLine className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-textMain text-lg">Type</h3>
                  <p className="text-textMuted text-sm font-medium">Enter details manually</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-primary" />
            </button>

            {/* Scan Card */}
            <button 
              onClick={() => setActiveTab('receipt')}
              className="w-full bg-surface rounded-2xl p-4 flex items-center justify-between border border-border/60 hover:border-primary transition-colors shadow-sm text-left"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center text-primary">
                  <FileImage className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-textMain text-lg">Scan Receipt</h3>
                  <p className="text-textMuted text-sm font-medium">AI auto-extracts data</p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-primary" />
            </button>
          </div>

          {/* Recent Scans Real View */}
          {recentScans.length > 0 && (
            <div>
              <div className="flex justify-between items-center mb-4 px-1">
                <h3 className="text-[17px] font-bold text-textMain">Recent Scans</h3>
                <button onClick={() => navigate('/history')} className="text-primary text-sm font-bold hover:underline">View all</button>
              </div>
              <div className="flex gap-4 overflow-x-auto pb-4 px-1 hide-scrollbar">
                {recentScans.map((scan) => (
                  <div key={scan.id} className="bg-surface rounded-2xl p-3 min-w-[160px] border border-border/50 shadow-sm flex-shrink-0">
                    <div 
                      className="h-32 bg-background rounded-xl mb-3 relative overflow-hidden flex items-center justify-center cursor-pointer hover:opacity-90 transition-opacity"
                      onClick={() => window.open(scan.receipt_url, '_blank')}
                    >
                      <img src={scan.receipt_url} alt="Receipt preview" className="w-full h-full object-cover" />
                      <div className="absolute top-2 right-2 bg-primary text-white text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider shadow-sm">
                        Uploaded
                      </div>
                    </div>
                    <h4 className="font-bold text-textMain text-sm truncate">{scan.merchant || 'General'}</h4>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-xs text-textMuted">{format(new Date(scan.expense_date), 'MMM d')}</span>
                      <span className="text-sm font-bold text-primary">{formatCurrency(scan.amount, scan.currency)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {activeTab !== 'overview' && (
        <div className="relative min-h-[400px]">
          <button 
            onClick={() => {
              setActiveTab('overview');
              setVoicePhase('idle');
            }}
            className="mb-6 font-semibold text-textMuted hover:text-textMain flex items-center gap-1 transition-colors"
          >
            ← Back
          </button>

          {activeTab === 'voice_review' && parsedVoiceData && (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <div className="mb-6">
                 <h2 className="text-xl font-bold text-textMain mb-1">Review Details</h2>
                 <p className="text-sm text-textMuted">Does this look right?</p>
              </div>
              <ExpenseReviewCard 
                initialData={parsedVoiceData}
                onSave={handleVoiceDataSave}
                onCancel={() => {
                  setActiveTab('overview');
                  setVoicePhase('idle');
                }}
              />
            </div>
          )}

          {activeTab === 'receipt' && (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <ReceiptUpload 
                onSuccess={() => setActiveTab('overview')}
                onCancel={() => setActiveTab('overview')}
              />
            </div>
          )}

          {activeTab === 'manual' && (
            <div className="animate-in fade-in zoom-in-95 duration-300">
              <ExpenseReviewCard 
                initialData={emptyExpense}
                onSave={handleManualSave}
                onCancel={() => setActiveTab('overview')}
              />
            </div>
          )}
        </div>
      )}

    </div>
  );
}
