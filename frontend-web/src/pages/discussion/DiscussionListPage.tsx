import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Heart, MessageCircle, Bookmark, Plus } from 'lucide-react';
import { apiRequest, buildImageUrl } from '../../lib/api';
import { DiscussionTopic } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';
import { useAuthStore } from '../../stores/auth-store';

export default function DiscussionListPage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ['discussions'],
    queryFn: () => apiRequest<{ code: number; data: DiscussionTopic[] }>('/discussion/'),
  });

  const topics = (data?.data || []) as DiscussionTopic[];

  return (
    <div className="px-4 py-5 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-serif font-bold text-ink">社区讨论</h1>
        <button onClick={() => navigate('/discussion')}
          className="ink-btn ink-btn-primary !text-xs !px-3 !py-1.5">
          <Plus size={14} /> 发帖
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <SkeletonLoader key={i} variant="card" />)}
        </div>
      ) : topics.length === 0 ? (
        <div className="text-center py-16">
          <MessageCircle size={40} className="text-ink-muted/40 mx-auto mb-2" />
          <p className="text-ink-muted text-sm">暂无讨论</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {topics.map(item => (
            <button
              key={item.id}
              onClick={() => navigate(`/discussion/${item.id}`)}
              className="w-full glass-card p-3.5 hover:border-gold-200 transition-all text-left card-lift"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-cinnabar-100 flex items-center justify-center shrink-0">
                  <span className="text-cinnabar-600 font-bold text-sm">{(item.nickname || '匿')[0]}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-ink">{item.title}</h3>
                  <p className="text-xs text-ink-muted mt-1 line-clamp-2">
                    {item.content?.replace(/<[^>]*>/g, '').slice(0, 200)}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-ink-muted">
                    {item.nickname && <span className="text-ink-secondary">{item.nickname}</span>}
                    <span className="flex items-center gap-1"><Heart size={12} /> {item.like_count || 0}</span>
                    <span className="flex items-center gap-1"><MessageCircle size={12} /> {item.comment_count || 0}</span>
                    <span className="flex items-center gap-1"><Bookmark size={12} /> {item.favorite_count || 0}</span>
                    <span className="ml-auto">{item.created_at?.slice(0, 10)}</span>
                  </div>
                  {item.tags && item.tags.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {item.tags.slice(0, 3).map((t, i) => (
                        <span key={i} className="text-[10px] bg-parchment-dark text-ink-muted px-1.5 py-0.5 rounded-full">#{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
