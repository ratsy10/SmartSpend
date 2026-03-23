import React, { useRef, useState } from 'react';
import { UploadCloud, Loader2, CheckCircle } from 'lucide-react';
import { api } from '../lib/api';
import type { ExpenseData } from './ExpenseReviewCard';
import ExpenseReviewCard from './ExpenseReviewCard';

interface ReceiptUploadProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export default function ReceiptUpload({ onSuccess, onCancel }: ReceiptUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [phase, setPhase] = useState<'idle' | 'uploading' | 'processing' | 'review' | 'success'>('idle');
  const [parsedData, setParsedData] = useState<ExpenseData | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPreviewUrl(URL.createObjectURL(file));
    
    // Auto-upload and parse
    setPhase('uploading');
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const { data } = await api.post('/expenses/parse-receipt', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setParsedData(data);
      setPhase('review');
    } catch (err) {
      console.error(err);
      alert('Failed to parse receipt');
      setPhase('idle');
    }
  };

  const handleSave = async (finalData: ExpenseData) => {
    setPhase('processing');
    try {
      await api.post('/expenses', {
        ...finalData,
        category_id: finalData.category_id,
        input_method: "receipt"
      });
      setPhase('success');
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err) {
      alert('Failed to save expense');
      setPhase('review');
    }
  };

  return (
    <div className="w-full">
      {phase === 'idle' && (
        <div 
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-primary/50 bg-primary/5 hover:bg-primary/10 transition-colors rounded-3xl p-8 flex flex-col items-center justify-center cursor-pointer min-h-[250px]"
        >
          <div className="w-16 h-16 bg-primary/20 text-primary rounded-full flex items-center justify-center mb-4">
            <UploadCloud className="w-8 h-8" />
          </div>
          <h3 className="font-semibold text-lg mb-2 text-textMain">Upload Receipt</h3>
          <p className="text-textMuted text-sm text-center">Tap to select an image from your gallery or take a picture</p>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept="image/*"
            capture="environment"
          />
        </div>
      )}

      {(phase === 'uploading' || phase === 'processing') && (
        <div className="border border-border bg-surface rounded-3xl p-8 flex flex-col items-center justify-center min-h-[250px]">
          {previewUrl && (
            <img src={previewUrl} alt="Receipt preview" className="w-32 h-32 object-cover rounded-xl mb-6 opacity-50" />
          )}
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-4" />
          <p className="text-textMuted font-medium">
            {phase === 'uploading' ? 'Extracting text using AI...' : 'Saving your expense...'}
          </p>
        </div>
      )}

      {phase === 'review' && parsedData && (
        <div>
          <div className="flex justify-between items-center mb-6 px-2">
            <h3 className="font-semibold text-lg">Review Details</h3>
            <button onClick={onCancel} className="text-sm text-textMuted hover:text-textMain">Cancel</button>
          </div>
          <ExpenseReviewCard 
            initialData={parsedData}
            onSave={handleSave}
            onCancel={onCancel}
          />
        </div>
      )}

      {phase === 'success' && (
        <div className="border border-border bg-surface rounded-3xl p-8 flex flex-col items-center justify-center min-h-[250px] text-success">
          <CheckCircle className="w-16 h-16 mb-4" />
          <h3 className="font-semibold text-xl">Receipt logged!</h3>
        </div>
      )}
    </div>
  );
}
