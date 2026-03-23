import React, { useState } from 'react';
import { useNavigate, useLocation, Navigate } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuthStore } from '../store/useAuthStore';
import { KeyRound, ArrowRight } from 'lucide-react';

export default function VerifyOTP() {
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const setAuth = useAuthStore(state => state.setAuth);
  
  const email = location.state?.email;
  const nextRoute = location.state?.next || '/';

  if (!email) {
    return <Navigate to="/login" replace />;
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      const { data } = await api.post('/auth/verify-otp', { 
        email, 
        otp_code: otp 
      });
      
      const userRes = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` }
      });
      
      setAuth(data.access_token, userRes.data);
      navigate(nextRoute);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid verification code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-surface p-8 sm:p-10 rounded-[2.5rem] shadow-sm border border-border/60">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 text-primary mb-6">
            <KeyRound className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-extrabold text-textMain mb-2 tracking-tight">Verify Email</h1>
          <p className="text-textMuted text-base">We sent a 6-digit code to {email}</p>
        </div>
        
        {error && (
          <div className="bg-danger/10 text-danger border border-danger/20 p-4 rounded-2xl text-sm mb-8">
            <span className="block">{error}</span>
          </div>
        )}
        
        <form onSubmit={handleVerify} className="space-y-5">
          <div className="space-y-1">
            <label className="text-sm font-semibold text-textMain ml-1">Verification Code</label>
            <input 
              type="text" 
              placeholder="123456" 
              className="w-full bg-background border border-border rounded-2xl py-4 px-4 text-center text-2xl tracking-widest text-textMain focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              value={otp}
              onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
              required
              maxLength={6}
              minLength={6}
            />
          </div>
          
          <button 
            type="submit" 
            disabled={loading || otp.length < 6}
            className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground font-bold py-4 rounded-2xl hover:opacity-90 transition-opacity disabled:opacity-50 mt-4 shadow-lg shadow-primary/20"
          >
            {loading ? 'Verifying...' : 'Verify & Continue'}
            {!loading && <ArrowRight className="h-5 w-5 ml-1" />}
          </button>
        </form>
      </div>
    </div>
  );
}
