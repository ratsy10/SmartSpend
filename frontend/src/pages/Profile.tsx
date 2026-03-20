import { useState } from 'react';
import { useAuthStore } from '../store/useAuthStore';
import { LogOut, Bell, DollarSign, Save } from 'lucide-react';
import { api } from '../lib/api';
import { usePushNotifications } from '../hooks/usePushNotifications';

export default function Profile() {
  const { user, updateUser, logout } = useAuthStore();
  const { subscribeToPush, isSubscribed } = usePushNotifications();
  
  const [currency, setCurrency] = useState(user?.currency || 'USD');
  const [reminder, setReminder] = useState(true);
  const [saving, setSaving] = useState(false);

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.error(err);
    } finally {
      logout();
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/auth/me', {
        currency,
        reminder_enabled: reminder
      });
      updateUser({ currency });
      alert("Settings saved successfully!");
    } catch (err) {
      alert("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-1">Profile</h1>
      </header>

      <div className="bg-surface border border-border rounded-3xl p-6 flex items-center gap-6 mb-8 shadow-lg">
        {user?.avatar_url ? (
          <img src={user.avatar_url} alt="Profile" className="w-20 h-20 rounded-full border-4 border-background object-cover" />
        ) : (
          <div className="w-20 h-20 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-3xl border-4 border-background">
            {user?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
        )}
        <div>
          <h2 className="text-xl font-bold text-textMain">{user?.full_name}</h2>
          <p className="text-textMuted text-sm">{user?.email}</p>
          <div className="mt-2 text-xs bg-primary/10 text-primary px-3 py-1 rounded-full inline-block font-medium">
            Pro Member
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="bg-surface border border-border rounded-3xl overflow-hidden shadow-lg">
          <div className="p-4 border-b border-border/50 flex items-center gap-3">
            <DollarSign className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Currency</h3>
          </div>
          <div className="p-4 bg-background/50">
            <select 
              value={currency} 
              onChange={e => setCurrency(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl p-3 outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
              <option value="GBP">GBP (£)</option>
              <option value="INR">INR (₹)</option>
            </select>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-3xl overflow-hidden shadow-lg">
          <div className="p-4 border-b border-border/50 flex items-center gap-3">
            <Bell className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Notifications</h3>
          </div>
          <div className="p-4 bg-background/50 space-y-4">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-textMain font-medium">Daily Reminders</span>
              <input 
                type="checkbox" 
                checked={reminder} 
                onChange={(e) => setReminder(e.target.checked)}
                className="w-5 h-5 accent-primary rounded" 
              />
            </label>

            <div className="border-t border-border pt-4">
              <div className="flex justify-between items-center mb-2">
                <span className="text-textMain font-medium">Push Notifications</span>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${isSubscribed ? 'bg-success/20 text-success' : 'bg-surface border border-border text-textMuted'}`}>
                  {isSubscribed ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <p className="text-xs text-textMuted mb-3">Get real-time alerts for budget limits and insights.</p>
              {!isSubscribed && (
                <button 
                  onClick={subscribeToPush}
                  className="w-full py-2 bg-primary/10 text-primary rounded-xl font-medium hover:bg-primary/20 transition"
                >
                  Enable Push Notifications
                </button>
              )}
            </div>
          </div>
        </div>

        <button 
          onClick={handleSave}
          disabled={saving}
          className="w-full py-4 bg-primary text-primary-foreground rounded-2xl font-bold flex items-center justify-center gap-2 hover:opacity-90 transition disabled:opacity-50"
        >
          <Save className="w-5 h-5" />
          {saving ? 'Saving...' : 'Save Preferences'}
        </button>

        <button 
          onClick={handleLogout}
          className="w-full py-4 bg-danger/10 text-danger border border-danger/20 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-danger/20 transition mt-8"
        >
          <LogOut className="w-5 h-5" />
          Log Out
        </button>
      </div>
    </div>
  );
}
