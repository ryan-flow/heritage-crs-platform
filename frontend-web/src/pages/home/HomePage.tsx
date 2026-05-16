import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, MapPin, Clock, MessageSquare, BookOpen, Sparkles, ChevronRight, Calendar } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
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
  const [greeting, setGreeting] = useState('');
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

  const handleDigitalHumanGreeting = useCallback(() => {
    const greetings = ['来跟我聊聊吧！', '想知道非遗的秘密吗？', '点我探索非遗世界~', '今天想了解什么呢？'];
    const msg = greetings[Math.floor(Math.random() * greetings.length)];
    setGreeting(msg);
    setTimeout(() => setGreeting(''), 2800);
  }, []);

  return (
    <div className="home-page px-4 sm:px-6 pb-10 space-y-5 max-w-2xl mx-auto">

      {/* ═══════════════════════════════════════
         Hero 区 — 黑塔数字人导览
         ═══════════════════════════════════════ */}
      <section className="home-hero relative rounded-[36px] p-5 pb-0 min-h-[260px] flex items-end overflow-hidden
        before:absolute before:inset-0 before:pointer-events-none before:opacity-40
        before:bg-[radial-gradient(ellipse_at_20%_10%,rgba(255,215,170,0.12)_0%,transparent_50%),radial-gradient(ellipse_at_80%_70%,rgba(200,160,100,0.10)_0%,transparent_50%)]
        after:absolute after:inset-0 after:pointer-events-none
        after:bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMzAgMnYyNk0yIDI4aDU2IiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC4wNCkiIHN0cm9rZS13aWR0aD0iMC41IiBmaWxsPSJub25lIi8+PC9zdmc+')] after:bg-[length:60px_60px] after:opacity-30"
        style={{
          background: 'linear-gradient(135deg, #7f1d1d 0%, #b34130 40%, #8b4513 100%)',
          boxShadow: '0 22px 46px rgba(127,29,29,0.30)',
        }}>
        {/* 装饰光晕 */}
        <div className="absolute -top-12 -right-12 w-40 h-40 rounded-full bg-white/[0.04] blur-3xl" />
        <div className="absolute -bottom-8 -left-8 w-32 h-32 rounded-full bg-amber-400/[0.06] blur-2xl" />
        <div className="absolute top-1/4 right-1/3 w-2 h-2 rounded-full bg-white/30 ping-slow" />

        <div className="flex-[0_0_52%] pb-5 relative z-10 animate-fade-in-up">
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-semibold tracking-[0.6px] text-[#ffd8a8] bg-white/[0.16] backdrop-blur-sm mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-[#ffd8a8] animate-pulse" />
            数字导览中枢
          </span>
          <h2 className="text-[clamp(22px,5vw,32px)] font-extrabold text-[#fff8f1] leading-tight mb-2"
            style={{ textShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
            和黑塔聊聊非遗
          </h2>
          <p className="text-sm text-white/90 mb-4 leading-relaxed">
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
        <div className="flex-[0_0_48%] relative z-10 self-end translate-y-2">
          <DigitalHumanModel variant="hero" mood={mood} size={240} onSpeak={handleDigitalHumanGreeting} />
          {/* Greeting bubble */}
          {greeting && (
            <div className="absolute -top-2 right-0 bg-white/95 backdrop-blur-md text-[#5a3520] text-sm font-semibold px-4 py-2.5 rounded-[20px] rounded-br-md shadow-lg animate-fade-in-up"
              style={{ border: '1px solid rgba(200,155,100,0.3)', maxWidth: 180 }}>
              {greeting}
              <div className="absolute -bottom-1.5 right-5 w-3 h-3 bg-white/95 rotate-45"
                style={{ borderRight: '1px solid rgba(200,155,100,0.3)', borderBottom: '1px solid rgba(200,155,100,0.3)' }} />
            </div>
          )}
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
         快捷入口 Grid
         ═══════════════════════════════════════ */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
        {QUICK_ENTRIES.map((item, i) => {
          const Icon = item.icon;
          return (
            <button key={item.path} onClick={() => navigate(item.path)}
              className="quick-entry-card relative rounded-[28px] p-[18px] border-none cursor-pointer text-left flex flex-col gap-1.5
                transition-all duration-300 ease-out
                hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
              style={{
                background: item.bg,
                boxShadow: '0 14px 34px rgba(121,58,31,0.08)',
                animationDelay: `${0.2 + i * 0.08}s`,
              }}>
              <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-1 bg-white/60 backdrop-blur-sm text-brand">
                <Icon size={20} />
              </div>
              <span className="text-base font-bold text-ink">{item.label}</span>
              <span className="text-[13px] text-ink-muted">{item.note}</span>
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
             精选推荐 — Featured Content
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
                className="w-full border-none bg-none p-0 cursor-pointer text-left flex gap-3.5 group">
                {firstContent.cover_url ? (
                  <div className="w-[114px] h-[78px] rounded-2xl overflow-hidden shrink-0 transition-transform duration-300 group-hover:scale-105"
                    style={{ boxShadow: '0 6px 16px rgba(121,58,31,0.08)' }}>
                    <img src={buildImageUrl(firstContent.cover_url)} alt="" className="w-full h-full object-cover" loading="lazy" />
                  </div>
                ) : (
                  <div className="w-[114px] h-[78px] rounded-2xl shrink-0 flex items-center justify-center text-3xl
                    transition-transform duration-300 group-hover:scale-105"
                    style={{ background: 'linear-gradient(135deg, #f5e8d5, #e8d5b8)' }}>📜</div>
                )}
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
             文化内容 Grid
             ═══════════════════════════════════════ */}
          {recommend.contents && recommend.contents.length > 1 && (
            <section className="animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
              <SectionHeader title="文化内容" onViewAll={() => navigate('/content')} />
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {recommend.contents.slice(1, 5).map((item: ContentItem, i: number) => (
                  <button key={item.id} onClick={() => { trackClick('content', item.id); navigate(`/content/${item.id}`); }}
                    className="content-card rounded-[18px] overflow-hidden border-none cursor-pointer text-left p-0
                      transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-lg active:scale-[0.98]"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                      boxShadow: '0 14px 34px rgba(121,58,31,0.08)',
                    }}>
                    <div className="h-[100px] flex items-center justify-center overflow-hidden"
                      style={{ background: 'linear-gradient(135deg, #f5e8d5, #eadcc8)' }}>
                      {item.cover_url
                        ? <img src={buildImageUrl(item.cover_url)} alt="" className="w-full h-full object-cover transition-transform duration-500 hover:scale-110" loading="lazy" />
                        : <span className="text-4xl">📖</span>}
                    </div>
                    <div className="p-3.5">
                      <h4 className="text-sm font-bold text-ink mb-1 line-clamp-2 leading-snug">{item.title}</h4>
                      <p className="text-[11px] text-ink-muted line-clamp-2 leading-relaxed">{shortenReason(item.reason, '')}</p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* ═══════════════════════════════════════
             推荐活动
             ═══════════════════════════════════════ */}
          {recommend.events && recommend.events.length > 0 && (
            <section className="animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
              <SectionHeader title="推荐活动" onViewAll={() => navigate('/activity')} />
              <div className="space-y-3">
                {recommend.events.slice(0, 3).map((item: Activity, i: number) => (
                  <button key={item.id} onClick={() => { trackClick('event', item.id); navigate(`/activity/${item.id}`); }}
                    className="event-card w-full flex gap-3.5 items-center p-4 rounded-[16px] border-none cursor-pointer text-left
                      transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-md active:scale-[0.99]"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                      boxShadow: '0 14px 34px rgba(121,58,31,0.06)',
                    }}>
                    <div className="w-[72px] h-14 rounded-xl shrink-0 flex items-center justify-center text-2xl text-brand overflow-hidden
                      transition-transform duration-300 group-hover:scale-105"
                      style={{ background: 'linear-gradient(135deg, #f0e6d8, #e0d0b8)' }}>
                      {item.cover_url
                        ? <img src={buildImageUrl(item.cover_url)} alt="" className="w-full h-full object-cover rounded-xl" loading="lazy" />
                        : <Calendar size={22} className="text-cinnabar-500/60" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[15px] font-bold text-ink mb-1">{item.title}</h4>
                      <p className="text-[11px] text-ink-muted mb-0.5">
                        <MapPin size={10} className="inline mr-1" />{item.location} · {item.start_time?.slice(0, 10)}
                      </p>
                      <p className="text-[11px] text-ink-muted line-clamp-1">{shortenReason(item.reason, '')}</p>
                    </div>
                  </button>
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
                  <button key={item.id} onClick={() => { trackClick('topic', item.id); navigate(`/discussion/${item.id}`); }}
                    className="topic-card w-full p-4 rounded-[16px] border-none cursor-pointer text-left
                      transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-md active:scale-[0.99]"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                      boxShadow: '0 14px 34px rgba(121,58,31,0.06)',
                    }}>
                    <h4 className="text-[15px] font-bold text-ink mb-1.5">{item.title}</h4>
                    <p className="text-[13px] text-ink-secondary mb-2 line-clamp-2 leading-relaxed">
                      {item.content?.replace(/<[^>]*>/g, '').slice(0, 140)}
                    </p>
                    <div className="flex gap-3.5 text-[11px] text-ink-muted">
                      <span>👍 {item.like_count || 0}</span>
                      <span>💬 {item.comment_count || 0}</span>
                      {item.nickname && <span className="text-ink-muted">{item.nickname}</span>}
                    </div>
                  </button>
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
