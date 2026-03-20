import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuthStore } from '../store/useAuthStore';
import { ArrowRight, Check, DollarSign, Bell, PieChart } from 'lucide-react';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [currency, setCurrency] = useState('USD');
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [reminderTime, setReminderTime] = useState('20:00');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const { updateUser } = useAuthStore();

  const handleNext = async () => {
    if (step < 3) {
      setStep(step + 1);
      return;
    }
    
    // Final step: Save to backend
    setLoading(true);
    try {
      await api.put('/auth/me', {
        currency,
        reminder_enabled: reminderEnabled,
        reminder_time: `${reminderTime}:00` // backend might expect HH:MM:SS
      });
      
      updateUser({ currency });
      navigate('/');
    } catch (err) {
      console.error('Failed to save onboarding data', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-lg bg-surface p-8 rounded-3xl shadow-xl relative overflow-hidden">
        {/* Progress Bar */}
        <div className="absolute top-0 left-0 w-full flex h-2 bg-border">
          <div 
            className="bg-primary h-full transition-all duration-300 ease-in-out" 
            style={{ width: `${(step / 3) * 100}%` }}
          ></div>
        </div>

        <div className="mt-4 mb-8">
          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6">
                <DollarSign className="w-8 h-8" />
              </div>
              <h2 className="text-3xl font-bold mb-4">Choose your currency</h2>
              <p className="text-textMuted mb-8">SmartSpend tracks all your expenses in your preferred currency.</p>
              
              <div className="grid grid-cols-2 gap-4">
                {['USD', 'EUR', 'GBP', 'INR', 'AUD', 'CAD'].map(cur => (
                  <button
                    key={cur}
                    onClick={() => setCurrency(cur)}
                    className={`py-4 rounded-xl border-2 transition text-lg font-medium tracking-wide flex items-center justify-center gap-2 ${
                      currency === cur ? 'border-primary bg-primary/10 text-primary' : 'border-border text-textMuted hover:border-textMuted'
                    }`}
                  >
                    {cur} 
                    {currency === cur && <Check className="w-5 h-5" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6">
                <Bell className="w-8 h-8" />
              </div>
              <h2 className="text-3xl font-bold mb-4">Daily Reminders</h2>
              <p className="text-textMuted mb-8">Want a gentle nudge to log your expenses at the end of the day?</p>
              
              <div className="space-y-6">
                <label className="flex items-center justify-between p-4 border border-border rounded-xl cursor-pointer hover:bg-black/5 transition">
                  <span className="font-medium text-lg">Enable daily reminder</span>
                  <input 
                    type="checkbox" 
                    className="w-6 h-6 rounded text-primary accent-primary" 
                    checked={reminderEnabled}
                    onChange={(e) => setReminderEnabled(e.target.checked)}
                  />
                </label>
                
                {reminderEnabled && (
                  <div className="p-4 border border-border rounded-xl animate-in slide-in-from-top-2">
                    <label className="block text-textMuted mb-2">What time works best?</label>
                    <input 
                      type="time" 
                      value={reminderTime}
                      onChange={(e) => setReminderTime(e.target.value)}
                      className="w-full bg-background border border-border rounded-lg py-3 px-4 focus:ring-2 focus:ring-primary outline-none text-lg"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-500">
              <div className="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6">
                <PieChart className="w-8 h-8" />
              </div>
              <h2 className="text-3xl font-bold mb-4">Ready to go!</h2>
              <p className="text-textMuted mb-8">Your profile is set up. You can start creating budgets and logging your daily expenses.</p>
              
              <div className="bg-slate-800/50 border border-border p-6 rounded-2xl">
                <h3 className="font-semibold mb-2">Next steps:</h3>
                <ul className="space-y-3 text-sm text-textMuted">
                  <li className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs text-white">1</div>
                    Try the Voice UI to log an expense quickly
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs text-white">2</div>
                    Set up your first monthly budget
                  </li>
                  <li className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs text-white">3</div>
                    Review your auto-generated weekly insights
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>

        <button 
          onClick={handleNext}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground font-semibold py-4 rounded-xl hover:bg-opacity-90 transition disabled:opacity-50 text-lg shadow-lg shadow-primary/20"
        >
          {step < 3 ? 'Continue' : (loading ? 'Saving...' : 'Go to Dashboard')}
          {!loading && <ArrowRight className="w-5 h-5" />}
        </button>
      </div>
    </div>
  );
}
