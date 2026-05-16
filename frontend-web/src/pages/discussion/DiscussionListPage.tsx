import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Heart, MessageCircle, Bookmark, Plus, MessageSquareText } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { DiscussionTopic } from '../../types';
import CoverImage from '../../components/ui/CoverImage';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function DiscussionListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ['discussions'],
    queryFn: () => apiRequest<{ code: number; data: DiscussionTopic[] }>('/discussion/'),
  });
  const topics = (data?.data || []) as DiscussionTopic[];

  return (
    <div className="px-5 pb-28 pt-1">
      {/* ── Hero Banner ── */}
      <div
        className="rise-in relative overflow-hidden mb-5 mt-3 p-5 rounded-[36px]"
        style={{
          background: 'linear-gradient(135deg, #6B3A2A 0%, #9B4F3C 50%, #b85d47 100%)',
          boxShadow: '0 22px 46px rgba(60, 20, 10, 0.22)',
        }}
      >
        {/* Decorative blobs */}
        <div className="absolute -top-10 -right-8 w-36 h-36 rounded-full bg-white/6" />
        <div className="absolute -bottom-6 left-10 w-20 h-20 rounded-full bg-white/4" />

        <span className="relative inline-block px-3.5 py-1 rounded-full text-xs font-semibold tracking-wide bg-white/12 text-[#ffe1bc] mb-2.5">
          非遗社区交流
        </span>
        <h1 className="relative font-serif text-[26px] font-extrabold text-[#fff8f1] leading-tight mb-1">
          社区讨论
        </h1>
        <p className="relative text-sm text-white/85 font-sans">
          分享和探讨非遗文化的方方面面
        </p>
      </div>

      {/* ── Loading State ── */}
      {isLoading ? (
        <div className="flex flex-col gap-3.5">
          {[1, 2, 3].map((i) => (
            <SkeletonLoader key={i} variant="card" className="!h-28" />
          ))}
        </div>
      ) : topics.length === 0 ? (
        /* ── Empty State ── */
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-full bg-parchment-dark flex items-center justify-center mb-4">
            <MessageSquareText size={28} className="text-ink-muted opacity-40" />
          </div>
          <p className="text-ink-muted text-sm font-sans">暂无讨论话题</p>
          <p className="text-ink-muted text-xs mt-1 opacity-55 font-sans">
            成为第一个发起讨论的人吧
          </p>
        </div>
      ) : (
        /* ── Topic List ── */
        <div className="rise-in-stagger flex flex-col gap-3">
          {topics.map((item, idx) => (
            <button
              key={item.id}
              type="button"
              onClick={() => navigate(`/discussion/${item.id}`)}
              className="card-interactive w-full text-left"
              style={{ animationDelay: `${0.08 + idx * 0.06}s` }}
            >
              <GlassCard hover className="p-4">
                <div className="flex items-start gap-3">
                  {/* Avatar / Cover Thumbnail */}
                  {item.cover_url ? (
                    <div className="w-14 h-14 shrink-0 rounded-2xl overflow-hidden bg-parchment-dark">
                      <CoverImage
                        coverUrl={item.cover_url}
                        alt={item.title}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </div>
                  ) : (
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold text-[#fff7ef] select-none"
                      style={{
                        background: `linear-gradient(135deg, #9f2d22, #c08a3e)`,
                      }}
                    >
                      {(item.nickname || '匿')[0]}
                    </div>
                  )}

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <h3 className="font-serif text-[15px] font-bold text-ink mb-1.5 leading-snug line-clamp-2">
                      {item.title}
                    </h3>
                    <p className="text-[13px] text-ink-secondary mb-2.5 leading-relaxed line-clamp-2 font-sans">
                      {item.content?.replace(/<[^>]*>/g, '').slice(0, 200)}
                    </p>

                    {/* Stats row */}
                    <div className="flex items-center gap-3.5 text-[11px] text-ink-muted font-sans">
                      {item.nickname && (
                        <span className="text-ink-secondary font-medium truncate max-w-[100px]">
                          {item.nickname}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Heart size={11} /> {item.like_count || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageCircle size={11} /> {item.comment_count || 0}
                      </span>
                      <span className="flex items-center gap-1">
                        <Bookmark size={11} /> {item.favorite_count || 0}
                      </span>
                      <span className="ml-auto opacity-55 whitespace-nowrap">
                        {item.created_at?.slice(0, 10)}
                      </span>
                    </div>

                    {/* Tags */}
                    {item.tags && item.tags.length > 0 && (
                      <div className="flex gap-1.5 mt-2.5 flex-wrap">
                        {item.tags.slice(0, 3).map((t, i) => (
                          <span key={i} className="chip !text-[11px] !min-h-0 !py-0.5 !px-2.5">
                            #{t}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>
            </button>
          ))}
        </div>
      )}

      {/* ── Composer FAB ── */}
      <button
        type="button"
        onClick={() => navigate('/discussion')}
        className="fixed right-5 bottom-28 z-50 w-14 h-14 rounded-full flex flex-col items-center justify-center border-none cursor-pointer guofeng-press"
        style={{
          background: 'linear-gradient(135deg, #7a2f25, #b74f3b)',
          boxShadow: '0 14px 30px rgba(126, 45, 35, 0.28)',
        }}
        aria-label="发帖"
      >
        <Plus size={24} className="text-white" />
        <span className="text-[9px] font-bold text-white -mt-0.5 tracking-wide">发帖</span>
      </button>
    </div>
  );
}
