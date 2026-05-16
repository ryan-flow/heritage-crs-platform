import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Tag, MapPin } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
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
        {[1, 2, 3].map(i => (
          <SkeletonLoader key={i} variant="text" />
        ))}
      </div>
    );
  }

  if (!item) {
    return (
      <div className="px-4 py-20 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-parchment-dark flex items-center justify-center">
          <span className="text-2xl opacity-40">?</span>
        </div>
        <p className="text-ink-muted font-sans">内容不存在</p>
        <button onClick={() => navigate(-1)} className="text-brand text-sm mt-2 hover:underline font-sans">
          返回
        </button>
      </div>
    );
  }

  return (
    <div className="pb-8">

      {/* Cover Image Area */}
      {item.cover_url ? (
        <div className="relative h-48 bg-parchment-dark overflow-hidden rounded-2xl mx-4 mt-4">
          <CoverImage coverUrl={item.cover_url} alt={item.title} className="w-full h-full object-cover" />
          {/* Gradient overlay for back button visibility */}
          <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-black/40 to-transparent pointer-events-none" />
          <button
            onClick={() => navigate(-1)}
            className="absolute top-4 left-4 p-2 glass-card rounded-xl z-10 animate-fade-in-up"
          >
            <ArrowLeft size={18} className="text-ink" />
          </button>
        </div>
      ) : (
        /* No-cover hero banner */
        <div className="mx-4 mt-4 rounded-[36px] bg-gradient-to-br from-cinnabar-700 via-brand to-gold-400 p-6 pb-8 animate-fade-in-up">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-1 text-sm text-white/80 hover:text-white transition-colors mb-3 font-sans"
          >
            <ArrowLeft size={16} /> 返回
          </button>
          <h1 className="text-xl font-serif font-bold text-white leading-snug">{item.title}</h1>
        </div>
      )}

      <div className="px-4">
        {/* Back button when no cover */}
        {!item.cover_url && (
          <div className="hidden">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1 text-sm text-ink-secondary mt-4 hover:text-ink transition-colors font-sans"
            >
              <ArrowLeft size={16} /> 返回
            </button>
          </div>
        )}

        {/* Title (when cover exists; no-cover already has title in hero) */}
        {item.cover_url && (
          <h1 className="text-xl font-serif font-bold text-ink mt-4 leading-snug animate-fade-in-up">
            {item.title}
          </h1>
        )}

        {/* Category & Region */}
        <div className="flex items-center gap-2 mt-2 text-xs text-ink-muted animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          {item.category && <SealBadge variant="gold">{item.category}</SealBadge>}
          {item.region && (
            <span className="inline-flex items-center gap-1 font-sans">
              <MapPin size={12} className="text-cinnabar-500" /> {item.region}
            </span>
          )}
        </div>

        {/* Summary Card */}
        {item.summary && (
          <GlassCard className="mt-4 !p-3.5 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
            <p className="text-sm text-ink-secondary leading-relaxed font-sans">{item.summary}</p>
          </GlassCard>
        )}

        {/* Content Body */}
        <div
          className="mt-5 text-sm text-ink leading-relaxed whitespace-pre-wrap space-y-3 font-sans animate-fade-in-up"
          style={{ animationDelay: '0.2s' }}
        >
          {(item.content || '').split('\n').filter(Boolean).map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>

        {/* Tags */}
        {item.tags && item.tags.length > 0 && (
          <div
            className="flex flex-wrap gap-1.5 mt-5 pt-4 border-t border-[rgba(219,191,155,0.25)] animate-fade-in-up"
            style={{ animationDelay: '0.25s' }}
          >
            {item.tags.map((t, i) => (
              <span key={i} className="text-xs glass-card px-2.5 py-1 rounded-full text-ink-muted font-sans">
                #{t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
