import { NavLink } from 'react-router-dom';
import { Home, BarChart2, Plus, Wallet, Settings } from 'lucide-react';

export default function BottomNav() {
  const navItems = [
    { to: "/", icon: Home, label: "Home" },
    { to: "/analytics", icon: BarChart2, label: "Stats" },
    { to: "/add", icon: Plus, label: "Add" },
    { to: "/history", icon: Wallet, label: "Wallet" }, 
    { to: "/profile", icon: Settings, label: "Settings" },
  ];

  return (
    <div className="fixed bottom-0 left-0 w-full bg-surface border-t border-border z-50 pb-safe pt-2 px-6">
      <div className="max-w-md mx-auto flex justify-between items-center relative">
        {navItems.map((item, i) => {
          const isAddBtn = item.to === "/add";
          return (
            <NavLink
              key={i}
              to={item.to}
              className={({ isActive }) => 
                `flex flex-col items-center justify-center w-16 h-14 transition-colors ${
                  isAddBtn 
                    ? 'absolute left-1/2 -translate-x-1/2 -top-6 w-16 h-16 bg-primary rounded-full shadow-lg shadow-primary/30 text-textMain flex items-center justify-center hover:scale-105 transform transition' 
                    : isActive 
                      ? 'text-primary' 
                      : 'text-textMuted hover:text-textMain'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon className={isAddBtn ? "w-8 h-8 text-black" : "w-6 h-6"} />
                  {!isAddBtn && <span className={`text-[10px] mt-1 font-bold tracking-wide uppercase ${isActive ? 'text-primary' : 'text-textMuted'}`}>{item.label}</span>}
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </div>
  );
}
