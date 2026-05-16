import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Settings, MapPin, Clock, BookOpen, LogOut, ChevronRight, Sparkles, BarChart3 } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { User as UserType } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';

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

  const confidenceLabel = confidence > 70 ? '已懂你' : confidence > 30 ? '了解中' : '初识';

  const confidenceBarColor =
    confidence > 70
      ? 'bg-gradient-to-r from-jade-500 to-jade-200'
      : confidence > 30
        ? 'bg-gradient-to-r from-indigo-500 to-indigo-500/60'
        : 'bg-gradient-to-r from-[#ff9800] to-[#ffb74d]';

  const menuItems = [
    { icon: BookOpen, label: '非遗文化', path: '/culture' },
    { icon: MapPin, label: '非遗场馆', path: '/places' },
    { icon: Clock, label: '浏览历史', path: '/history' },
    { icon: Settings, label: '偏好设置', path: '/preferences' },
    { icon: BarChart3, label: 'AI 画像', path: '/ai' },
  ];

  return (
    <div className="px-6 pb-9 pt-0 space-y-[18px]">

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-[30px] bg-gradient-to-br from-[#2a1611] via-cinnabar-700 to-gold-400 p-7 mt-4">
        <div className="relative z-10 flex items-center gap-4">
          {/* Chibi avatar (CSS drawn) */}
          <div className="relative w-[50px] h-[50px] shrink-0">
            <div className="absolute left-1 top-1 w-[42px] h-[42px] rounded-full bg-gradient-to-b from-[#ede1ff] via-[#cfb6ff] to-[#b38af0]">
              {/* hair */}
              <div className="absolute -top-1.5 left-1 w-[34px] h-[18px] bg-[#2d2344] rounded-full" />
              {/* face */}
              <div className="absolute top-2.5 left-2.5 w-[22px] h-[18px] rounded-[45%] bg-[#fff3f7] shadow-[0_2px_0_rgba(93,66,132,0.06)]">
                {/* left eye */}
                <div className="absolute top-1 left-[3px] w-1.5 h-2.5 rounded-full bg-gradient-to-b from-[#9f71ff] to-[#5a3ab5]" />
                {/* right eye */}
                <div className="absolute top-1 right-[3px] w-1.5 h-2.5 rounded-full bg-gradient-to-b from-[#9f71ff] to-[#5a3ab5]" />
                {/* mouth */}
                <div className="absolute bottom-[3px] left-[9px] w-1 h-0.5 rounded-full bg-[#8f6b86]" />
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-xl font-bold text-[#fff8ef] m-0">
              {user?.nickname || session?.nickname || '用户'}
            </h2>
            <p className="text-[13px] text-white/70 mt-1">
              @{user?.username || session?.username}
            </p>
          </div>
        </div>

        {/* CRS confidence bar */}
        <div className="relative z-10 mt-4 pt-3.5 border-t border-white/15">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[13px] text-white/80 font-semibold inline-flex items-center gap-1">
              <Sparkles size={12} />
              {confidenceLabel}
            </span>
            <span className="text-[15px] font-extrabold text-white">{confidence}%</span>
          </div>
          <div className="mt-1.5 h-2.5 rounded-full bg-black/15 overflow-hidden">
            <div
              className={`h-full rounded-full transition-[width] duration-600 ease-out ${confidenceBarColor}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-2.5">
        {[
          { label: '画像完整度', value: `${confidence}%` },
          { label: '浏览', value: data ? '查看' : '-' },
          { label: '收藏', value: data ? '查看' : '-' },
        ].map((stat, i) => {
          const valueColors = ['text-cinnabar-700', 'text-brand', 'text-gold-600'];
          return (
            <GlassCard key={i} className="!p-[18px_14px] text-center !rounded-[28px]">
              <p className={`text-[22px] font-extrabold m-0 ${valueColors[i]}`}>{stat.value}</p>
              <p className="text-xs text-ink-muted mt-1">{stat.label}</p>
            </GlassCard>
          );
        })}
      </div>

      {/* Preferences hint */}
      {user?.preferred_heritage_types && user.preferred_heritage_types.length > 0 && (
        <GlassCard className="!p-4">
          <p className="text-xs text-ink-muted m-0">
            偏好：{Array.isArray(user.preferred_heritage_types) ? user.preferred_heritage_types.join('、') : String(user.preferred_heritage_types)}
          </p>
        </GlassCard>
      )}

      {/* Menu */}
      <GlassCard className="!p-0 overflow-hidden">
        {menuItems.map((item, i) => {
          const Icon = item.icon;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center justify-between px-6 py-[18px] bg-transparent cursor-pointer text-ink-secondary text-sm transition-colors hover:bg-ink/4 ${
                i < menuItems.length - 1 ? 'border-b border-[rgba(219,191,155,0.18)]' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon size={18} className="text-brand" />
                <span className="font-medium">{item.label}</span>
              </div>
              <ChevronRight size={16} className="text-ink-muted/60" />
            </button>
          );
        })}
      </GlassCard>

      {/* Logout */}
      <InkButton
        variant="primary"
        size="lg"
        onClick={() => { logout(); navigate('/login', { replace: true }); }}
        className="!w-full"
      >
        <LogOut size={16} /> 退出登录
      </InkButton>
    </div>
  );
}
