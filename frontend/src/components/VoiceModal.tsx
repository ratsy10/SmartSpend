import { useState, useEffect, useRef } from 'react';
import { Mic, X, CheckCircle, Loader2 } from 'lucide-react';
import { useVoiceRecognition } from '../hooks/useVoiceRecognition';
import { api } from '../lib/api';
import type { ExpenseData } from './ExpenseReviewCard';
import ExpenseReviewCard from './ExpenseReviewCard';

interface VoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function VoiceModal({ isOpen, onClose, onSuccess }: VoiceModalProps) {
  const { isListening, transcript, startListening, stopListening, hasSupport } = useVoiceRecognition();
  
  const [phase, setPhase] = useState<'idle' | 'listening' | 'processing' | 'review' | 'success'>('idle');
  const [parsedData, setParsedData] = useState<ExpenseData | null>(null);
  const transcriptRef = useRef(transcript);
  const phaseRef = useRef(phase);

  // Keep refs in sync
  useEffect(() => { transcriptRef.current = transcript; }, [transcript]);
  useEffect(() => { phaseRef.current = phase; }, [phase]);

  useEffect(() => {
    if (isOpen) {
      setPhase('idle');
      setParsedData(null);
    }
  }, [isOpen]);

  const handleMicClick = () => {
    if (phase === 'idle') {
      startListening();
      setPhase('listening');
    } else if (phase === 'listening') {
      stopListening();
      // Give a short delay for the final transcript to settle
      setTimeout(() => {
        const finalTranscript = transcriptRef.current;
        if (finalTranscript && finalTranscript.trim()) {
          handleProcessVoice(finalTranscript);
        } else {
          setPhase('idle');
        }
      }, 300);
    }
  };
  
  // Auto-process when recognition ends naturally (silence timeout)
  useEffect(() => {
    if (phaseRef.current === 'listening' && !isListening) {
      // Recognition ended on its own - give a small delay for state to settle
      setTimeout(() => {
        const finalTranscript = transcriptRef.current;
        if (finalTranscript && finalTranscript.trim() && phaseRef.current === 'listening') {
          handleProcessVoice(finalTranscript);
        } else if (phaseRef.current === 'listening') {
          setPhase('idle');
        }
      }, 300);
    }
  }, [isListening]);

  const handleProcessVoice = async (finalTranscript: string) => {
    if (!finalTranscript.trim()) return;
    
    console.log('[VoiceModal] Sending transcript to AI:', finalTranscript);
    setPhase('processing');
    try {
      const formData = new FormData();
      formData.append('transcript', finalTranscript);
      
      const { data } = await api.post('/expenses/parse-voice', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      console.log('[VoiceModal] AI response:', data);
      setParsedData(data);
      setPhase('review');
    } catch (err) {
      console.error(err);
      alert('Failed to parse voice input');
      setPhase('idle');
    }
  };

  const handleSave = async (finalData: ExpenseData) => {
    setPhase('processing');
    try {
      await api.post('/expenses', {
        amount: finalData.amount,
        currency: finalData.currency,
        categoryUrl: null,
        category_id: finalData.category_id,
        description: finalData.description,
        merchant: finalData.merchant,
        expense_date: finalData.expense_date,
        notes: finalData.notes,
        input_method: "voice",
        transcript: transcript
      });
      setPhase('success');
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
    } catch (err) {
      console.error(err);
      alert('Failed to save expense');
      setPhase('review');
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] transition-opacity" onClick={onClose} />
      
      <div className="fixed bottom-0 left-0 w-full bg-surface z-[101] rounded-t-3xl shadow-2xl overflow-hidden transition-transform transform translate-y-0 max-h-[90vh] overflow-y-auto pb-safe">
        <div className="flex justify-between items-center p-4 border-b border-border/50">
          <h3 className="text-lg font-semibold">Voice Input</h3>
          <button onClick={onClose} className="p-2 bg-background rounded-full hover:bg-black/5 transition">
            <X className="w-5 h-5 text-textMuted" />
          </button>
        </div>

        <div className="p-6">
          {!hasSupport && (
            <div className="p-4 bg-danger/20 text-danger rounded-xl">
              Speech recognition is not supported in this browser. Please use text input.
            </div>
          )}

          {(phase === 'idle' || phase === 'listening') && hasSupport && (
            <div className="flex flex-col items-center justify-center py-10">
              <button 
                onClick={handleMicClick}
                className={`w-24 h-24 rounded-full flex items-center justify-center text-white transition-all ${
                  phase === 'listening' 
                    ? 'bg-danger shadow-[0_0_50px_rgba(239,68,68,0.6)] animate-pulse scale-110' 
                    : 'bg-primary shadow-[0_0_30px_rgba(163,230,53,0.3)] hover:scale-105'
                }`}
              >
                <Mic className="w-10 h-10" />
              </button>
              
              <p className="mt-8 text-xl font-medium text-textMain min-h-[2rem] text-center max-w-xs">
                {phase === 'listening' ? (transcript || 'Listening...') : 'Tap to speak'}
              </p>
              
              <p className="mt-4 text-sm text-textMuted text-center max-w-xs">
                Try saying: "I spent 15 dollars on lunch at Subway"
              </p>
            </div>
          )}

          {phase === 'processing' && (
            <div className="flex flex-col items-center justify-center py-16 text-textMuted">
              <Loader2 className="w-12 h-12 mb-4 animate-spin text-primary" />
              <p>Extracting details with AI...</p>
            </div>
          )}

          {phase === 'review' && parsedData && (
            <ExpenseReviewCard 
              initialData={parsedData} 
              onSave={handleSave} 
              onCancel={() => setPhase('idle')} 
            />
          )}

          {phase === 'success' && (
            <div className="flex flex-col items-center justify-center py-16 text-success">
              <CheckCircle className="w-20 h-20 mb-6" />
              <h2 className="text-2xl font-bold">Expense Saved!</h2>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
