import { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../../store/useAuthStore';
import { Bell, Check } from 'lucide-react';
import { api } from '../../lib/api';
import { formatDistanceToNow } from 'date-fns';

interface AppNotification {
  id: string;
  type: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  data: any;
}

export default function TopBar() {
  const user = useAuthStore((state) => state.user);
  const [showDropdown, setShowDropdown] = useState(false);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const { data } = await api.get('/notifications');
      setNotifications(data);
    } catch(err) {
      console.error("Failed to fetch notifications", err);
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
      // Poll every 30 seconds
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const markAsRead = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch(err) {
      console.error(err);
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.put('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch(err) {
      console.error(err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="fixed top-0 left-0 w-full bg-background/90 backdrop-blur-md z-40 px-4 pt-safe flex items-center justify-between h-[72px] border-b border-border/40">
      <div className="flex items-center gap-3">
        {user?.avatar_url ? (
          <img src={user.avatar_url} alt="Profile" className="w-10 h-10 rounded-full border border-slate-200 object-cover" />
        ) : (
          <div className="w-10 h-10 rounded-full bg-[#E6F9EC] text-[#10B981] flex items-center justify-center font-bold text-lg">
            {user?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
        )}
        <div className="flex flex-col">
          <span className="font-bold text-textMain text-lg tracking-tight">SmartSpend AI</span>
        </div>
      </div>
      
      <div className="relative" ref={dropdownRef}>
        <button 
          onClick={() => setShowDropdown(!showDropdown)}
          className="relative w-10 h-10 rounded-full flex items-center justify-center text-textMain hover:bg-black/5 transition"
        >
          <Bell className="w-6 h-6" />
          {unreadCount > 0 && (
            <span className="absolute top-2 right-2 min-w-4 h-4 px-1 bg-[#EF4444] text-white text-[10px] font-bold rounded-full flex items-center justify-center border border-background">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {showDropdown && (
          <div className="absolute right-0 mt-2 w-80 bg-surface rounded-2xl shadow-xl border border-border/50 overflow-hidden z-50">
            <div className="p-4 border-b border-border/50 flex justify-between items-center">
              <h3 className="font-bold text-textMain">Notifications</h3>
              {unreadCount > 0 && (
                <button onClick={markAllAsRead} className="text-xs text-primary font-semibold hover:underline flex items-center gap-1">
                  <Check className="w-3 h-3" /> Mark all read
                </button>
              )}
            </div>
            <div className="max-h-[350px] overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="p-6 text-center text-textMuted text-sm">
                  You have no notifications yet.
                </div>
              ) : (
                <div className="flex flex-col">
                  {notifications.map((n) => (
                    <div 
                      key={n.id} 
                      onClick={() => !n.is_read && markAsRead(n.id)}
                      className={`p-4 border-b border-border/20 cursor-pointer hover:bg-black/5 transition ${!n.is_read ? 'bg-primary/5' : ''}`}
                    >
                      <div className="flex justify-between items-start mb-1">
                        <h4 className={`text-sm ${!n.is_read ? 'font-bold text-textMain' : 'font-semibold text-textMuted'}`}>
                          {n.title}
                        </h4>
                        <span className="text-[10px] text-textMuted whitespace-nowrap ml-2">
                          {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                        </span>
                      </div>
                      <p className={`text-xs mt-1 ${!n.is_read ? 'text-textMain' : 'text-textMuted'}`}>
                        {n.body}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
