import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Heart, MessageCircle, Bookmark, Send } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { DiscussionTopic } from '../../types';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
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

  if (isLoading) {
    return <div className="px-4 py-4"><SkeletonLoader variant="image" className="!h-40" /></div>;
  }

  if (!item) {
    return (
      <div className="px-4 py-20 text-center">
        <p className="text-ink-muted">帖子不存在</p>
        <button onClick={() => navigate(-1)} className="text-cinnabar-600 text-sm mt-2 hover:underline">返回</button>
      </div>
    );
  }

  return (
    <div className="pb-8 px-4">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary mt-4 mb-3 hover:text-ink transition-colors">
        <ArrowLeft size={16} /> 返回
      </button>

      <h1 className="text-lg font-serif font-bold text-ink">{item.title}</h1>

      <div className="flex items-center gap-3 mt-2 text-xs text-ink-muted">
        {item.nickname && <span className="text-ink-secondary">{item.nickname}</span>}
        <span>{item.created_at?.slice(0, 10)}</span>
        {item.category && <span className="bg-parchment-dark text-ink-muted px-1.5 py-0.5 rounded-full">{item.category}</span>}
      </div>

      <div className="mt-4 text-sm text-ink leading-relaxed whitespace-pre-wrap font-sans">
        {item.content?.replace(/<[^>]*>/g, '')}
      </div>

      {item.tags && item.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3">
          {item.tags.map((t, i) => (
            <span key={i} className="text-xs bg-parchment-dark text-ink-muted px-2 py-0.5 rounded-full">#{t}</span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4 mt-5 py-3 border-y border-ink-border/30">
        <button onClick={handleLike} className={`flex items-center gap-1 text-sm transition-colors ${liked ? 'text-cinnabar-600' : 'text-ink-muted hover:text-cinnabar-600'}`}>
          <Heart size={18} className={liked ? 'fill-cinnabar-600' : ''} /> {likeCount}
        </button>
        <button onClick={handleFavorite} className="flex items-center gap-1 text-sm text-ink-muted hover:text-cinnabar-600 transition-colors">
          <Bookmark size={18} /> 收藏
        </button>
        <span className="flex items-center gap-1 text-sm text-ink-muted">
          <MessageCircle size={18} /> {item.comment_count || 0}
        </span>
      </div>

      <div className="mt-5">
        <h3 className="text-sm font-serif font-bold text-ink mb-3">评论 ({comments.length + (item.comment_count || 0)})</h3>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={comment}
            onChange={e => setComment(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleComment()}
            placeholder="写评论..."
            className="flex-1 px-3 py-2 glass-card rounded-xl text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15"
          />
          <button
            onClick={handleComment}
            disabled={!comment.trim()}
            className="p-2.5 cinnabar-gradient text-white rounded-xl hover:shadow-md transition-all disabled:opacity-40 disabled:shadow-none"
          >
            <Send size={15} />
          </button>
        </div>

        {comments.length === 0 ? (
          <p className="text-xs text-ink-muted text-center py-4">暂无评论，来写第一条吧</p>
        ) : (
          <div className="space-y-2.5">
            {comments.map((c, i) => (
              <GlassCard key={c.id || i} className="p-3">
                <div className="flex items-center justify-between text-xs text-ink-muted mb-1">
                  <span className="font-medium text-ink-secondary">{c.nickname}</span>
                  <span>{c.created_at?.slice(0, 10)}</span>
                </div>
                <p className="text-sm text-ink">{c.content}</p>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
