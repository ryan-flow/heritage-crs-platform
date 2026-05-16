import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Eye, Clock } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { ContentItem } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ['history', session?.userId],
    queryFn: () => apiRequest<{ code: number; data: { contents: ContentItem[] } }>(`/users/${session?.userId}/history`),
    enabled: !!session?.userId,
  });

  const history = (data?.data?.contents || []) as ContentItem[];

  return (
    <div className="pb-8 space-y-5">

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-[36px] bg-gradient-to-br from-cinnabar-700 via-brand to-gold-400 mx-4 mt-4 p-6 animate-fade-in-up">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1 text-sm text-white/80 hover:text-white transition-colors mb-2 font-sans"
        >
          <ArrowLeft size={16} /> 返回
        </button>
        <h1 className="text-2xl font-serif font-bold text-white leading-snug">
          浏览历史
        </h1>
        <p className="text-sm text-white/65 mt-1 font-sans">
          你走过的每一步，都是与非遗的对话
        </p>
      </div>

      {/* Content */}
      <div className="px-4">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4].map(i => (
              <SkeletonLoader key={i} variant="card" className="!h-16" />
            ))}
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-20 animate-fade-in-up">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-parchment-dark flex items-center justify-center">
              <Clock size={28} className="text-ink-muted/40" />
            </div>
            <p className="text-ink-muted text-sm font-sans">暂无浏览记录</p>
            <p className="text-ink-muted/60 text-xs mt-1 font-sans">浏览非遗文化内容后将自动记录</p>
            <button
              onClick={() => navigate('/culture')}
              className="ink-btn ink-btn-outline mt-4 !text-xs"
            >
              去看看内容
            </button>
          </div>
        ) : (
          <div className="space-y-2 rise-in-stagger">
            {history.map((item: ContentItem) => (
              <button
                key={item.id}
                onClick={() => navigate(`/content/${item.id}`)}
                className="w-full glass-card p-3 card-interactive text-left flex items-center gap-3 guofeng-press"
              >
                {item.cover_url ? (
                  <div className="w-12 h-12 shrink-0 rounded-lg overflow-hidden bg-parchment-dark">
                    <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" />
                  </div>
                ) : (
                  <div className="w-12 h-12 shrink-0 rounded-lg bg-parchment-dark flex items-center justify-center">
                    <Eye size={18} className="text-ink-muted/40" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-ink line-clamp-1 font-sans">{item.title}</h3>
                  <p className="text-xs text-ink-muted mt-0.5 font-sans">{item.category || '未分类'}</p>
                </div>
                <Eye size={15} className="text-ink-muted shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
