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
        <span className="text-4xl opacity-20 block mb-4">📖</span>
        <p className="text-ink-muted text-sm">内容不存在</p>
        <button onClick={() => navigate(-1)} className="text-cinnabar-600 text-sm mt-2 hover:underline transition-colors">返回</button>
      </div>
    );
  }

  return (
    <div className="pb-8">
      {/* Hero Image Area */}
      {item.cover_url ? (
        <div className="h-56 bg-parchment-dark relative">
          <CoverImage coverUrl={item.cover_url} alt={item.title} className="w-full h-full object-cover" />
          <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-black/30 to-transparent pointer-events-none" />
          <div className="absolute top-4 left-4">
            <GlassCard as="button" onClick={() => navigate(-1)} className="p-2 rounded-xl cursor-pointer backdrop-blur-md">
              <ArrowLeft size={18} className="text-ink" />
            </GlassCard>
          </div>
        </div>
      ) : (
        /* No Cover Fallback */
        <div className="h-40 bg-gradient-to-b from-parchment-dark/60 to-parchment-dark/20 flex items-end px-4 pb-2">
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary hover:text-ink transition-colors mb-2">
            <ArrowLeft size={16} /> 返回
          </button>
        </div>
      )}

      <div className="px-4">
        {/* Title */}
        <h1 className="text-xl font-serif font-bold text-ink mt-4 leading-snug">{item.title}</h1>

        {/* Meta Row */}
        <div className="flex items-center flex-wrap gap-2 mt-3 text-xs text-ink-muted">
          {item.category && <SealBadge variant="gold">{item.category}</SealBadge>}
          {item.region && (
            <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-parchment-dark/50 text-ink-secondary">
              <Tag size={11} /> {item.region}
            </span>
          )}
          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-parchment-dark/50 text-ink-secondary">
            <Eye size={11} /> {item.view_count || 0}
          </span>
          <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-parchment-dark/50 text-ink-secondary">
            <Heart size={11} /> {item.like_count || 0}
          </span>
        </div>

        {/* Chapter Info */}
        {item.chapter && (
          <GlassCard className="mt-3 p-3 text-xs text-ink-secondary">
            <span className="font-medium text-ink">章节：</span>
            {item.chapter}{item.sub_chapter ? ` · ${item.sub_chapter}` : ''}
          </GlassCard>
        )}

        {/* Tags */}
        {item.tags && item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {item.tags.map((t, i) => (
              <span key={i} className="text-xs px-2.5 py-0.5 rounded-full bg-parchment-dark/60 text-ink-muted border border-gold-200/30 font-sans">
                #{t}
              </span>
            ))}
          </div>
        )}

        {/* Content Body */}
        <div className="mt-5 text-sm text-ink leading-relaxed whitespace-pre-wrap space-y-3 font-sans">
          {(item.content || item.summary || '').split('\n').filter(Boolean).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        {/* Source */}
        {item.source_site && (
          <p className="mt-6 pt-3 text-xs text-ink-muted border-t border-ink-muted/15">
            来源：{item.source_site}
          </p>
        )}
      </div>
    </div>
  );
}
