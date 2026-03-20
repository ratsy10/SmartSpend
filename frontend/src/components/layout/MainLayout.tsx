import type { ReactNode } from 'react';
import TopBar from './TopBar';
import BottomNav from './BottomNav';

export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-textMain flex flex-col font-sans">
      <TopBar />
      <main className="flex-1 w-full max-w-md mx-auto pt-20 pb-24 px-4 overflow-y-auto overflow-x-hidden">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
