import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Sparkles, MapPin, Clock, MessageSquare, BookOpen, Calendar, MessageCircle, ChevronRight } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
import { RecommendData, ContentItem, Activity, DiscussionTopic } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';
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
    <div style={{ padding: '24rpx', paddingBottom: 40 }}>
      {/* ── Hero (小程序 ai-hero 风格) ── */}
      <div className="rise-in" style={{
        background: 'linear-gradient(135deg, #5B3A7A 0%, #8B4513 100%)',
        borderRadius: '36rpx', padding: '16rpx 24rpx 0',
        minHeight: 200, display: 'flex', alignItems: 'flex-end',
        boxShadow: '0 22rpx 46rpx rgba(65,32,92,0.24)',
        position: 'relative', overflow: 'hidden', marginBottom: 20,
      }}>
        {/* Inner glows */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'radial-gradient(ellipse at 30% 20%, rgba(255,255,255,0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 60%, rgba(200,160,100,0.08) 0%, transparent 50%)' }} />
        <div style={{ flex: '0 0 56%', paddingBottom: 20, position: 'relative', zIndex: 1 }}>
          <span style={{
            display: 'inline-block', padding: '4rpx 14rpx', borderRadius: 999,
            background: 'rgba(255,247,236,0.16)', color: '#ffd8a8',
            fontSize: 12, fontWeight: 600, marginBottom: 12, letterSpacing: '0.6rpx',
          }}>
            数字导览中枢
          </span>
          <h2 style={{
            fontSize: 28, fontWeight: 800, color: '#fff8f1',
            lineHeight: 1.22, margin: '0 0 8rpx',
            textShadow: '0 2rpx 8rpx rgba(0,0,0,0.1)',
          }}>
            和黑塔聊聊非遗
          </h2>
          <p style={{ fontSize: 14, color: 'rgba(255,244,232,0.92)', lineHeight: 1.5, margin: '0 0 14rpx' }}>
            {crsMode === 'precision' ? '已为你准备好个性化推荐' : crsMode === 'mixed' ? '正在探索你的兴趣偏好' : '让我来了解你喜欢什么'}
          </p>
          <button onClick={() => navigate('/ai')}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '12rpx 28rpx', borderRadius: 999, border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg, #ffd39a, #ffb765)',
              color: '#5d2410', fontWeight: 800, fontSize: 14, letterSpacing: '1rpx',
              boxShadow: '0 8rpx 16rpx rgba(0,0,0,0.1)',
            }}>
            <Sparkles size={14} /> 开始对话
          </button>
        </div>
        <div style={{ flex: '0 0 44%', position: 'relative', zIndex: 1, alignSelf: 'flex-end', transform: 'translateY(16rpx)' }}>
          <DigitalHumanModel variant="hero" mood={mood} size={160} />
        </div>
      </div>

      {/* ── Guide text ── */}
      {recommend.guide_text && (
        <div className="card rise-in rise-in-2" style={{ padding: '20rpx 24rpx' }}>
          <p style={{ margin: 0, fontSize: 14, color: '#5a4430', lineHeight: 1.8 }}>{recommend.guide_text}</p>
        </div>
      )}

      {/* ── Quick entry grid (小程序 quick-grid 风格) ── */}
      <div className="rise-in rise-in-2" style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14,
        marginBottom: 18,
      }}>
        {[
          { label: '非遗文化', note: '策展精选', icon: BookOpen, path: '/culture', bg: '#fff5eb' },
          { label: '非遗场馆', note: '线下体验', icon: MapPin, path: '/places', bg: '#f5f0e8' },
          { label: '浏览历史', note: '足迹回顾', icon: Clock, path: '/history', bg: '#f0f0f5' },
          { label: 'AI 对话', note: '黑塔导览', icon: MessageSquare, path: '/ai', bg: '#fff0ec' },
        ].map(item => {
          const Icon = item.icon;
          return (
            <button key={item.path} onClick={() => navigate(item.path)}
              className="card"
              style={{ padding: '18rpx', margin: 0, background: item.bg, border: 'none', cursor: 'pointer', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <Icon size={20} style={{ color: '#9f2d22' }} />
              <span style={{ fontSize: 16, fontWeight: 700, color: '#3a2416' }}>{item.label}</span>
              <span style={{ fontSize: 13, color: '#83664d' }}>{item.note}</span>
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 120 }} />)}
        </div>
      ) : (
        <>
          {/* ── Featured Recommendation ── */}
          {firstContent && (
            <section className="rise-in rise-in-3" style={{ marginBottom: 18 }}>
              <div style={{
                background: 'linear-gradient(180deg, rgba(255,249,241,0.98), rgba(251,236,219,0.98))',
                borderRadius: '28rpx', padding: '20rpx 24rpx',
                boxShadow: '0 14rpx 34rpx rgba(121,58,31,0.08)',
                border: '1rpx solid rgba(219,191,155,0.18)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Sparkles size={14} style={{ color: '#c08a3e' }} />
                    <span style={{ fontSize: 18, fontWeight: 800, color: '#342114' }}>精选推荐</span>
                  </div>
                  <span style={{
                    fontSize: 11, padding: '2rpx 10rpx', borderRadius: 999,
                    background: '#f7e7dc', color: '#9f2d22', fontWeight: 600,
                  }}>文化</span>
                </div>
                <button
                  onClick={() => { trackClick('content', firstContent.id); navigate(`/content/${firstContent.id}`); }}
                  style={{ width: '100%', border: 'none', background: 'none', padding: 0, cursor: 'pointer', textAlign: 'left', display: 'flex', gap: 14 }}>
                  {firstContent.cover_url ? (
                    <div style={{ width: 114, height: 78, borderRadius: 14, overflow: 'hidden', flexShrink: 0, boxShadow: '0 6rpx 16rpx rgba(121,58,31,0.08)' }}>
                      <img src={buildImageUrl(firstContent.cover_url)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                  ) : (
                    <div style={{
                      width: 114, height: 78, borderRadius: 14, flexShrink: 0,
                      background: 'linear-gradient(135deg, #f5e8d5, #e8d5b8)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 32, color: '#c08a3e',
                    }}>
                      📜
                    </div>
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ fontSize: 17, fontWeight: 800, color: '#342114', margin: '0 0 6rpx', lineHeight: 1.3 }}>{firstContent.title}</h3>
                    <p style={{ fontSize: 12, color: '#83664d', margin: 0, lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {shortenReason(firstContent.reason, firstContent.summary || '')}
                    </p>
                  </div>
                </button>
              </div>
            </section>
          )}

          {/* ── Content Section ── */}
          {recommend.contents && recommend.contents.length > 1 && (
            <section style={{ marginBottom: 18 }}>
              <div className="split-line" style={{ marginBottom: 14 }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: '#2f2419' }}>文化内容</span>
                <button onClick={() => navigate('/content')} style={{ fontSize: 13, color: '#9f2d22', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
                  全部 <ChevronRight size={14} style={{ verticalAlign: 'middle' }} />
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {recommend.contents.slice(1, 5).map((item: ContentItem, idx: number) => (
                  <button key={item.id} onClick={() => { trackClick('content', item.id); navigate(`/content/${item.id}`); }}
                    className="card" style={{
                      margin: 0, padding: 0, overflow: 'hidden', textAlign: 'left', border: 'none', cursor: 'pointer',
                      animationDelay: `${0.3 + idx * 0.08}s`,
                    }}>
                    <div style={{
                      height: 90, background: 'linear-gradient(135deg, #f5e8d5, #eadcc8)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {item.cover_url
                        ? <img src={buildImageUrl(item.cover_url)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        : <span style={{ fontSize: 36, color: '#c08a3e' }}>📖</span>}
                    </div>
                    <div style={{ padding: '14rpx 16rpx' }}>
                      <h4 style={{ fontSize: 14, fontWeight: 700, color: '#332418', margin: 0, lineHeight: 1.3 }}>{item.title}</h4>
                      <p style={{ fontSize: 11, color: '#7c5f44', margin: '4rpx 0 0', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {shortenReason(item.reason, '')}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* ── Events ── */}
          {recommend.events && recommend.events.length > 0 && (
            <section style={{ marginBottom: 18 }}>
              <div className="split-line" style={{ marginBottom: 14 }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: '#2f2419' }}>推荐活动</span>
                <button onClick={() => navigate('/activity')} style={{ fontSize: 13, color: '#9f2d22', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
                  全部 <ChevronRight size={14} style={{ verticalAlign: 'middle' }} />
                </button>
              </div>
              {recommend.events.slice(0, 3).map((item: Activity, idx: number) => (
                <button key={item.id} onClick={() => { trackClick('event', item.id); navigate(`/activity/${item.id}`); }}
                  className="card rise-in" style={{
                    display: 'flex', gap: 14, alignItems: 'center', width: '100%',
                    border: 'none', cursor: 'pointer', textAlign: 'left',
                    animationDelay: `${0.3 + idx * 0.08}s`, margin: '0 0 12rpx',
                  }}>
                  <div style={{
                    width: 72, height: 56, borderRadius: 12, flexShrink: 0,
                    background: 'linear-gradient(135deg, #f0e6d8, #e0d0b8)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 28, color: '#9f2d22',
                  }}>
                    {item.cover_url
                      ? <img src={buildImageUrl(item.cover_url)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      : '📅'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h4 style={{ fontSize: 15, fontWeight: 700, color: '#342114', margin: '0 0 4rpx' }}>{item.title}</h4>
                    <p style={{ fontSize: 11, color: '#8b6a4b', margin: '0 0 2rpx' }}>
                      <MapPin size={10} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                      {item.location} · {item.start_time?.slice(0, 10)}
                    </p>
                    <p style={{ fontSize: 11, color: '#a08868', margin: 0, display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {shortenReason(item.reason, '')}
                    </p>
                  </div>
                </button>
              ))}
            </section>
          )}

          {/* ── Topics ── */}
          {recommend.topics && recommend.topics.length > 0 && (
            <section style={{ marginBottom: 18 }}>
              <div className="split-line" style={{ marginBottom: 14 }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: '#2f2419' }}>社区讨论</span>
                <button onClick={() => navigate('/discussion')} style={{ fontSize: 13, color: '#9f2d22', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
                  全部 <ChevronRight size={14} style={{ verticalAlign: 'middle' }} />
                </button>
              </div>
              {recommend.topics.slice(0, 3).map((item: DiscussionTopic, idx: number) => (
                <button key={item.id} onClick={() => { trackClick('topic', item.id); navigate(`/discussion/${item.id}`); }}
                  className="card" style={{
                    width: '100%', border: 'none', cursor: 'pointer', textAlign: 'left',
                    margin: '0 0 10rpx',
                  }}>
                  <h4 style={{ fontSize: 15, fontWeight: 700, color: '#322418', margin: '0 0 6rpx' }}>{item.title}</h4>
                  <p style={{ fontSize: 13, color: '#674d36', margin: '0 0 8rpx', lineHeight: 1.6, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.content?.replace(/<[^>]*>/g, '').slice(0, 140)}
                  </p>
                  <div style={{ display: 'flex', gap: 14, fontSize: 11, color: '#8b6a4b' }}>
                    <span>👍 {item.like_count || 0}</span>
                    <span>💬 {item.comment_count || 0}</span>
                    {item.nickname && <span style={{ color: '#a08868' }}>{item.nickname}</span>}
                  </div>
                </button>
              ))}
            </section>
          )}
        </>
      )}
    </div>
  );
}
