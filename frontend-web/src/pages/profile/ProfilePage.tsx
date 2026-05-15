import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Settings, MapPin, Clock, BookOpen, LogOut, ChevronRight, Sparkles, BarChart3 } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { User as UserType } from '../../types';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { session, logout } = useAuthStore();
  const { data } = useQuery({
    queryKey: ['user-profile', session?.userId],
    queryFn: () => apiRequest<{ code: number; data: UserType }>(`/users/${session?.userId}`),
    enabled: !!session?.userId,
  });
  const user = data?.data;

  const confidence = user?.confidence_score ? Math.round(user.confidence_score) : 0;

  const menuItems = [
    { icon: BookOpen, label: '非遗文化', path: '/culture' },
    { icon: MapPin, label: '非遗场馆', path: '/places' },
    { icon: Clock, label: '浏览历史', path: '/history' },
    { icon: Settings, label: '偏好设置', path: '/preferences' },
    { icon: BarChart3, label: 'AI 画像', path: '/ai' },
  ];

  return (
    <div style={{ padding: '0 24px 36px' }}>
      {/* Hero */}
      <div style={{
        background: 'linear-gradient(135deg, #2a1611 0%, #6d2a20 54%, #bf7948 100%)',
        borderRadius: '30px', padding: '28px', marginTop: 16, marginBottom: 18,
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, position: 'relative', zIndex: 1 }}>
          {/* Chibi avatar (CSS) */}
          <div style={{ position: 'relative', width: 50, height: 50 }}>
            <div style={{
              width: 42, height: 42, borderRadius: '50%', position: 'absolute', left: 4, top: 4,
              background: 'linear-gradient(180deg, #ede1ff, #cfb6ff 58%, #b38af0 100%)',
            }}>
              <div style={{ position: 'absolute', top: -6, left: 4, width: 34, height: 18, background: '#2d2344', borderRadius: '50%' }} />
              <div style={{ position: 'absolute', top: 10, left: 10, width: 22, height: 18, background: '#fff3f7', borderRadius: '45%', boxShadow: '0 2px 0 rgba(93,66,132,0.06)' }}>
                <div style={{ position: 'absolute', top: 4, left: 3, width: 6, height: 10, borderRadius: 999, background: 'linear-gradient(180deg, #9f71ff, #5a3ab5)' }} />
                <div style={{ position: 'absolute', top: 4, right: 3, width: 6, height: 10, borderRadius: 999, background: 'linear-gradient(180deg, #9f71ff, #5a3ab5)' }} />
                <div style={{ position: 'absolute', bottom: 3, left: 9, width: 4, height: 2, borderRadius: 999, background: '#8f6b86' }} />
              </div>
            </div>
          </div>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: '#fff8ef', margin: 0 }}>{user?.nickname || session?.nickname || '用户'}</h2>
            <p style={{ fontSize: 13, color: 'rgba(255,244,232,0.75)', margin: '4px 0 0' }}>@{user?.username || session?.username}</p>
          </div>
        </div>

        {/* CRS bar */}
        <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.15)', position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
            <span style={{ fontSize: 13, color: 'rgba(255,244,232,0.8)', fontWeight: 600 }}>
              <Sparkles size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />
              {confidence > 70 ? '已懂你' : confidence > 30 ? '了解中' : '初识'}
            </span>
            <span style={{ fontSize: 15, fontWeight: 800, color: '#fff' }}>{confidence}%</span>
          </div>
          <div style={{ marginTop: 6, height: 10, borderRadius: 5, background: 'rgba(0,0,0,0.15)' }}>
            <div style={{
              height: '100%', borderRadius: 5,
              width: `${confidence}%`,
              background: confidence > 70 ? 'linear-gradient(90deg, #4caf50, #81c784)' : confidence > 30 ? 'linear-gradient(90deg, #2196f3, #64b5f6)' : 'linear-gradient(90deg, #ff9800, #ffb74d)',
              transition: 'width 0.6s ease',
            }} />
          </div>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 18 }}>
        {[
          { label: '画像完整度', value: `${confidence}%`, color: '#7b2a1d' },
          { label: '浏览', value: data ? '查看' : '-', color: '#a04e1c' },
          { label: '收藏', value: data ? '查看' : '-', color: '#6d4c2a' },
        ].map((stat, i) => (
          <div key={i} className="card" style={{ margin: 0, textAlign: 'center', padding: '18px 14px' }}>
            <p style={{ fontSize: 22, fontWeight: 800, color: stat.color, margin: 0 }}>{stat.value}</p>
            <p style={{ fontSize: 12, color: '#85684c', margin: '4px 0 0' }}>{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Preferences hint */}
      {user?.preferred_heritage_types && user.preferred_heritage_types.length > 0 && (
        <div className="card" style={{ marginBottom: 18, padding: '16px 20px' }}>
          <p style={{ fontSize: 12, color: '#85684c', margin: 0 }}>
            偏好：{Array.isArray(user.preferred_heritage_types) ? user.preferred_heritage_types.join('、') : String(user.preferred_heritage_types)}
          </p>
        </div>
      )}

      {/* Menu */}
      <div className="card" style={{ marginBottom: 18, padding: '0', overflow: 'hidden' }}>
        {menuItems.map((item, i) => { const Icon = item.icon; return (
          <button key={item.path} onClick={() => navigate(item.path)}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: '18px 24px', border: 'none', background: 'transparent', cursor: 'pointer',
              borderBottom: i < menuItems.length - 1 ? '1px solid rgba(219,191,155,0.18)' : 'none',
              color: '#5a4430', fontSize: 14,
            }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Icon size={18} style={{ color: '#9f2d22' }} />
              <span style={{ fontWeight: 500 }}>{item.label}</span>
            </div>
            <ChevronRight size={16} style={{ color: '#c4a882' }} />
          </button>
        ); })}
      </div>

      {/* Logout */}
      <button onClick={() => { logout(); navigate('/login', { replace: true }); }}
        className="primary-btn" style={{ width: '100%' }}>
        <LogOut size={16} style={{ marginRight: 6 }} /> 退出登录
      </button>
    </div>
  );
}
