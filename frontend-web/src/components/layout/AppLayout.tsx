import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Menu, Sparkles, MapPin, Clock, Settings, Compass } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../../stores/auth-store';
import { PageTransition } from '../ui/PageTransition';

/* CSS-only tab icons matching mini-program style */
function HomeGlyph({ active }: { active: boolean }) {
  const c = active ? '#fff7ef' : '#9f2d22';
  return (
    <div style={{ position: 'relative', width: 24, height: 24, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 3 }}>
      <div style={{ width: 18, height: 2.5, background: c, borderRadius: 1 }} />
      <div style={{ width: 14, height: 2.5, background: c, borderRadius: 1 }} />
      <div style={{ width: 8, height: 2.5, background: c, borderRadius: 1 }} />
    </div>
  );
}

function ContentGlyph({ active }: { active: boolean }) {
  const c = active ? '#fff7ef' : '#9f2d22';
  return (
    <div style={{ position: 'relative', width: 22, height: 24, border: `2.5px solid ${c}`, borderRadius: 4, boxSizing: 'border-box' }}>
      <div style={{ position: 'absolute', top: 6, left: 4, right: 4, height: 1.5, background: c, borderRadius: 1 }} />
      <div style={{ position: 'absolute', top: 12, left: 4, width: 8, height: 1.5, background: c, borderRadius: 1 }} />
    </div>
  );
}

function ActivityGlyph({ active }: { active: boolean }) {
  const c = active ? '#fff7ef' : '#9f2d22';
  return (
    <div style={{ position: 'relative', width: 22, height: 24, border: `2.5px solid ${c}`, borderRadius: 4, boxSizing: 'border-box' }}>
      <div style={{ position: 'absolute', top: 4, left: 0, right: 0, height: 2, background: c, margin: '0 4rpx' }} />
      <div style={{ position: 'absolute', top: 10, left: '50%', width: 2, height: 8, background: c, transform: 'translateX(-50%)' }} />
    </div>
  );
}

function DiscussGlyph({ active }: { active: boolean }) {
  const c = active ? '#fff7ef' : '#9f2d22';
  return (
    <div style={{ position: 'relative', width: 24, height: 24 }}>
      <div style={{ position: 'absolute', left: 2, top: 2, width: 17, height: 14, border: `2.5px solid ${c}`, borderRadius: 6, boxSizing: 'border-box' }} />
      <div style={{ position: 'absolute', right: 1, bottom: 1, width: 0, height: 0, borderLeft: `6rpx solid transparent`, borderRight: '6rpx solid transparent', borderTop: `7rpx solid ${c}` }} />
      <div style={{ position: 'absolute', left: 7, top: 7, width: 6, height: 1.5, background: c, borderRadius: 1 }} />
    </div>
  );
}

function ProfileGlyph({ active }: { active: boolean }) {
  const c = active ? '#fff7ef' : '#9f2d22';
  return (
    <div style={{ position: 'relative', width: 22, height: 24, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ width: 13, height: 13, borderRadius: '50%', background: c }} />
      <div style={{ width: 18, height: 10, borderRadius: '9rpx 9rpx 0 0', background: c, marginTop: -1 }} />
    </div>
  );
}

