import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Home, MessageCircle, Library, Calendar, User, Menu, Sparkles, MapPin, Clock, Settings, Compass } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../../stores/auth-store';
import { PageTransition } from '../ui/PageTransition';

const tabs = [
  { path: '/', label: '首页', icon: Home },
  { path: '/content', label: '文化', icon: Library },
  { path: '/activity', label: '活动', icon: Calendar },
  { path: '/discussion', label: '社区', icon: MessageCircle },
  { path: '/profile', label: '我的', icon: User },
];

function useActiveTab(pathname: string) {
  if (pathname === '/') return 0;
  const idx = tabs.findIndex(t => pathname.startsWith(t.path) && t.path !== '/');
  return idx >= 0 ? idx : 0;
}

export default function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const activeIdx = useActiveTab(location.pathname);
  const { session } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);

  const isAiPage = location.pathname === '/ai';

  const extraLinks = [
    { label: 'AI 数字人', path: '/ai', icon: Sparkles, accent: 'text-cinnabar-600' },
    { label: '非遗场馆', path: '/places', icon: MapPin },
    { label: '浏览历史', path: '/history', icon: Clock },
    { label: '偏好设置', path: '/preferences', icon: Settings },
    { label: '非遗文化', path: '/culture', icon: Compass },
  ];

  return (
    <div className="min-h-screen bg-parchment max-w-3xl mx-auto relative">
      {/* Header */}
      {!isAiPage && (
        <header className="sticky top-0 z-40 glass-card-elevated border-b border-ink-border/30 rounded-none">
          <div className="flex items-center justify-between px-4 h-14">
            <button onClick={() => navigate('/')} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <span className="w-7 h-7 cinnabar-gradient rounded-lg flex items-center justify-center text-white text-xs font-bold shadow-sm">非</span>
              <h1 className="text-base font-serif font-bold text-ink tracking-wide">黑塔 · 非遗</h1>
            </button>
            <div className="flex items-center gap-1.5">
              {session?.role === 'admin' && (
                <button
                  onClick={() => navigate('/admin')}
                  className="text-xs bg-gold-100 text-gold-600 px-2.5 py-1 rounded-full hover:bg-gold-200 transition-colors font-medium"
                >
                  管理
                </button>
              )}
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className={`p-1.5 rounded-lg transition-all ${menuOpen ? 'bg-ink-border/50 text-ink' : 'hover:bg-ink-border/30 text-ink-secondary'}`}
              >
                <Menu size={20} />
              </button>
            </div>
          </div>

          {/* Dropdown menu */}
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-3 top-12 bg-white/90 backdrop-blur-xl rounded-2xl shadow-lg border border-ink-border/30 p-1.5 w-44 z-50 animate-[pageIn_0.2s_ease-out]">
                {extraLinks.map(item => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.path}
                      onClick={() => { navigate(item.path); setMenuOpen(false); }}
                      className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-ink-secondary hover:text-ink hover:bg-parchment-dark/50 rounded-xl transition-all"
                    >
                      <Icon size={16} className={item.accent || 'text-ink-muted'} />
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </header>
      )}

      {/* Content */}
      <main className={isAiPage ? '' : 'pb-20'}>
        <PageTransition key={location.pathname}>
          <Outlet />
        </PageTransition>
      </main>

      {/* TabBar */}
      {!isAiPage && (
        <nav className="fixed bottom-3 left-1/2 -translate-x-1/2 max-w-sm w-[92%] z-40">
          <div className="glass-card-elevated rounded-2xl shadow-lg flex items-center justify-around h-16 px-2">
            {tabs.map((tab, idx) => {
              const Icon = tab.icon;
              const isActive = idx === activeIdx;
              return (
                <button
                  key={tab.path}
                  onClick={() => navigate(tab.path)}
                  className={`flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-xl transition-all min-w-0 relative ${
                    isActive ? 'text-cinnabar-700' : 'text-ink-muted hover:text-ink-secondary'
                  }`}
                >
                  {isActive && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-8 h-1 bg-cinnabar-700/30 rounded-full" />
                  )}
                  <Icon size={21} strokeWidth={isActive ? 2.5 : 1.8} />
                  <span className={`text-[11px] ${isActive ? 'font-semibold' : 'font-normal'}`}>
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
