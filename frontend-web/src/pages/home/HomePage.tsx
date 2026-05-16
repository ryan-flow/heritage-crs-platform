import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, MapPin, Clock, MessageSquare, BookOpen, Sparkles, ChevronRight, Calendar } from 'lucide-react';
import { apiRequest, shortenReason } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { RecommendData, ContentItem, Activity, DiscussionTopic } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';

/* ── 功能区名片配置 ── */
const QUICK_ENTRIES = [
  { label: '非遗文化', note: '策展精选', icon: BookOpen, path: '/culture', bg: '#fff5eb', hue: 'culture' },
  { label: '非遗场馆', note: '线下体验', icon: MapPin, path: '/places', bg: '#f5f0e8', hue: 'place' },
  { label: '浏览历史', note: '足迹回顾', icon: Clock, path: '/history', bg: '#f0f0f5', hue: 'history' },
  { label: 'AI 对话', note: '黑塔导览', icon: MessageSquare, path: '/ai', bg: '#fff0ec', hue: 'ai' },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const { data, isLoading } = useQuery({
    queryKey: ['recommend', 'home'],
    queryFn: () => apiRequest<{ code: number; data: RecommendData }>(`/recommend/?user_id=${session?.userId}&scene=home`),
    enabled: !!session?.userId,
  });
  const recommend = data?.data || { guide_text: '', contents: [], events: [], topics: [], profile_summary: null };
  const crsState = (recommend as Record<string, unknown>).crs_state as Record<string, unknown> || {};
  const crsMode = (crsState.mode as string) || 'cold_start';
  const confidence = Math.round(Number(crsState.stage_progress_percent || 0));
  const mood = crsMode === 'precision' ? 'confident' : crsMode === 'mixed' ? 'thinking' : 'curious';
  const firstContent = recommend.contents?.[0];

  const trackClick = async (type: string, id: number, scene = 'home_page') => {
    try { await apiRequest('/recommend/track', { method: 'POST', data: { user_id: session?.userId, action: 'click', target_type: type, target_id: id, source_scene: scene } }); } catch {}
  };

  return (
    <div className="home-page px-4 sm:px-6 pb-10 space-y-5 max-w-2xl mx-auto">

      {/* ═══════════════════════════════════════
         Hero 区 — 黑塔数字人导览
         布局：数字人居中在上 → 文字块在下
         ═══════════════════════════════════════ */}
      <section className="home-hero relative rounded-[36px] px-5 pt-8 pb-6 flex flex-col items-center text-center overflow-hidden"
        style={{
          background: 'linear-gradient(160deg, #5c1a1a 0%, #9f2d22 30%, #b34130 55%, #8b4513 100%)',
          boxShadow: '0 22px 46px rgba(127,29,29,0.30)',
        }}>
        {/* 装饰光晕 */}
        <div className="absolute -top-16 -right-16 w-52 h-52 rounded-full bg-white/[0.03] blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 -left-10 w-40 h-40 rounded-full bg-amber-400/[0.04] blur-2xl pointer-events-none" />
        <div className="absolute top-1/4 right-1/4 w-2 h-2 rounded-full bg-white/25 ping-slow pointer-events-none" />
        <div className="absolute bottom-1/3 left-1/4 w-1.5 h-1.5 rounded-full bg-amber-200/20 ping-slow pointer-events-none" style={{ animationDelay: '1.5s' }} />

        {/* 数字人 — 居中 220px */}
        <div className="relative z-10">
          <DigitalHumanModel variant="hero" mood={mood} size={220} greeting="来跟我聊聊吧！" />
        </div>

        {/* 文字块 — 位于数字人下方 */}
        <div className="relative z-10 animate-fade-in-up max-w-[280px] mt-2">
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-semibold tracking-[0.6px] text-amber-200 bg-white/[0.14] backdrop-blur-sm mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-200 animate-pulse" />
            数字导览中枢
          </span>
          <h2 className="text-[26px] font-extrabold text-[#fff8f1] leading-tight mb-2"
            style={{ textShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
            和黑塔聊聊非遗
          </h2>
          <p className="text-sm text-white/85 mb-4 leading-relaxed">
            {crsMode === 'precision'
              ? '已为你准备好个性化推荐'
              : crsMode === 'mixed'
              ? '正在探索你的兴趣偏好'
              : '让我来了解你喜欢什么'}
          </p>
          <InkButton variant="primary" size="md" onClick={() => navigate('/ai')}
            className="shadow-lg shadow-amber-900/20 hover:shadow-amber-900/30 whitespace-nowrap">
            <Sparkles size={14} /> 开始对话 <ArrowRight size={14} />
          </InkButton>
        </div>
      </section>

      {/* ═══════════════════════════════════════
         引导语
         ═══════════════════════════════════════ */}
      {recommend.guide_text && (
        <GlassCard className="px-6 py-5 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <p className="m-0 text-sm text-ink-secondary leading-relaxed">{recommend.guide_text}</p>
        </GlassCard>
      )}

      {/* ═══════════════════════════════════════
         快捷入口 Grid — 统一高度防换行
         ═══════════════════════════════════════ */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
        {QUICK_ENTRIES.map((item, i) => {
          const Icon = item.icon;
          return (
            <button key={item.path} onClick={() => navigate(item.path)}
              className="quick-entry-card relative rounded-[24px] p-4 border-none cursor-pointer text-left flex flex-col gap-1
                transition-all duration-300 ease-out min-h-[96px]
                hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
              style={{
                background: item.bg,
                boxShadow: '0 14px 34px rgba(121,58,31,0.08)',
                animationDelay: `${0.2 + i * 0.08}s`,
              }}>
              <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-white/60 backdrop-blur-sm text-brand">
                <Icon size={18} />
              </div>
              <span className="text-[15px] font-bold text-ink leading-tight">{item.label}</span>
              <span className="text-[12px] text-ink-muted leading-tight">{item.note}</span>
            </button>
          );
        })}
      </div>

      {/* ═══════════════════════════════════════
         加载状态
         ═══════════════════════════════════════ */}
      {isLoading ? (
        <div className="space-y-3.5 animate-fade-in-up">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-[120px] rounded-2xl skeleton" style={{ animationDelay: `${i * 0.1}s` }} />
          ))}
        </div>
      ) : (
        <>
          {/* ═══════════════════════════════════════
             精选推荐 — 横版信息流布局
             ═══════════════════════════════════════ */}
          {firstContent && (
            <GlassCard elevated hover className="px-6 py-5 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center justify-between mb-3.5">
                <div className="flex items-center gap-2">
                  <Sparkles size={14} className="text-gold" />
                  <span className="text-lg font-extrabold text-ink">精选推荐</span>
                </div>
                <span className="seal-badge seal-badge-cinnabar">文化</span>
              </div>
              <button onClick={() => { trackClick('content', firstContent.id); navigate(`/content/${firstContent.id}`); }}
                className="w-full border-none bg-transparent p-0 cursor-pointer text-left flex gap-3.5 group">
                <div className="w-[114px] h-[78px] rounded-2xl overflow-hidden shrink-0 bg-parchment-dark
                  transition-transform duration-300 group-hover:scale-105"
                  style={{ boxShadow: '0 6px 16px rgba(121,58,31,0.08)' }}>
                  {firstContent.cover_url
                    ? <CoverImage coverUrl={firstContent.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" fallback={<span className="text-3xl">📜</span>} />
                    : <span className="w-full h-full flex items-center justify-center text-3xl">📜</span>}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-[17px] font-extrabold text-ink mb-1.5 leading-snug
                    transition-colors duration-300 group-hover:text-brand">{firstContent.title}</h3>
                  <p className="text-xs text-ink-muted leading-relaxed line-clamp-2">
                    {shortenReason(firstContent.reason, firstContent.summary || '')}
                  </p>
                </div>
              </button>
            </GlassCard>
          )}

          {/* ═══════════════════════════════════════
             文化内容 — 横版信息流（图片左 + 文字右）
             ═══════════════════════════════════════ */}
          {recommend.contents && recommend.contents.length > 1 && (
            <section className="animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
              <SectionHeader title="文化内容" onViewAll={() => navigate('/content')} />
              <div className="space-y-3">
                {recommend.contents.slice(1, 6).map((item: ContentItem, i: number) => (
                  <GlassCard key={item.id} hover className="px-4 py-3 group">
                    <button onClick={() => { trackClick('content', item.id); navigate(`/content/${item.id}`); }}
                      className="w-full border-none bg-transparent p-0 cursor-pointer text-left flex gap-3.5 items-center">
                      <div className="w-[100px] h-[68px] rounded-xl overflow-hidden shrink-0 bg-parchment-dark
                        transition-transform duration-300 group-hover:scale-105">
                        {item.cover_url
                          ? <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" fallback={<BookOpen size={22} className="text-ink-muted/40 m-auto mt-[23px]" />} />
                          : <BookOpen size={22} className="text-ink-muted/40 m-auto mt-[23px]" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[15px] font-bold text-ink mb-1 line-clamp-2 leading-snug
                          transition-colors duration-300 group-hover:text-brand">{item.title}</h4>
                        <p className="text-xs text-ink-muted line-clamp-1 leading-relaxed">
                          {shortenReason(item.reason, item.summary || '')}
                        </p>
                      </div>
                    </button>
                  </GlassCard>
                ))}
              </div>
            </section>
          )}

          {/* ═══════════════════════════════════════
             推荐活动 — 横版（方形封面左 + 信息右）
             ═══════════════════════════════════════ */}
          {recommend.events && recommend.events.length > 0 && (
            <section className="animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
              <SectionHeader title="推荐活动" onViewAll={() => navigate('/activity')} />
              <div className="space-y-3">
                {recommend.events.slice(0, 3).map((item: Activity, i: number) => (
                  <GlassCard key={item.id} hover className="px-4 py-3 group">
                    <button onClick={() => { trackClick('event', item.id); navigate(`/activity/${item.id}`); }}
                      className="w-full border-none bg-transparent p-0 cursor-pointer text-left flex gap-3.5 items-center">
                      <div className="w-[72px] h-[72px] rounded-xl shrink-0 overflow-hidden bg-parchment-dark
                        transition-transform duration-300 group-hover:scale-105">
                        {item.cover_url
                          ? <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" fallback={<Calendar size={22} className="text-ink-muted/40 m-auto mt-[25px]" />} />
                          : <Calendar size={22} className="text-ink-muted/40 m-auto mt-[25px]" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-[15px] font-bold text-ink mb-1
                          transition-colors duration-300 group-hover:text-brand">{item.title}</h4>
                        <p className="text-[11px] text-ink-muted mb-0.5">
                          <MapPin size={10} className="inline mr-1" />{item.location} · {item.start_time?.slice(0, 10)}
                        </p>
                        <p className="text-[11px] text-ink-muted line-clamp-1">{shortenReason(item.reason, '')}</p>
                      </div>
                    </button>
                  </GlassCard>
                ))}
              </div>
            </section>
          )}

          {/* ═══════════════════════════════════════
             社区讨论
             ═══════════════════════════════════════ */}
          {recommend.topics && recommend.topics.length > 0 && (
            <section className="animate-fade-in-up" style={{ animationDelay: '0.35s' }}>
              <SectionHeader title="社区讨论" onViewAll={() => navigate('/discussion')} />
              <div className="space-y-2.5">
                {recommend.topics.slice(0, 3).map((item: DiscussionTopic, i: number) => (
                  <GlassCard key={item.id} hover className="px-5 py-4">
                    <button onClick={() => { trackClick('topic', item.id); navigate(`/discussion/${item.id}`); }}
                      className="w-full border-none bg-transparent p-0 cursor-pointer text-left">
                      <h4 className="text-[15px] font-bold text-ink mb-1.5
                        transition-colors duration-300 hover:text-brand">{item.title}</h4>
                      <p className="text-[13px] text-ink-secondary mb-2 line-clamp-2 leading-relaxed">
                        {item.content?.replace(/<[^>]*>/g, '').slice(0, 140)}
                      </p>
                      <div className="flex gap-3.5 text-[11px] text-ink-muted">
                        <span>👍 {item.like_count || 0}</span>
                        <span>💬 {item.comment_count || 0}</span>
                        {item.nickname && <span className="text-ink-muted">{item.nickname}</span>}
                      </div>
                    </button>
                  </GlassCard>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

/* ── Section Header 提取为子组件 ── */
function SectionHeader({ title, onViewAll }: { title: string; onViewAll: () => void }) {
  return (
    <div className="flex justify-between items-center mb-3 px-1">
      <span className="text-h4 font-bold text-ink">{title}</span>
      <button onClick={onViewAll}
        className="text-[13px] text-brand font-semibold border-none bg-transparent cursor-pointer
          transition-all duration-200 hover:text-brand-deep hover:gap-1.5 inline-flex items-center gap-0.5">
        全部 <ChevronRight size={14} className="inline transition-transform duration-200" />
      </button>
    </div>
  );
}
