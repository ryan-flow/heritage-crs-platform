import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Tag } from 'lucide-react';
import { apiRequest, buildImageUrl } from '../../lib/api';
import { ContentItem } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function HeritageDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { session } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ['heritage', id],
    queryFn: () => apiRequest<{ code: number; data: ContentItem }>(`/contents/${id}`),
    enabled: !!id,
  });

  const item = data?.data;

  useEffect(() => {
    if (id && session?.userId) {
      apiRequest('/recommend/track', {
        method: 'POST',
        data: { user_id: session.userId, action: 'view', target_type: 'content', target_id: Number(id), source_scene: 'culture_detail' },
      }).catch(() => {});
    }
  }, [id, session?.userId]);

  if (isLoading) {
    return (
      <div className="px-4 py-4 space-y-3">
        <SkeletonLoader variant="image" className="!h-48" />
        {[1, 2, 3].map(i => <SkeletonLoader key={i} variant="text" />)}
      </div>
    );
  }

  if (!item) {
    return (
      <div className="px-4 py-20 text-center">
        <p className="text-ink-muted">内容不存在</p>
        <button onClick={() => navigate(-1)} className="text-cinnabar-600 text-sm mt-2 hover:underline">返回</button>
      </div>
    );
  }

  return (
    <div className="pb-8">
      {item.cover_url && (
        <div className="h-48 bg-parchment-dark relative">
          <img src={buildImageUrl(item.cover_url)} alt={item.title} className="w-full h-full object-cover" />
          <button onClick={() => navigate(-1)} className="absolute top-4 left-4 p-2 glass-card rounded-xl">
            <ArrowLeft size={18} className="text-ink" />
          </button>
        </div>
      )}

      <div className="px-4">
        {!item.cover_url && (
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary mt-4 hover:text-ink transition-colors">
            <ArrowLeft size={16} /> 返回
          </button>
        )}

        <h1 className="text-xl font-serif font-bold text-ink mt-4 leading-snug">{item.title}</h1>

        <div className="flex items-center gap-2 mt-2 text-xs text-ink-muted">
          {item.category && <SealBadge variant="gold">{item.category}</SealBadge>}
          {item.region && <span className="flex items-center gap-1"><Tag size={12} /> {item.region}</span>}
        </div>

        {item.summary && (
          <GlassCard className="mt-4 p-3.5">
            <p className="text-sm text-ink-secondary leading-relaxed font-sans">{item.summary}</p>
          </GlassCard>
        )}

        <div className="mt-5 text-sm text-ink leading-relaxed whitespace-pre-wrap space-y-3 font-sans">
          {(item.content || '').split('\n').filter(Boolean).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        {item.tags && item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-5 pt-3 border-t border-ink-border/30">
            {item.tags.map((t, i) => (
              <span key={i} className="text-xs glass-card px-2 py-0.5 rounded-full text-ink-muted">#{t}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
