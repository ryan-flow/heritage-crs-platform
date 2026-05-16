import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Users, FileText, Calendar, MessageSquare, BookOpen, TrendingUp, ChevronRight } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { DashboardStats } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function DashboardPage() {
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => apiRequest<{ code: number; data: DashboardStats }>('/stats/dashboard'),
  });

  const stats = data?.data;

  const statCards = stats ? [
    { label: '总用户', value: stats.total_users, icon: Users, color: 'bg-cinnabar-500' },
    { label: '内容总数', value: stats.total_contents, icon: FileText, color: 'bg-brand' },
    { label: '活动总数', value: stats.total_activities, icon: Calendar, color: 'bg-jade-500' },
    { label: '帖子总数', value: stats.total_discussions, icon: MessageSquare, color: 'bg-gold-500' },
    { label: '知识条目', value: stats.total_knowledge_base, icon: BookOpen, color: 'bg-indigo-500' },
    { label: '今日新增', value: stats.users_today, icon: TrendingUp, color: 'bg-cinnabar-600' },
  ] : [];

  const quickActions = [
    { label: '管理内容', path: '/admin/contents' },
    { label: '管理活动', path: '/admin/activities' },
    { label: '管理帖子', path: '/admin/topics' },
    { label: '管理用户', path: '/admin/users' },
  ];

  return (
    <div className="space-y-5 pb-8">

      {/* Header */}
      <div className="animate-fade-in-up">
        <h2 className="text-lg font-serif font-bold text-ink">数据概览</h2>
        <p className="text-xs text-ink-muted mt-1 font-sans">管理平台核心运营数据</p>
      </div>

      {/* Stats Grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <SkeletonLoader key={i} variant="card" className="!h-24" />
          ))}
        </div>
      ) : statCards.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {statCards.map((card, i) => {
            const Icon = card.icon;
            return (
              <GlassCard
                key={i}
                className="!p-4 !rounded-[28px] rise-in"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 ${card.color} rounded-xl flex items-center justify-center shrink-0`}>
                    <Icon size={20} className="text-white" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-2xl font-extrabold text-ink font-sans">{card.value}</p>
                    <p className="text-xs text-ink-muted font-sans">{card.label}</p>
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </div>
      ) : (
        <GlassCard className="!p-8 text-center">
          <p className="text-ink-muted text-sm font-sans">暂无数据</p>
        </GlassCard>
      )}

      {/* Quick Actions */}
      <GlassCard className="!p-5 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
        <h3 className="text-sm font-serif font-bold text-ink mb-3">快速操作</h3>
        <div className="grid grid-cols-2 gap-2">
          {quickActions.map((link, i) => (
            <button
              key={i}
              onClick={() => navigate(link.path)}
              className="flex items-center justify-between py-2.5 px-4 bg-parchment-dark/60 rounded-xl text-sm text-ink-secondary hover:text-ink hover:bg-parchment-dark transition-all font-sans"
            >
              <span>{link.label}</span>
              <ChevronRight size={14} className="text-ink-muted/50" />
            </button>
          ))}
        </div>
      </GlassCard>
    </div>
  );
}
