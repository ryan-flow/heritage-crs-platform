import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Menu, Sparkles, MapPin, Clock, Settings, Compass } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../../stores/auth-store';
import { PageTransition } from '../ui/PageTransition';

/* CSS-only tab icons matching mini-program style */
function TabGlyph({ active, type }: { active: boolean; type: string }) {
  const c = active ? '#fff7ef' : '#9f2d22';
  if (type === 'home') return (
    <div className="relative w-6 h-6 flex flex-col justify-center items-center gap-[3px]">
      <div style={{ width: 18, height: 2.5, background: c, borderRadius: 1 }} />
      <div style={{ width: 14, height: 2.5, background: c, borderRadius: 1 }} />
      <div style={{ width: 8, height: 2.5, background: c, borderRadius: 1 }} />
    </div>
  );
  if (type === 'content') return (
    <div className="relative w-[22px] h-6 rounded" style={{ border: `2.5px solid ${c}` }}>
      <div className="absolute top-1.5 left-1 right-1 h-[1.5px]" style={{ background: c }} />
      <div className="absolute top-3 left-1 w-2 h-[1.5px]" style={{ background: c }} />
    </div>
  );
  if (type === 'activity') return (
    <div className="relative w-[22px] h-6 rounded" style={{ border: `2.5px solid ${c}` }}>
      <div className="absolute top-1 left-0 right-0 mx-1 h-0.5" style={{ background: c }} />
      <div className="absolute top-2.5 left-1/2 -translate-x-1/2 w-0.5 h-2" style={{ background: c }} />
    </div>
  );
  if (type === 'discussion') return (
    <div className="relative w-6 h-6">
      <div className="absolute left-0.5 top-0.5 w-[17px] h-3.5 rounded-md" style={{ border: `2.5px solid ${c}` }} />
      <div className="absolute right-px -bottom-px w-0 h-0 border-l-[6px] border-r-[6px] border-t-[7px] border-l-transparent border-r-transparent" style={{ borderTopColor: c }} />
      <div className="absolute left-[7px] top-[7px] w-1.5 h-[1.5px]" style={{ background: c }} />
    </div>
  );
  if (type === 'profile') return (
    <div className="relative w-[22px] h-6 flex flex-col items-center">
      <div className="w-[13px] h-[13px] rounded-full" style={{ background: c }} />
      <div className="w-[18px] h-2.5 rounded-t-[9px] -mt-px" style={{ background: c }} />
    </div>
  );
  return null;
}

const tabs = [
  { path: '/', label: '首页', type: 'home' },
  { path: '/content', label: '文化', type: 'content' },
  { path: '/activity', label: '活动', type: 'activity' },
  { path: '/discussion', label: '讨论', type: 'discussion' },
  { path: '/profile', label: '我的', type: 'profile' },
] as const;

function useActiveTab(pathname: string) {
  if (pathname === '/') return 0;
  return tabs.findIndex(t => pathname.startsWith(t.path) && t.path !== '/');
}

export default function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeIdx = useActiveTab(location.pathname);
  const effectiveIdx = activeIdx >= 0 ? activeIdx : 0;
  const { session } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);
  const isAiPage = location.pathname === '/ai';

  const extraLinks = [
    { label: 'AI 数字人', path: '/ai', icon: Sparkles },
    { label: '非遗场馆', path: '/places', icon: MapPin },
    { label: '浏览历史', path: '/history', icon: Clock },
    { label: '偏好设置', path: '/preferences', icon: Settings },
    { label: '非遗文化', path: '/culture', icon: Compass },
  ];

  return (
    <div className="min-h-screen max-w-[480px] mx-auto relative"
      style={{ background: 'linear-gradient(180deg, #fff8ef 0%, #f7efe0 42%, #f7f3eb 100%)' }}>

      {/* Header */}
      {!isAiPage && (
        <header className="sticky top-0 z-40 backdrop-blur-md border-b border-[rgba(219,191,155,0.22)]"
          style={{ background: 'rgba(255,250,243,0.92)' }}>
          <div className="flex items-center justify-between px-5 h-[50px]">
            <button onClick={() => navigate('/')} className="flex items-center gap-2 bg-transparent border-none cursor-pointer">
              <span className="w-7 h-7 rounded-lg flex items-center justify-center text-[#fff7ef] text-sm font-extrabold"
                style={{ background: 'linear-gradient(135deg, #9f2d22, #bf563f)' }}>非</span>
              <span className="text-base font-bold text-[#2f2419] tracking-[0.5px]">黑塔 · 非遗</span>
            </button>
            <div className="flex items-center gap-2">
              {session?.role === 'admin' && (
                <button onClick={() => navigate('/admin')}
                  className="text-xs bg-[#f7e7dc] text-brand px-3 py-1 rounded-full border-none cursor-pointer font-semibold">
                  管理
                </button>
              )}
              <button onClick={() => setMenuOpen(!menuOpen)}
                className="p-1.5 rounded-xl border-none cursor-pointer text-[#7b6141] hover:bg-[#f5e8d5] transition-colors">
                <Menu size={20} />
              </button>
            </div>
          </div>
        </header>
      )}

      {/* Menu dropdown */}
      {menuOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
          <div className="absolute right-4 top-[52px] z-50 rounded-[10px] p-2 w-[180px]"
            style={{
              background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
              boxShadow: '0 14px 34px rgba(121,58,31,0.12)',
              border: '1px solid rgba(219,191,155,0.22)',
            }}>
            {extraLinks.map(item => { const Icon = item.icon; return (
              <button key={item.path} onClick={() => { navigate(item.path); setMenuOpen(false); }}
                className="w-full flex items-center gap-2.5 px-3.5 py-3 border-none rounded-xl bg-transparent text-sm text-[#5a4430] cursor-pointer hover:bg-[#f5e8d5]/50 transition-colors">
                <Icon size={16} className="text-brand" /> {item.label}
              </button>
            ); })}
          </div>
        </>
      )}

      {/* Main content */}
      <main style={{ paddingBottom: isAiPage ? 0 : 90 }}>
        <PageTransition key={location.pathname}>
          <Outlet />
        </PageTransition>
      </main>

      {/* Floating capsule tab bar */}
      {!isAiPage && (
        <nav className="fixed bottom-3.5 left-1/2 -translate-x-1/2 z-[100] max-w-[440px] w-[92%]">
          <div className="flex items-center justify-around h-14 rounded-full px-1.5"
            style={{
              background: 'linear-gradient(135deg, #fffdf8, #f5e8d5)',
              boxShadow: '0 12px 32px rgba(97,63,33,0.16)',
              border: '1px solid rgba(182,141,95,0.2)',
            }}>
            {tabs.map((tab, idx) => {
              const isActive = idx === effectiveIdx;
              return (
                <button key={tab.path} onClick={() => navigate(tab.path)}
                  className="flex items-center justify-center gap-1.5 h-11 px-3.5 rounded-full border-none cursor-pointer transition-all duration-200"
                  style={{
                    background: isActive ? 'linear-gradient(135deg, #9f2d22, #bf563f)' : 'transparent',
                    boxShadow: isActive ? '0 10px 20px rgba(159,45,34,0.24)' : 'none',
                    color: isActive ? '#fff7ef' : '#8c6a42',
                    fontWeight: isActive ? 700 : 500,
                    fontSize: 13,
                  }}>
                  <TabGlyph active={isActive} type={tab.type} />
                  {isActive && tab.label}
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
