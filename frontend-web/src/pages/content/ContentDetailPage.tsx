import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ChevronRight } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { ContentItem } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
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

  // 解析 displayBlocks 数据
  const displayBlocks = item.displayBlocks || {};
  const highlights = displayBlocks.highlights || [];
  const readingTips = displayBlocks.reading_tips || [];
  const introText = displayBlocks.intro || item.summary || '';
  const bodyText = item.content || item.summary || '';

  return (
    <div className="pb-12 page-enter" key={loadKey}>
      {/* ═══════════════════════════════════════
          Cover Image Hero — 小程序同款设计
         ═══════════════════════════════════════ */}
      {item.cover_url ? (
        <div className="relative h-[220px] overflow-hidden">
          <CoverImage coverUrl={item.cover_url} alt={item.title} className="w-full h-full object-cover" />
          {/* 渐变遮罩 */}
          <div className="absolute inset-0 bg-gradient-to-b from-[rgba(16,10,8,0.08)] to-[rgba(18,9,6,0.68)]" />
          {/* 返回按钮 */}
          <div className="absolute top-4 left-4">
            <GlassCard as="button" onClick={() => navigate(-1)} className="p-2 rounded-xl cursor-pointer backdrop-blur-md">
              <ArrowLeft size={18} className="text-white" />
            </GlassCard>
          </div>
          {/* 封面上的标题信息 */}
          <div className="absolute left-4 right-4 bottom-5">
            <span className="inline-block px-2.5 py-1 rounded-full bg-[rgba(255,245,230,0.18)] text-[#ffe1b7] text-xs mb-2">
              {item.chapter || '非遗文化'}
            </span>
            <h1 className="text-xl font-bold text-[#fff8f2] leading-snug mb-1">{item.title}</h1>
            <p className="text-sm text-[rgba(255,242,231,0.86)]">
              {item.sub_chapter || item.content_type || '中国非遗精选'}
            </p>
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
        {/* ═══════════════════════════════════════
            元信息标签条
           ═══════════════════════════════════════ */}
        <div className="flex flex-wrap gap-2 pt-4 pb-2">
          <span className="chip !bg-[#f5e7d6] !text-[#8b6139] !min-h-0 !py-0.5 !px-2.5 !text-[11px]">
            {item.chapter || '非遗文化'}
          </span>
          <span className="chip !bg-[#f5e7d6] !text-[#8b6139] !min-h-0 !py-0.5 !px-2.5 !text-[11px]">
            {item.sub_chapter || item.content_type || '专题导读'}
          </span>
        </div>

        {/* ═══════════════════════════════════════
            导览摘要
           ═══════════════════════════════════════ */}
        {introText && (
          <div className="py-4 border-b border-[rgba(133,97,63,0.10)]">
            <h2 className="text-sm font-bold text-[#38261a] mb-2.5">导览摘要</h2>
            <p className="text-[13px] text-[#6f5540] leading-relaxed">{introText}</p>
          </div>
        )}

        {/* ═══════════════════════════════════════
            三分钟看点
           ═══════════════════════════════════════ */}
        {highlights.length > 0 && (
          <div className="py-4 border-b border-[rgba(133,97,63,0.10)]">
            <h2 className="text-sm font-bold text-[#38261a] mb-2.5">三分钟看点</h2>
            {highlights.map((h: string, i: number) => (
              <p key={i} className="text-[13px] text-[#6b513b] leading-relaxed mb-2">
                {i + 1}. {h}
              </p>
            ))}
          </div>
        )}

        {/* ═══════════════════════════════════════
            阅读建议
           ═══════════════════════════════════════ */}
        {readingTips.length > 0 && (
          <div className="py-4 border-b border-[rgba(133,97,63,0.10)] bg-[rgba(247,240,227,0.72)] -mx-4 px-4">
            <h2 className="text-sm font-bold text-[#38261a] mb-2.5">阅读建议</h2>
            {readingTips.map((tip: string, i: number) => (
              <p key={i} className="text-[13px] text-[#6b513b] leading-relaxed mb-2">
                {tip}
              </p>
            ))}
          </div>
        )}

        {/* ═══════════════════════════════════════
            延展讲解
           ═══════════════════════════════════════ */}
        {bodyText && (
          <div className="py-4">
            <h2 className="text-sm font-bold text-[#38261a] mb-2.5">延展讲解</h2>
            <div className="text-[13px] text-[#5a4430] leading-relaxed whitespace-pre-wrap">
              {bodyText}
            </div>
          </div>
        )}

        {/* 来源 */}
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
                className="snap-start shrink-0 w-[160px] rounded-[14px] overflow-hidden text-left border-none cursor-pointer group
                  transition-all duration-200 hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: 'rgba(255, 251, 245, 0.96)',
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
