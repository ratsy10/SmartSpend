import { useAuthStore } from '../../store/useAuthStore';
import { Bell } from 'lucide-react';

export default function TopBar() {
  const user = useAuthStore((state) => state.user);

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
          <span className="font-bold text-[#0F172A] text-lg tracking-tight">SmartSpend AI</span>
        </div>
      </div>
      
      <button className="relative w-10 h-10 rounded-full flex items-center justify-center text-[#0F172A] hover:bg-black/5 transition">
        <Bell className="w-6 h-6" />
        {/* Mock unread dot */}
        <span className="absolute top-2 right-2.5 w-2 h-2 bg-[#EF4444] rounded-full border border-background"></span>
      </button>
    </div>
  );
}
