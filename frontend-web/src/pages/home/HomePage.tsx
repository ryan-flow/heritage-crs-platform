import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Clock, MessageSquare, BookOpen, Sparkles, ChevronRight, Calendar, Heart, TrendingUp } from 'lucide-react';
import { apiRequest, shortenReason } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { RecommendData, ContentItem, Activity, DiscussionTopic } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';

/* ── CRS mode 显示映射 ── */
const CRS_MODE_META: Record<string, { label: string; color: string; bg: string }> = {
  cold_start: { label: '冷启动', color: '#8c6a42', bg: 'rgba(160,136,104,0.12)' },
  mixed: { label: '混合推荐', color: '#7b5a32', bg: 'rgba(140,106,66,0.12)' },
  precision: { label: '精准推荐', color: '#9f2d22', bg: 'rgba(159,45,34,0.10)' },
};

export default function HomePage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const { data, isLoading } = useQuery({
    queryKey: ['recommend', 'home'],
    queryFn: () => apiRequest<{ code: number; data: RecommendData }>(`/recommend/?user_id=${session?.userId}&scene=home`),
    enabled: !!session?.userId,
  });
  const recommend = data?.data || { contents: [], events: [], topics: [], profile_summary: null };
  const crsState = (recommend as Record<string, unknown>).crs_state as Record<string, unknown> || {};
  const crsMode = (crsState.mode as string) || 'cold_start';
  const crsConfidence = (crsState.confidence as number) || 0;
  const strategySummary = (crsState.strategy_summary as string) || '';
  const mood = crsMode === 'precision' ? 'confident' : crsMode === 'mixed' ? 'thinking' : 'curious';
  const modeMeta = CRS_MODE_META[crsMode] || CRS_MODE_META.cold_start;
  const firstContent = recommend.contents?.[0];
  const restContents = recommend.contents?.slice(1, 3) || [];
  const events = recommend.events?.slice(0, 2) || [];
  const topics = recommend.topics?.slice(0, 2) || [];

  const trackClick = async (type: string, id: number, scene = 'home_page') => {
    try { await apiRequest('/recommend/track', { method: 'POST', data: { user_id: session?.userId, action: 'click', target_type: type, target_id: id, source_scene: scene } }); } catch {}
  };

  return (
    <div className="home-page px-4 sm:px-6 pb-10 space-y-4 max-w-2xl mx-auto">

      {/* ═══════════════════════════════════════
         Hero — 双栏布局：左文右图（对标小程序 .ai-hero）
         ═══════════════════════════════════════ */}
      <section className="hero-section relative rounded-[24px] flex items-center overflow-hidden px-4 py-3 gap-2"
        style={{
          background: 'linear-gradient(135deg, #5B3A7A 0%, #6B3A5B 35%, #7a4020 65%, #8B4513 100%)',
          boxShadow: '0 22px 46px rgba(65, 32, 92, 0.24)',
          minHeight: '180px',
        }}>
        {/* 装饰光晕 */}
        <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-white/[0.04] blur-3xl pointer-events-none" />
        <div className="absolute -bottom-4 -left-4 w-32 h-32 rounded-full bg-amber-400/[0.05] blur-2xl pointer-events-none" />

        {/* 左侧文字区 56% */}
        <div className="relative z-10 flex-[0.56] flex flex-col gap-0.5 min-w-0">
          <span className="self-start inline-flex items-center gap-1 px-[9px] py-[4px] rounded-full text-[11px] font-semibold tracking-[0.5px] text-[#ffd8a8] mb-1"
            style={{ background: 'rgba(255, 247, 236, 0.16)' }}>
            <span className="w-1.5 h-1.5 rounded-full bg-[#ffd8a8] animate-pulse" />
            数字导览中枢
          </span>
          <h2 className="text-[22px] font-extrabold text-[#fff8f1] leading-[1.22]"
            style={{ textShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
            和黑塔聊聊非遗
          </h2>
          <p className="text-[12px] leading-[1.5] text-[rgba(255,244,232,0.92)]">
            {crsMode === 'precision'
              ? '已为你准备好个性化推荐'
              : crsMode === 'mixed'
                ? '正在探索你的兴趣偏好'
                : '让我来了解你喜欢什么'}
          </p>
          {/* CRS 模式标签 */}
          {crsMode !== 'cold_start' && (
            <span className="self-start inline-flex items-center gap-1 mt-1 px-[9px] py-[4px] rounded-full text-[11px] font-semibold"
              style={{ color: modeMeta.color, background: modeMeta.bg }}>
              <TrendingUp size={10} />
              {modeMeta.label} · {Math.round(crsConfidence * 100)}%
            </span>
          )}
          <button onClick={() => navigate('/ai')}
            className="inline-flex items-center gap-1.5 mt-2.5 px-5 py-[7px] rounded-full text-[13px] font-extrabold border-none cursor-pointer transition-all duration-200 hover:shadow-lg active:translate-y-[1px] active:scale-[0.985] self-start tracking-[1px]"
            style={{
              background: 'linear-gradient(135deg, #ffd39a, #ffb765)',
              color: '#5d2410',
              boxShadow: '0 4px 12px rgba(255, 183, 101, 0.3)',
            }}>
            开始对话 →
          </button>
        </div>

        {/* 右侧数字人 44% — 下沉效果对标小程序 translateY(66rpx) */}
        <div className="relative z-10 flex-[0.44] flex justify-center items-center translate-y-[20px]">
          <DigitalHumanModel variant="hero" mood={mood} size={130} greeting="" />
        </div>
      </section>

      {/* Hero → 内容区渐变过渡条 */}
      <div className="h-5 -mt-3 -mx-4 sm:-mx-6 relative pointer-events-none"
        style={{
          background: 'linear-gradient(180deg, #7a2a1a 0%, rgba(159,45,34,0.25) 50%, transparent 100%)',
          maskImage: 'linear-gradient(90deg, transparent 3%, black 20%, black 80%, transparent 97%)',
          WebkitMaskImage: 'linear-gradient(90deg, transparent 3%, black 20%, black 80%, transparent 97%)',
        }} />

      {/* ═══════════════════════════════════════
         加载状态
         ═══════════════════════════════════════ */}
      {isLoading ? (
        <div className="space-y-3 animate-fade-in-up">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-[100px] rounded-2xl skeleton" style={{ animationDelay: `${i * 0.1}s` }} />
          ))}
        </div>
      ) : (
        <>
          {/* ═══════════════════════════════════════
             精选推荐（对标小程序 .today-focus-card）
             ═══════════════════════════════════════ */}
          {firstContent && (
            <GlassCard elevated hover className="px-5 py-4 animate-fade-in-up" style={{ animationDelay: '0.03s' }}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[16px] font-extrabold text-ink">精选推荐</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[var(--color-jade-50)] text-[var(--color-jade-600)]">
                  文化
                </span>
              </div>
              <button onClick={() => { trackClick('content', firstContent.id); navigate(`/content/${firstContent.id}`); }}
                className="w-full border-none bg-transparent p-0 cursor-pointer text-left flex gap-3 group">
                <div className="w-[114px] h-[78px] rounded-[14px] overflow-hidden shrink-0 bg-parchment-dark"
                  style={{ boxShadow: '0 6px 16px rgba(121,58,31,0.08)' }}>
                  {firstContent.cover_url
                    ? <CoverImage coverUrl={firstContent.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" fallback={<span className="text-3xl flex items-center justify-center h-full">📜</span>} />
                    : <span className="w-full h-full flex items-center justify-center text-3xl">📜</span>}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-[16px] font-extrabold text-ink mb-1 leading-snug
                    transition-colors duration-300 group-hover:text-brand">{firstContent.title}</h3>
                  <p className="text-[11px] text-ink-muted leading-relaxed line-clamp-2">
                    {shortenReason(firstContent.reason, firstContent.summary || '')}
                  </p>
                  {firstContent.reason && (
                    <span className="inline-block mt-1.5 text-[10px] text-accent font-medium bg-accent-soft/50 px-2 py-0.5 rounded-full">
                      推荐理由
                    </span>
                  )}
                </div>
              </button>
            </GlassCard>
          )}

          {/* ═══════════════════════════════════════
             今日推荐（对标小程序 .recommend-card）
             ═══════════════════════════════════════ */}
          <GlassCard elevated className="px-5 py-4 animate-fade-in-up" style={{ animationDelay: '0.08s' }}>
            {/* 标题行 + CRS 策略标签 */}
            <div className="flex items-center justify-between mb-3">
              <span className="text-[16px] font-extrabold text-ink">今日推荐</span>
              {crsMode !== 'cold_start' && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
                  style={{ color: modeMeta.color, background: modeMeta.bg }}>
                  <TrendingUp size={10} />
                  {modeMeta.label} · {Math.round(crsConfidence * 100)}%
                </span>
              )}
            </div>

            {/* 内容 split */}
            {restContents.length > 0 && (
              <div className="mb-3">
                <span className="text-[11px] font-semibold text-ink-muted tracking-[2px] mb-2 block">内容</span>
                <div className="space-y-2">
                  {restContents.map((item: ContentItem) => (
                    <button key={item.id} onClick={() => { trackClick('content', item.id); navigate(`/content/${item.id}`); }}
                      className="w-full border-none bg-transparent p-0 cursor-pointer text-left flex gap-3 items-center group">
                      <div className="w-[72px] h-[54px] rounded-[10px] overflow-hidden shrink-0 bg-parchment-dark">
                        {item.cover_url
                          ? <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" fallback={<BookOpen size={16} className="text-ink-muted/30 m-auto mt-[19px]" />} />
                          : <BookOpen size={16} className="text-ink-muted/30 m-auto mt-[19px]" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[13px] font-bold text-ink line-clamp-1 leading-snug
                          transition-colors duration-300 group-hover:text-brand">{item.title}</h4>
                        <p className="text-[10px] text-ink-muted line-clamp-1 mt-0.5">
                          {shortenReason(item.reason, item.summary || '')}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 活动 split */}
            {events.length > 0 && (
              <div className="mb-3">
                <span className="text-[11px] font-semibold text-ink-muted tracking-[2px] mb-2 block">活动</span>
                <div className="space-y-2">
                  {events.map((item: Activity) => (
                    <button key={item.id} onClick={() => { trackClick('event', item.id); navigate(`/activity/${item.id}`); }}
                      className="w-full border-none bg-transparent p-0 cursor-pointer text-left flex gap-3 items-center group">
                      <div className="w-[72px] h-[54px] rounded-[10px] overflow-hidden shrink-0 bg-parchment-dark">
                        {item.cover_url
                          ? <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" fallback={<Calendar size={16} className="text-ink-muted/30 m-auto mt-[19px]" />} />
                          : <Calendar size={16} className="text-ink-muted/30 m-auto mt-[19px]" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[13px] font-bold text-ink line-clamp-1 leading-snug
                          transition-colors duration-300 group-hover:text-brand">{item.title}</h4>
                        <p className="text-[10px] text-ink-muted mt-0.5">
                          <MapPin size={9} className="inline mr-0.5" />{item.location} · {item.start_time?.slice(0, 10)}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 讨论 split */}
            {topics.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold text-ink-muted tracking-[2px] mb-2 block">讨论</span>
                <div className="space-y-2">
                  {topics.map((item: DiscussionTopic) => (
                    <button key={item.id} onClick={() => { trackClick('topic', item.id); navigate(`/discussion/${item.id}`); }}
                      className="w-full border-none bg-transparent p-0 cursor-pointer text-left">
                      <h4 className="text-[13px] font-bold text-ink line-clamp-1 leading-snug
                        transition-colors duration-300 hover:text-brand">{item.title}</h4>
                      <div className="flex gap-3 text-[10px] text-ink-muted mt-0.5">
                        <span>👍 {item.like_count || 0}</span>
                        <span>💬 {item.comment_count || 0}</span>
                        {item.nickname && <span>{item.nickname}</span>}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 策略来源条 */}
            {strategySummary && (
              <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-[rgba(200,165,120,0.2)]">
                <Heart size={11} className="text-ink-muted/60" />
                <span className="text-[10px] text-ink-muted/70">兴趣来源：{strategySummary}</span>
              </div>
            )}
          </GlassCard>

          {/* ═══════════════════════════════════════
             快捷入口（2 列，对标小程序 .quick-grid）
             ═══════════════════════════════════════ */}
          <section className="animate-fade-in-up" style={{ animationDelay: '0.12s' }}>
            <span className="text-[16px] font-extrabold text-ink mb-3 block px-1">快速入口</span>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => navigate('/history')}
                className="quick-entry-btn rounded-[14px] px-4 py-3 border-none cursor-pointer text-left flex flex-col gap-1
                  transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: '#fff5eb',
                  boxShadow: '0 10px 24px rgba(121,58,31,0.06)',
                }}>
                <Clock size={16} className="text-brand" />
                <span className="text-[13px] font-bold text-ink">非遗发展史</span>
                <span className="text-[10px] text-ink-muted">时间轴回溯关键节点</span>
              </button>
              <button onClick={() => navigate('/places')}
                className="quick-entry-btn rounded-[14px] px-4 py-3 border-none cursor-pointer text-left flex flex-col gap-1
                  transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: '#f5f0e8',
                  boxShadow: '0 10px 24px rgba(121,58,31,0.06)',
                }}>
                <MapPin size={16} className="text-brand" />
                <span className="text-[13px] font-bold text-ink">非遗地点</span>
                <span className="text-[10px] text-ink-muted">规划体验目的地路线</span>
              </button>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
