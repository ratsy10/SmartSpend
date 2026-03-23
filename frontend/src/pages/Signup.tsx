import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuthStore } from '../store/useAuthStore';
import { User, Mail, Lock, ArrowRight } from 'lucide-react';

export default function Signup() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore(state => state.setAuth);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/register', { 
        email, 
        password, 
        full_name: fullName 
      });
      
      if (res.data.require_verification) {
        navigate('/verify-otp', { state: { email, next: '/onboarding' } });
        return;
      }
      
      // Fallback if verification disabled in future
      const { data } = await api.post('/auth/login', { email, password });
      const userRes = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` }
      });
      setAuth(data.access_token, userRes.data);
      navigate('/onboarding');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create account. Email might be in use.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    window.location.href = `${backendUrl}/auth/login/google`;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-4">
      <div className="w-full max-w-md bg-surface p-8 sm:p-10 rounded-[2.5rem] shadow-sm border border-border/60">
        
        <div className="text-center mb-10">
          <h1 className="text-3xl font-extrabold text-textMain mb-2 tracking-tight">Create Account</h1>
          <p className="text-textMuted text-base">Start tracking your expenses smartly</p>
        </div>
        
        {error && (
          <div className="bg-danger/10 text-danger border border-danger/20 p-4 rounded-2xl text-sm mb-8 flex items-start">
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        
        <form onSubmit={handleSignup} className="space-y-5">
          <div className="space-y-1">
            <label className="text-sm font-semibold text-textMain ml-1">Full Name</label>
            <div className="relative">
              <User className="absolute left-4 top-4 h-5 w-5 text-textMuted" />
              <input 
                type="text" 
                placeholder="John Doe" 
                className="w-full bg-background border border-border rounded-2xl py-4 pl-12 pr-4 text-textMain placeholder:text-textMuted/60 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-semibold text-textMain ml-1">Email address</label>
            <div className="relative">
              <Mail className="absolute left-4 top-4 h-5 w-5 text-textMuted" />
              <input 
                type="email" 
                placeholder="hello@example.com" 
                className="w-full bg-background border border-border rounded-2xl py-4 pl-12 pr-4 text-textMain placeholder:text-textMuted/60 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
          </div>
          
          <div className="space-y-1">
            <label className="text-sm font-semibold text-textMain ml-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-4 h-5 w-5 text-textMuted" />
              <input 
                type="password" 
                placeholder="••••••••" 
                className="w-full bg-background border border-border rounded-2xl py-4 pl-12 pr-4 text-textMain placeholder:text-textMuted/60 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={6}
              />
            </div>
          </div>
          
          <button 
            type="submit" 
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground font-bold py-4 rounded-2xl hover:opacity-90 transition-opacity disabled:opacity-50 mt-4 shadow-lg shadow-primary/20"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
            {!loading && <ArrowRight className="h-5 w-5 ml-1" />}
          </button>
        </form>
        
        <div className="mt-8 relative flex items-center justify-center">
          <span className="absolute w-full border-t border-border"></span>
          <span className="bg-surface px-4 text-sm text-textMuted font-medium relative z-10">or continue with</span>
        </div>
        
        <button 
          onClick={handleGoogleLogin}
          className="mt-8 w-full flex items-center justify-center gap-3 bg-background border border-border py-4 rounded-2xl hover:bg-black/5 transition-colors font-semibold text-textMain"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24">
            <path fill="currentColor" d="M21.35,11.1H12.18V13.83H18.69C18.36,17.64 15.19,19.27 12.19,19.27C8.36,19.27 5,16.25 5,12C5,7.9 8.2,4.73 12.2,4.73C15.29,4.73 17.1,6.7 17.1,6.7L19,4.72C19,4.72 16.56,2 12.1,2C6.42,2 2.03,6.8 2.03,12C2.03,17.05 6.16,22 12.25,22C17.6,22 21.5,18.33 21.5,12.91C21.5,11.76 21.35,11.1 21.35,11.1V11.1Z" />
          </svg>
          Sign up with Google
        </button>

        <p className="mt-10 text-center text-sm font-medium text-textMuted">
          Already have an account? <Link to="/login" className="text-primary hover:text-primary/80 transition-colors">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
