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
    <div className="px-4 py-5 space-y-4">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary hover:text-ink transition-colors">
        <ArrowLeft size={16} /> 返回
      </button>
      <h1 className="text-xl font-serif font-bold text-ink">浏览历史</h1>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => <SkeletonLoader key={i} variant="card" className="!h-16" />)}
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-16">
          <Clock size={32} className="mx-auto mb-2 text-ink-muted/40" />
          <p className="text-ink-muted text-sm">暂无浏览记录</p>
          <button onClick={() => navigate('/content')} className="text-cinnabar-600 mt-2 hover:underline text-sm">去看看内容</button>
        </div>
      ) : (
        <div className="space-y-2">
          {history.map((item: ContentItem) => (
            <button
              key={item.id}
              onClick={() => navigate(`/content/${item.id}`)}
              className="w-full glass-card p-3 hover:border-gold-200 transition-all text-left flex items-center gap-3 card-lift"
            >
              {item.cover_url ? (
                <div className="w-12 h-12 shrink-0 rounded-lg overflow-hidden bg-parchment-dark">
                  <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" />
                </div>
              ) : null}
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-ink line-clamp-1">{item.title}</h3>
                <p className="text-xs text-ink-muted mt-0.5">{item.category}</p>
              </div>
              <Eye size={15} className="text-ink-muted shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
