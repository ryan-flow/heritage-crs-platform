import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Heart, Eye, Tag } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { ContentItem } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function ContentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { session } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ['content', id],
    queryFn: () => apiRequest<{ code: number; data: ContentItem }>(`/contents/${id}`),
    enabled: !!id,
  });

  const item = data?.data;

  useEffect(() => {
    if (id && session?.userId) {
      apiRequest('/recommend/track', {
        method: 'POST',
        data: { user_id: session.userId, action: 'view', target_type: 'content', target_id: Number(id), source_scene: 'content_detail' },
      }).catch(() => {});
    }
  }, [id, session?.userId]);

  if (isLoading) {
    return (
      <div className="px-4 py-4 space-y-3">
        <SkeletonLoader variant="image" className="!h-56" />
        <SkeletonLoader variant="text" className="!w-3/4" />
        <SkeletonLoader variant="text" className="!w-1/2" />
        {[1, 2, 3, 4, 5].map(i => <SkeletonLoader key={i} variant="text" />)}
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
        <div className="h-56 bg-parchment-dark relative">
          <CoverImage coverUrl={item.cover_url} alt={item.title} className="w-full h-full object-cover" />
          <div className="absolute top-4 left-4">
            <button onClick={() => navigate(-1)} className="p-2 glass-card rounded-xl backdrop-blur-md">
              <ArrowLeft size={18} className="text-ink" />
            </button>
          </div>
        </div>
      )}

      <div className="px-4">
        {!item.cover_url && (
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary mt-4 hover:text-ink transition-colors">
            <ArrowLeft size={16} /> 返回
          </button>
        )}

        <h1 className="text-xl font-serif font-bold text-ink mt-4 leading-snug">{item.title}</h1>

        <div className="flex items-center flex-wrap gap-2 mt-3 text-xs text-ink-muted">
          {item.category && <SealBadge variant="gold">{item.category}</SealBadge>}
          {item.region && <span className="flex items-center gap-1"><Tag size={12} /> {item.region}</span>}
          <span className="flex items-center gap-1"><Eye size={12} /> {item.view_count || 0}</span>
          <span className="flex items-center gap-1"><Heart size={12} /> {item.like_count || 0}</span>
        </div>

        {item.chapter && (
          <GlassCard className="mt-3 p-3 text-xs text-ink-secondary">
            <span className="font-medium text-ink">章节：</span>
            {item.chapter}{item.sub_chapter ? ` · ${item.sub_chapter}` : ''}
          </GlassCard>
        )}

        {item.tags && item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {item.tags.map((t, i) => (
              <span key={i} className="text-xs glass-card px-2 py-0.5 rounded-full text-ink-muted">{t}</span>
            ))}
          </div>
        )}

        <div className="mt-5 text-sm text-ink leading-relaxed whitespace-pre-wrap space-y-3 font-sans">
          {(item.content || item.summary || '').split('\n').filter(Boolean).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        {item.source_site && (
          <p className="mt-6 text-xs text-ink-muted border-t border-ink-border/30 pt-3">
            来源：{item.source_site}
          </p>
        )}
      </div>
    </div>
  );
}