const tabs = [
  { path: '/', label: '首页', Glyph: HomeGlyph },
  { path: '/content', label: '文化', Glyph: ContentGlyph },
  { path: '/activity', label: '活动', Glyph: ActivityGlyph },
  { path: '/discussion', label: '讨论', Glyph: DiscussGlyph },
  { path: '/profile', label: '我的', Glyph: ProfileGlyph },
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
    { label: 'AI 数字人', path: '/ai', icon: Sparkles },
    { label: '非遗场馆', path: '/places', icon: MapPin },
    { label: '浏览历史', path: '/history', icon: Clock },
    { label: '偏好设置', path: '/preferences', icon: Settings },
    { label: '非遗文化', path: '/culture', icon: Compass },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #fff8ef 0%, #f7efe0 42%, #f7f3eb 100%)',
      maxWidth: 480, margin: '0 auto', position: 'relative',
    }}>
      {/* Header */}
      {!isAiPage && (
        <header style={{
          position: 'sticky', top: 0, zIndex: 40,
          background: 'rgba(255,250,243,0.92)',
          backdropFilter: 'blur(16rpx)',
          borderBottom: '1rpx solid rgba(219,191,155,0.22)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 20rpx', height: 50 }}>
            <button onClick={() => navigate('/')} style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', cursor: 'pointer' }}>
              <span style={{
                width: 28, height: 28, borderRadius: 8,
                background: 'linear-gradient(135deg, #9f2d22, #bf563f)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff7ef', fontSize: 14, fontWeight: 800,
              }}>非</span>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#2f2419', letterSpacing: '0.5rpx' }}>黑塔 · 非遗</span>
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {session?.role === 'admin' && (
                <button onClick={() => navigate('/admin')}
                  style={{
                    fontSize: 12, background: '#f7e7dc', color: '#9f2d22',
                    padding: '4rpx 12rpx', borderRadius: 999, border: 'none',
                    cursor: 'pointer', fontWeight: 600,
                  }}>
                  管理
                </button>
              )}
              <button onClick={() => setMenuOpen(!menuOpen)}
                style={{
                  background: menuOpen ? '#f5e8d5' : 'transparent',
                  border: 'none', borderRadius: 10, padding: '6rpx',
                  color: '#7b6141', cursor: 'pointer',
                }}>
                <Menu size={20} />
              </button>
            </div>
          </div>
          {menuOpen && (
            <>
              <div style={{ position: 'fixed', inset: 0, zIndex: 40 }} onClick={() => setMenuOpen(false)} />
              <div style={{
                position: 'absolute', right: 16, top: 52, zIndex: 50,
                background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                borderRadius: 20, boxShadow: '0 14rpx 34rpx rgba(121,58,31,0.12)',
                border: '1rpx solid rgba(219,191,155,0.22)',
                padding: 8, width: 180,
              }}>
                {extraLinks.map(item => {
                  const Icon = item.icon;
                  return (
                    <button key={item.path} onClick={() => { navigate(item.path); setMenuOpen(false); }}
                      style={{
                        width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                        padding: '12rpx 14rpx', border: 'none', borderRadius: 12,
                        background: 'transparent', color: '#5a4430', fontSize: 14,
                        cursor: 'pointer',
                      }}>
                      <Icon size={16} style={{ color: '#9f2d22' }} />
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
      <main style={{ paddingBottom: isAiPage ? 0 : 120 }}>
        <PageTransition key={location.pathname}>
          <Outlet />
        </PageTransition>
      </main>

      {/* TabBar — floating pill (小程序风格) */}
      {!isAiPage && (
        <nav style={{
          position: 'fixed', bottom: '14rpx', left: '50%', transform: 'translateX(-50%)',
          zIndex: 100, maxWidth: 440, width: '92%',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-around',
            height: 56, borderRadius: 999,
            background: 'linear-gradient(135deg, #fffdf8, #f5e8d5)',
            boxShadow: '0 12rpx 32rpx rgba(97, 63, 33, 0.16)',
            border: '1rpx solid rgba(182, 141, 95, 0.2)',
            padding: '0 6rpx',
          }}>
            {tabs.map((tab, idx) => {
              const isActive = idx === activeIdx;
              const Glyph = tab.Glyph;
              return (
                <button key={tab.path} onClick={() => navigate(tab.path)}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                    height: 44, padding: '0 14rpx', borderRadius: 999,
                    border: 'none', cursor: 'pointer',
                    transition: 'all 0.22s ease',
                    background: isActive ? 'linear-gradient(135deg, #9f2d22, #bf563f)' : 'transparent',
                    boxShadow: isActive ? '0 10rpx 20rpx rgba(159,45,34,0.24)' : 'none',
                    color: isActive ? '#fff7ef' : '#8c6a42',
                    fontWeight: isActive ? 700 : 500,
                    fontSize: 13,
                  }}>
                  <Glyph active={isActive} />
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
