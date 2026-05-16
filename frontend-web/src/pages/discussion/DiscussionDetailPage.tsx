import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Heart, MessageCircle, Bookmark, Send } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { DiscussionTopic } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';
import { SealBadge } from '../../components/ui/SealBadge';
import CoverImage from '../../components/ui/CoverImage';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function DiscussionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const [comment, setComment] = useState('');
  const [comments, setComments] = useState<{ id: string; nickname: string; content: string; created_at: string }[]>([]);
  const [liked, setLiked] = useState(false);
  const [likeCount, setLikeCount] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['discussion', id],
    queryFn: () => apiRequest<{ code: number; data: DiscussionTopic }>(`/discussion/${id}`),
    enabled: !!id,
  });

  const item = data?.data;
  useEffect(() => {
    if (item?.like_count && likeCount === 0) setLikeCount(item.like_count);
  }, [item, likeCount]);

  const handleLike = async () => {
    try {
      await apiRequest('/discussion/like', { method: 'POST', data: { topic_id: Number(id), user_id: session?.userId } });
      setLiked(!liked);
      setLikeCount(liked ? likeCount - 1 : likeCount + 1);
    } catch {}
  };

  const handleFavorite = async () => {
    try {
      await apiRequest('/discussion/favorite', { method: 'POST', data: { topic_id: Number(id), user_id: session?.userId } });
    } catch {}
  };

  const handleComment = async () => {
    if (!comment.trim()) return;
    try {
      const res = await apiRequest<{ code: number; data: { id: number } }>('/discussion/comment', {
        method: 'POST',
        data: { topic_id: Number(id), user_id: session?.userId, content: comment },
      });
      if (res.code === 0) {
        setComments([...comments, { id: 'c' + Date.now(), nickname: session?.nickname || '我', content: comment, created_at: new Date().toISOString() }]);
        setComment('');
      }
    } catch {}
  };

  /* ── Loading State ── */
  if (isLoading) {
    return (
      <div className="px-5 py-5 space-y-4">
        <SkeletonLoader variant="text" className="!w-20 !h-4" />
        <SkeletonLoader variant="image" className="!h-48 !rounded-[28px]" />
        <SkeletonLoader variant="text" className="!w-3/4 !h-6" />
        <SkeletonLoader variant="text" className="!w-1/2 !h-4" />
        <SkeletonLoader variant="text" className="!h-20" />
        <SkeletonLoader variant="card" className="!h-28" />
        <SkeletonLoader variant="card" className="!h-20" />
      </div>
    );
  }

  /* ── Error / Not Found State ── */
  if (!item) {
    return (
      <div className="px-5 py-20 flex flex-col items-center justify-center text-center">
        <GlassCard elevated className="p-8 w-full max-w-sm flex flex-col items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-cinnabar-50 flex items-center justify-center">
            <MessageCircle size={24} className="text-cinnabar-500/50" />
          </div>
          <p className="text-ink font-serif font-bold text-lg">帖子不存在</p>
          <p className="text-ink-muted text-sm font-sans">该讨论可能已被删除或链接无效</p>
          <InkButton variant="outline" size="sm" onClick={() => navigate(-1)}>
            返回上一页
          </InkButton>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="pb-28 px-5">
      {/* ── Back Button ── */}
      <div className="mt-3 mb-3">
        <InkButton variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={15} /> 返回
        </InkButton>
      </div>

      {/* ── Cover Image ── */}
      {item.cover_url && (
        <div className="mb-4">
          <CoverImage
            coverUrl={item.cover_url}
            alt={item.title}
            className="w-full h-48 object-cover rounded-[28px]"
          />
        </div>
      )}

      {/* ── Title & Meta ── */}
      <h1 className="font-serif text-xl font-bold text-ink leading-snug mb-2.5">
        {item.title}
      </h1>

      <div className="flex items-center gap-2.5 mb-4 flex-wrap">
        {item.nickname && (
          <div className="flex items-center gap-1.5">
            <div
              className="w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-bold text-[#fff7ef] flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #9f2d22, #c08a3e)' }}
            >
              {item.nickname[0]}
            </div>
            <span className="text-xs text-ink-secondary font-medium">{item.nickname}</span>
          </div>
        )}
        <span className="text-xs text-ink-muted">{item.created_at?.slice(0, 10)}</span>
        {item.category && (
          <SealBadge variant="cinnabar">{item.category}</SealBadge>
        )}
      </div>

      {/* ── Content ── */}
      <GlassCard className="p-5 mb-4">
        <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap font-sans">
          {item.content?.replace(/<[^>]*>/g, '')}
        </p>

        {/* Tags */}
        {item.tags && item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-4 pt-3.5 border-t border-parchment-dark/40">
            {item.tags.map((t, i) => (
              <span key={i} className="chip !text-[11px] !min-h-0 !py-1 !px-3">
                #{t}
              </span>
            ))}
          </div>
        )}
      </GlassCard>

      {/* ── Action Bar ── */}
      <div className="flex items-center gap-1 mb-6 px-1">
        <InkButton
          variant="ghost"
          size="sm"
          onClick={handleLike}
          className={liked ? '!text-cinnabar-600' : ''}
        >
          <Heart size={17} className={liked ? 'fill-cinnabar-600 text-cinnabar-600' : ''} />
          {likeCount > 0 && likeCount}
        </InkButton>
        <InkButton variant="ghost" size="sm" onClick={handleFavorite}>
          <Bookmark size={17} /> 收藏
        </InkButton>
        <span className="flex items-center gap-1.5 text-sm text-ink-muted px-2.5 py-1.5 font-sans">
          <MessageCircle size={17} />
          {item.comment_count || 0}
        </span>
      </div>

      {/* ── Split line ── */}
      <div className="split-line mb-5" />

      {/* ── Comments Section ── */}
      <h3 className="font-serif text-sm font-bold text-ink mb-3.5">
        评论 ({comments.length + (item.comment_count || 0)})
      </h3>

      {comments.length === 0 ? (
        <p className="text-xs text-ink-muted text-center py-8 font-sans">
          暂无评论，来写第一条吧
        </p>
      ) : (
        <div className="space-y-2.5 mb-4">
          {comments.map((c, i) => (
            <GlassCard key={c.id || i} className="p-3.5">
              <div className="flex items-center gap-2 mb-1.5">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-[#fff7ef] flex-shrink-0"
                  style={{ background: 'linear-gradient(135deg, #9f2d22, #c08a3e)' }}
                >
                  {(c.nickname || '匿')[0]}
                </div>
                <span className="text-xs text-ink-secondary font-medium">{c.nickname}</span>
                <span className="text-[10px] text-ink-muted opacity-55 ml-auto">{c.created_at?.slice(0, 10)}</span>
              </div>
              <p className="text-sm text-ink leading-relaxed font-sans">{c.content}</p>
            </GlassCard>
          ))}
        </div>
      )}

      {/* ── Comment Input (sticky bottom) ── */}
      <div className="fixed bottom-0 left-0 right-0 z-40 px-4 py-3"
        style={{ background: 'linear-gradient(180deg, transparent 0%, #fdf8f0 20%, #f7efe0 100%)' }}>
        <div className="max-w-[800px] mx-auto flex gap-2 items-center">
          <div className="flex-1 glass-card rounded-2xl px-4 py-2.5 flex items-center backdrop-blur-sm">
            <input
              type="text"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleComment()}
              placeholder="写评论..."
              className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-muted/60 font-sans outline-none border-none"
            />
          </div>
          <InkButton
            variant="primary"
            size="sm"
            onClick={handleComment}
            disabled={!comment.trim()}
            className="!p-2.5 !rounded-2xl disabled:!opacity-40"
          >
            <Send size={15} />
          </InkButton>
        </div>
      </div>
    </div>
  );
}
