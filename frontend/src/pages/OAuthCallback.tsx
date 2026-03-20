import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';
import { useAuthStore } from '../store/useAuthStore';

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const setAuth = useAuthStore(state => state.setAuth);

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (token) {
      // Fetch user profile with the token
      api.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      }).then(res => {
        setAuth(token, res.data);
        navigate('/');
      }).catch(err => {
        console.error('Failed to fetch user after OAuth:', err);
        navigate('/login');
      });
    } else {
      navigate('/login');
    }
  }, [searchParams, navigate, setAuth]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
    </div>
  );
}
