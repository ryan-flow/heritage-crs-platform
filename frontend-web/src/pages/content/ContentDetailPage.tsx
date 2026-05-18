import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Heart, Eye, Tag, ChevronRight } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { ContentItem } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';
import FloatingAiButton from '../../components/ui/FloatingAiButton';

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

  // 猜你喜欢：相同分类的其他内容
  const { data: relatedData } = useQuery({
    queryKey: ['related-contents', item?.category],
    queryFn: () => apiRequest<{ code: number; data: ContentItem[] }>(`/contents/?category=${item?.category || ''}&limit=4`),
    enabled: !!item?.category,
  });
  const relatedItems = (relatedData?.data || []).filter((r: ContentItem) => r.id !== Number(id)).slice(0, 3);

  useEffect(() => {
    if (id && session?.userId) {
      apiRequest('/recommend/track', {
        method: 'POST',
        data: { user_id: session.userId, action: 'view', target_type: 'content', target_id: Number(id), source_scene: 'content_detail' },
      }).catch(() => {});
    }
  }, [id, session?.userId]);

  // Key 随加载状态变化，触发入场动画
  const loadKey = isLoading ? 'loading' : `loaded-${id}`;

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
    <div className="pb-12 page-enter" key={loadKey}>
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
          {item.category && <SealBadge variant="jade">{item.category}</SealBadge>}
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

        {/* Content Body — prose-serif 排版系统 */}
        <div className="mt-5 prose-serif whitespace-pre-wrap space-y-1">
          {(item.content || item.summary || '').split('\n').filter(Boolean).map((p, i) => (
            <p key={i} className={i > 0 ? 'first:!text-inherit first:!float-none' : ''}>{p}</p>
          ))}
        </div>

        {/* Source */}
        {item.source_site && (
          <p className="mt-6 pt-3 text-xs text-ink-muted border-t border-ink-muted/15">
            来源：{item.source_site}
          </p>
        )}
      </div>

      {/* ═══════════════════════════════════════
          猜你喜欢 — 同分类推荐文章
         ═══════════════════════════════════════ */}
      {relatedItems.length > 0 && (
        <div className="px-4 mt-8 animate-fade-in-up">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-bold text-ink flex items-center gap-2">
              <span className="text-jade-500">📖</span> 猜你喜欢
            </h3>
            <button onClick={() => navigate('/content')}
              className="text-xs text-brand font-semibold border-none bg-transparent cursor-pointer inline-flex items-center gap-0.5 hover:gap-1.5 transition-all">
              更多 <ChevronRight size={12} />
            </button>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 snap-x snap-mandatory scrollbar-hide">
            {relatedItems.map((r: ContentItem) => (
              <button key={r.id} onClick={() => { navigate(`/content/${r.id}`); window.scrollTo(0, 0); }}
                className="snap-start shrink-0 w-[160px] rounded-[18px] overflow-hidden text-left border-none bg-white cursor-pointer group
                  transition-all duration-200 hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                  boxShadow: '0 8px 20px rgba(121,58,31,0.06)',
                  border: '1px solid rgba(219,191,155,0.18)',
                }}>
                <div className="h-[100px] bg-parchment-dark overflow-hidden">
                  {r.cover_url ? (
                    <CoverImage coverUrl={r.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-2xl opacity-30">📖</div>
                  )}
                </div>
                <div className="p-3">
                  <h4 className="text-[13px] font-bold text-ink leading-snug line-clamp-2 mb-1
                    transition-colors group-hover:text-brand">{r.title}</h4>
                  {r.category && (
                    <span className="text-[10px] text-jade-600 bg-jade-50 px-2 py-0.5 rounded-full font-medium">{r.category}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <FloatingAiButton context={item?.title} />
    </div>
  );
}
