import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, MapPin, Clock, MessageSquare, BookOpen, Sparkles, Calendar, MessageCircle } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
import { RecommendData, ContentItem, Activity, DiscussionTopic } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';
import { useAuthStore } from '../../stores/auth-store';

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
    try {
      await apiRequest('/recommend/track', {
        method: 'POST',
        data: { user_id: session?.userId, action: 'click', target_type: type, target_id: id, source_scene: scene },
      });
    } catch {}
  };

  return (
    <div className="px-4 py-5 space-y-5">
      {/* Hero — Digital Human + CRS */}
      <div className="relative bg-gradient-to-br from-parchment via-white to-gold-50 rounded-3xl p-5 border border-ink-border/40 shadow-sm overflow-hidden">
        <div className="absolute top-0 right-0 w-48 h-48 bg-gold-100/20 rounded-full blur-2xl -translate-y-1/2 translate-x-1/4" />
        <div className="flex items-center gap-3 relative z-10">
          <div className="shrink-0">
            <DigitalHumanModel variant="hero" mood={mood} size={180} />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-serif font-bold text-ink">和黑塔聊聊非遗</h2>
            <p className="text-sm text-ink-secondary mt-1 leading-relaxed">
              {crsMode === 'precision'
                ? '已为你准备好个性化推荐'
                : crsMode === 'mixed'
                ? '正在探索你的兴趣偏好'
                : '让我来了解你喜欢什么'}
            </p>

            {/* Confidence ring */}
            {confidence > 0 && (
              <div className="flex items-center gap-2.5 mt-3">
                <div className="relative w-10 h-10">
                  <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                    <circle cx="18" cy="18" r="15" fill="none" stroke="currentColor" strokeWidth="3" className="text-ink-border/40" />
                    <circle
                      cx="18" cy="18" r="15" fill="none" stroke="currentColor" strokeWidth="3"
                      strokeDasharray={`${confidence * 0.942} 94.2`}
                      strokeLinecap="round"
                      className={`${mood === 'confident' ? 'text-cinnabar-600' : mood === 'thinking' ? 'text-jade-500' : 'text-gold-500'}`}
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-ink">{confidence}%</span>
                </div>
                <SealBadge variant={mood === 'confident' ? 'cinnabar' : mood === 'thinking' ? 'jade' : 'gold'}>
                  {mood === 'confident' ? '已懂你' : mood === 'thinking' ? '思考中' : '了解中'}
                </SealBadge>
              </div>
            )}

            <button
              onClick={() => navigate('/ai')}
              className="mt-3.5 ink-btn ink-btn-primary !text-sm"
            >
              <Sparkles size={15} /> 开始对话 <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-4 gap-2.5">
        {[
          { label: '非遗文化', icon: BookOpen, path: '/culture', color: 'bg-amber-50 text-amber-600' },
          { label: '非遗场馆', icon: MapPin, path: '/places', color: 'bg-jade-50 text-jade-500' },
          { label: '浏览历史', icon: Clock, path: '/history', color: 'bg-blue-50 text-blue-500' },
          { label: 'AI 对话', icon: MessageSquare, path: '/ai', color: 'bg-cinnabar-50 text-cinnabar-600' },
        ].map(item => {
          const Icon = item.icon;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className="flex flex-col items-center gap-1.5 p-2.5 glass-card hover:border-gold-200 transition-all"
            >
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${item.color}`}>
                <Icon size={18} />
              </div>
              <span className="text-[11px] text-ink-secondary">{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* Guide text */}
      {recommend.guide_text && (
        <GlassCard className="p-3.5">
          <p className="text-sm text-ink-secondary leading-relaxed">{recommend.guide_text}</p>
        </GlassCard>
      )}

      {isLoading ? (
        <div className="space-y-3">
          <SkeletonLoader variant="card" />
          <SkeletonLoader variant="text" />
          <SkeletonLoader variant="text" />
          <SkeletonLoader variant="card" />
        </div>
      ) : (
        <>
          {/* Featured Content */}
          {firstContent && (
            <section>
              <div className="flex items-center gap-2 mb-2.5">
                <Sparkles size={14} className="text-cinnabar-600" />
                <h3 className="text-sm font-serif font-bold text-ink">为你推荐</h3>
              </div>
              <button
                onClick={() => { trackClick('content', firstContent.id); navigate(`/content/${firstContent.id}`); }}
                className="w-full glass-card overflow-hidden hover:shadow-lg transition-all text-left card-lift"
              >
                {firstContent.cover_url && (
                  <div className="h-40 bg-parchment-dark relative">
                    <img src={buildImageUrl(firstContent.cover_url)} alt={firstContent.title} className="w-full h-full object-cover" loading="lazy" />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                    <div className="absolute top-3 right-3">
                      <SealBadge variant="gold">精选</SealBadge>
                    </div>
                  </div>
                )}
                <div className="p-4">
                  <h4 className="font-serif font-bold text-ink text-base">{firstContent.title}</h4>
                  <p className="text-xs text-ink-secondary mt-1.5 line-clamp-2 leading-relaxed">
                    {shortenReason(firstContent.reason, firstContent.summary || '')}
                  </p>
                </div>
              </button>
            </section>
          )}

          {/* Content list */}
          {recommend.contents && recommend.contents.length > 1 && (
            <section>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="text-sm font-serif font-bold text-ink flex items-center gap-1.5">
                  <BookOpen size={14} className="text-ink-muted" /> 文化内容
                </h3>
                <button onClick={() => navigate('/content')} className="text-xs text-cinnabar-600 hover:text-cinnabar-700 font-medium transition-colors">
                  全部 →
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                {recommend.contents.slice(1, 5).map((item: ContentItem) => (
                  <button
                    key={item.id}
                    onClick={() => { trackClick('content', item.id); navigate(`/content/${item.id}`); }}
                    className="glass-card p-0 overflow-hidden hover:border-gold-200 transition-all text-left card-lift"
                  >
                    {item.cover_url && (
                      <div className="h-24 bg-parchment-dark">
                        <img src={buildImageUrl(item.cover_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" />
                      </div>
                    )}
                    <div className="p-2.5">
                      <h4 className="text-xs font-medium text-ink line-clamp-2 leading-snug">{item.title}</h4>
                      <p className="text-[11px] text-ink-muted mt-1 line-clamp-1">{shortenReason(item.reason, '')}</p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Events */}
          {recommend.events && recommend.events.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="text-sm font-serif font-bold text-ink flex items-center gap-1.5">
                  <Calendar size={14} className="text-ink-muted" /> 推荐活动
                </h3>
                <button onClick={() => navigate('/activity')} className="text-xs text-cinnabar-600 hover:text-cinnabar-700 font-medium transition-colors">
                  全部 →
                </button>
              </div>
              <div className="space-y-2">
                {recommend.events.slice(0, 3).map((item: Activity) => (
                  <button
                    key={item.id}
                    onClick={() => { trackClick('event', item.id); navigate(`/activity/${item.id}`); }}
                    className="w-full glass-card p-3 flex gap-3 hover:border-gold-200 transition-all text-left card-lift"
                  >
                    {item.cover_url ? (
                      <div className="w-14 h-14 shrink-0 rounded-lg overflow-hidden bg-parchment-dark">
                        <img src={buildImageUrl(item.cover_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" />
                      </div>
                    ) : (
                      <div className="w-14 h-14 shrink-0 rounded-lg bg-jade-50 flex items-center justify-center">
                        <Calendar size={20} className="text-jade-400" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-medium text-ink">{item.title}</h4>
                      <p className="text-xs text-ink-muted mt-0.5">{item.location} · {item.start_time?.slice(0, 10)}</p>
                      <p className="text-xs text-ink-muted/70 line-clamp-1 mt-0.5">{shortenReason(item.reason, '')}</p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Topics */}
          {recommend.topics && recommend.topics.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="text-sm font-serif font-bold text-ink flex items-center gap-1.5">
                  <MessageCircle size={14} className="text-ink-muted" /> 社区讨论
                </h3>
                <button onClick={() => navigate('/discussion')} className="text-xs text-cinnabar-600 hover:text-cinnabar-700 font-medium transition-colors">
                  全部 →
                </button>
              </div>
              <div className="space-y-2">
                {recommend.topics.slice(0, 3).map((item: DiscussionTopic) => (
                  <button
                    key={item.id}
                    onClick={() => { trackClick('topic', item.id); navigate(`/discussion/${item.id}`); }}
                    className="w-full glass-card p-3 hover:border-gold-200 transition-all text-left card-lift"
                  >
                    <h4 className="text-sm font-medium text-ink">{item.title}</h4>
                    <p className="text-xs text-ink-muted mt-1 line-clamp-1">{shortenReason(item.reason, item.content || '')}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-ink-muted">
                      <span className="flex items-center gap-1">👍 {item.like_count || 0}</span>
                      <span className="flex items-center gap-1">💬 {item.comment_count || 0}</span>
                      {item.nickname && <span className="ml-auto">{item.nickname}</span>}
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Profile Summary */}
          {recommend.profile_summary?.summary_text && (
            <GlassCard className="p-3.5 border-gold-200/50">
              <p className="text-xs text-ink-secondary leading-relaxed">
                <span className="font-medium text-ink">你的画像：</span>
                {recommend.profile_summary.summary_text}
              </p>
            </GlassCard>
          )}
        </>
      )}

      <div className="h-4" />
    </div>
  );
}
