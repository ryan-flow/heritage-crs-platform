import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Settings, MapPin, Clock, BookOpen, LogOut, ChevronRight, Sparkles, BarChart3 } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { User as UserType } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { session, logout } = useAuthStore();

  const { data } = useQuery({
    queryKey: ['user-profile', session?.userId],
    queryFn: () => apiRequest<{ code: number; data: UserType }>(`/users/${session?.userId}`),
    enabled: !!session?.userId,
  });

  const user = data?.data;

  const menuItems = [
    { icon: BookOpen, label: '非遗文化', path: '/culture' },
    { icon: MapPin, label: '非遗场馆', path: '/places' },
    { icon: Clock, label: '浏览历史', path: '/history' },
    { icon: Settings, label: '偏好设置', path: '/preferences' },
    { icon: BarChart3, label: 'AI 画像', path: '/ai' },
  ];

  return (
    <div className="px-4 py-5 space-y-4">
      {/* Profile Card */}
      <GlassCard elevated className="p-5">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 cinnabar-gradient rounded-full flex items-center justify-center text-white text-xl font-serif shadow-md">
            {(session?.nickname || '用')[0]}
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-serif font-bold text-ink">{user?.nickname || session?.nickname || '用户'}</h2>
            <p className="text-sm text-ink-secondary">@{user?.username || session?.username}</p>
            {user?.confidence_score ? (
              <div className="mt-1.5 flex items-center gap-1.5">
                <Sparkles size={13} className="text-gold-500" />
                <span className="text-xs text-ink-muted">画像完整度 {Math.round(user.confidence_score)}%</span>
              </div>
            ) : null}
          </div>
        </div>
        {user?.preferred_heritage_types && (
          <div className="mt-3 pt-3 border-t border-ink-border/30">
            <span className="text-xs text-ink-secondary">偏好：{user.preferred_heritage_types.replace(/,/g, '、')}</span>
          </div>
        )}
      </GlassCard>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2.5">
        {[
          { label: '置信度', value: user?.confidence_score ? `${Math.round(user.confidence_score)}%` : '-', color: 'text-cinnabar-600' },
          { label: '浏览', value: data ? '查看' : '-', color: 'text-jade-600' },
          { label: '收藏', value: data ? '查看' : '-', color: 'text-gold-600' },
        ].map((stat, i) => (
          <GlassCard key={i} className="p-3 text-center">
            <p className={`text-lg font-bold font-serif ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-ink-muted mt-0.5">{stat.label}</p>
          </GlassCard>
        ))}
      </div>

      {/* Menu */}
      <GlassCard className="overflow-hidden">
        {menuItems.map((item, i) => {
          const Icon = item.icon;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center justify-between px-4 py-3.5 text-sm text-ink-secondary hover:bg-parchment-dark/30 hover:text-ink transition-colors ${
                i < menuItems.length - 1 ? 'border-b border-ink-border/20' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon size={17} className="text-ink-muted" />
                <span>{item.label}</span>
              </div>
              <ChevronRight size={15} className="text-ink-muted" />
            </button>
          );
        })}
      </GlassCard>

      {/* Logout */}
      <button
        onClick={() => { logout(); navigate('/login', { replace: true }); }}
        className="w-full py-3 glass-card text-cinnabar-600 rounded-xl text-sm font-medium hover:bg-cinnabar-50/50 transition-all flex items-center justify-center gap-2 border-cinnabar-100/50"
      >
        <LogOut size={16} /> 退出登录
      </button>
    </div>
  );
}
