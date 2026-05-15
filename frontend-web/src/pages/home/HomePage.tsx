import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, MapPin, Clock, MessageSquare, BookOpen, Calendar, MessageCircle, Sparkles, ChevronRight } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
import { RecommendData, ContentItem, Activity, DiscussionTopic } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';
import { useAuthStore } from '../../stores/auth-store';

function Card({ children, className = '', ...rest }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`rounded-[28px] px-6 py-5 mb-[18px] ${className}`}
      style={{
        background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
        boxShadow: '0 14px 34px rgba(121,58,31,0.10)',
        border: '1px solid rgba(219,191,155,0.18)',
      }}
      {...rest}>
      {children}
    </div>
  );
}

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
    <div className="p-6 pb-10 space-y-[18px]">
      {/* Hero */}
      <div className="rounded-[36px] p-4 pb-0 min-h-[200px] flex items-end relative overflow-hidden mb-5"
        style={{
          background: 'linear-gradient(135deg, #5B3A7A 0%, #8B4513 100%)',
          boxShadow: '0 22px 46px rgba(65,32,92,0.24)',
        }}>
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 60%, rgba(200,160,100,0.08) 0%, transparent 50%)' }} />
        <div className="flex-[0_0_56%] pb-5 relative z-10">
          <span className="inline-block px-3.5 py-1 rounded-full text-xs font-semibold tracking-[0.6px] text-[#ffd8a8] bg-white/[0.16] mb-3">
            数字导览中枢
          </span>
          <h2 className="text-[28px] font-extrabold text-[#fff8f1] leading-tight mb-2"
            style={{ textShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            和黑塔聊聊非遗
          </h2>
          <p className="text-sm text-white/90 mb-3.5 leading-relaxed">
            {crsMode === 'precision' ? '已为你准备好个性化推荐' : crsMode === 'mixed' ? '正在探索你的兴趣偏好' : '让我来了解你喜欢什么'}
          </p>
          <button onClick={() => navigate('/ai')}
            className="inline-flex items-center gap-1.5 px-7 py-2.5 rounded-full border-none cursor-pointer text-sm font-extrabold tracking-[1px] text-[#5d2410]"
            style={{
              background: 'linear-gradient(135deg, #ffd39a, #ffb765)',
              boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
            }}>
            <Sparkles size={14} /> 开始对话 <ArrowRight size={14} />
          </button>
        </div>
        <div className="flex-[0_0_44%] relative z-10 self-end translate-y-4">
          <DigitalHumanModel variant="hero" mood={mood} size={160} />
        </div>
      </div>

      {/* Guide text */}
      {recommend.guide_text && (
        <Card className="px-6 py-5">
          <p className="m-0 text-sm text-[#5a4430] leading-relaxed">{recommend.guide_text}</p>
        </Card>
      )}

      {/* Quick entry grid */}
      <div className="grid grid-cols-2 gap-3.5 mb-[18px]">
        {[
          { label: '非遗文化', note: '策展精选', icon: BookOpen, path: '/culture', bg: '#fff5eb' },
          { label: '非遗场馆', note: '线下体验', icon: MapPin, path: '/places', bg: '#f5f0e8' },
          { label: '浏览历史', note: '足迹回顾', icon: Clock, path: '/history', bg: '#f0f0f5' },
          { label: 'AI 对话', note: '黑塔导览', icon: MessageSquare, path: '/ai', bg: '#fff0ec' },
        ].map(item => { const Icon = item.icon; return (
          <button key={item.path} onClick={() => navigate(item.path)}
            className="rounded-[28px] p-[18px] border-none cursor-pointer text-left flex flex-col gap-1.5"
            style={{
              background: item.bg,
              boxShadow: '0 14px 34px rgba(121,58,31,0.08)',
            }}>
            <Icon size={20} style={{ color: '#9f2d22' }} />
            <span className="text-base font-bold text-[#3a2416]">{item.label}</span>
            <span className="text-[13px] text-[#83664d]">{item.note}</span>
          </button>
        ); })}
      </div>

      {isLoading ? (
        <div className="space-y-3.5">
          {[1,2,3].map(i => <div key={i} className="h-[120px] rounded-2xl skeleton" />)}
        </div>
      ) : (
        <>
          {/* Featured Content */}
          {firstContent && (
            <Card className="px-6 py-5" style={{
              background: 'linear-gradient(180deg, rgba(255,249,241,0.98), rgba(251,236,219,0.98))',
              border: '1px solid rgba(219,191,155,0.18)',
            }}>
              <div className="flex items-center justify-between mb-3.5">
                <div className="flex items-center gap-2">
                  <Sparkles size={14} style={{ color: '#c08a3e' }} />
                  <span className="text-lg font-extrabold text-[#342114]">精选推荐</span>
                </div>
                <span className="text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-[#f7e7dc] text-brand">文化</span>
              </div>
              <button onClick={() => { trackClick('content', firstContent.id); navigate(`/content/${firstContent.id}`); }}
                className="w-full border-none bg-none p-0 cursor-pointer text-left flex gap-3.5">
                {firstContent.cover_url ? (
                  <div className="w-[114px] h-[78px] rounded-2xl overflow-hidden shrink-0" style={{ boxShadow: '0 6px 16px rgba(121,58,31,0.08)' }}>
                    <img src={buildImageUrl(firstContent.cover_url)} alt="" className="w-full h-full object-cover" />
                  </div>
                ) : (
                  <div className="w-[114px] h-[78px] rounded-2xl shrink-0 flex items-center justify-center text-3xl"
                    style={{ background: 'linear-gradient(135deg, #f5e8d5, #e8d5b8)' }}>📜</div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="text-[17px] font-extrabold text-[#342114] mb-1.5 leading-snug">{firstContent.title}</h3>
                  <p className="text-xs text-[#83664d] leading-relaxed line-clamp-2">
                    {shortenReason(firstContent.reason, firstContent.summary || '')}
                  </p>
                </div>
              </button>
            </Card>
          )}

          {/* Content Grid */}
          {recommend.contents && recommend.contents.length > 1 && (
            <section>
              <div className="flex justify-between items-center mb-3 px-1">
                <span className="text-lg font-bold text-[#2f2419]">文化内容</span>
                <button onClick={() => navigate('/content')} className="text-[13px] text-brand font-semibold border-none bg-transparent cursor-pointer">
                  全部 <ChevronRight size={14} className="inline align-middle" />
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {recommend.contents.slice(1, 5).map((item: ContentItem) => (
                  <button key={item.id} onClick={() => { trackClick('content', item.id); navigate(`/content/${item.id}`); }}
                    className="rounded-[14px] overflow-hidden border-none cursor-pointer text-left p-0"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                      boxShadow: '0 14px 34px rgba(121,58,31,0.08)',
                    }}>
                    <div className="h-[90px] flex items-center justify-center"
                      style={{ background: 'linear-gradient(135deg, #f5e8d5, #eadcc8)' }}>
                      {item.cover_url
                        ? <img src={buildImageUrl(item.cover_url)} alt="" className="w-full h-full object-cover" />
                        : <span className="text-4xl">📖</span>}
                    </div>
                    <div className="p-3.5">
                      <h4 className="text-sm font-bold text-[#332418] mb-1 line-clamp-2 leading-snug">{item.title}</h4>
                      <p className="text-[11px] text-[#7c5f44] line-clamp-2 leading-relaxed">{shortenReason(item.reason, '')}</p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Events */}
          {recommend.events && recommend.events.length > 0 && (
            <section>
              <div className="flex justify-between items-center mb-3 px-1">
                <span className="text-lg font-bold text-[#2f2419]">推荐活动</span>
                <button onClick={() => navigate('/activity')} className="text-[13px] text-brand font-semibold border-none bg-transparent cursor-pointer">
                  全部 <ChevronRight size={14} className="inline align-middle" />
                </button>
              </div>
              <div className="space-y-3">
                {recommend.events.slice(0, 3).map((item: Activity) => (
                  <button key={item.id} onClick={() => { trackClick('event', item.id); navigate(`/activity/${item.id}`); }}
                    className="w-full flex gap-3.5 items-center p-4 rounded-[14px] border-none cursor-pointer text-left"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                      boxShadow: '0 14px 34px rgba(121,58,31,0.06)',
                    }}>
                    <div className="w-[72px] h-14 rounded-xl shrink-0 flex items-center justify-center text-2xl text-brand"
                      style={{ background: 'linear-gradient(135deg, #f0e6d8, #e0d0b8)' }}>
                      {item.cover_url
                        ? <img src={buildImageUrl(item.cover_url)} alt="" className="w-full h-full object-cover rounded-xl" />
                        : '📅'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[15px] font-bold text-[#342114] mb-1">{item.title}</h4>
                      <p className="text-[11px] text-[#8b6a4b] mb-0.5"><MapPin size={10} className="inline mr-1" />{item.location} · {item.start_time?.slice(0, 10)}</p>
                      <p className="text-[11px] text-[#a08868] line-clamp-1">{shortenReason(item.reason, '')}</p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Topics */}
          {recommend.topics && recommend.topics.length > 0 && (
            <section>
              <div className="flex justify-between items-center mb-3 px-1">
                <span className="text-lg font-bold text-[#2f2419]">社区讨论</span>
                <button onClick={() => navigate('/discussion')} className="text-[13px] text-brand font-semibold border-none bg-transparent cursor-pointer">
                  全部 <ChevronRight size={14} className="inline align-middle" />
                </button>
              </div>
              <div className="space-y-2.5">
                {recommend.topics.slice(0, 3).map((item: DiscussionTopic) => (
                  <button key={item.id} onClick={() => { trackClick('topic', item.id); navigate(`/discussion/${item.id}`); }}
                    className="w-full p-4 rounded-[14px] border-none cursor-pointer text-left"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                      boxShadow: '0 14px 34px rgba(121,58,31,0.06)',
                    }}>
                    <h4 className="text-[15px] font-bold text-[#322418] mb-1.5">{item.title}</h4>
                    <p className="text-[13px] text-[#674d36] mb-2 line-clamp-2 leading-relaxed">{item.content?.replace(/<[^>]*>/g, '').slice(0, 140)}</p>
                    <div className="flex gap-3.5 text-[11px] text-[#8b6a4b]">
                      <span>👍 {item.like_count || 0}</span>
                      <span>💬 {item.comment_count || 0}</span>
                      {item.nickname && <span className="text-[#a08868]">{item.nickname}</span>}
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
