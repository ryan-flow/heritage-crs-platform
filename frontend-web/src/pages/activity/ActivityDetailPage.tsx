import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, MapPin, Calendar, Users, User } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { Activity } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

export default function ActivityDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ['activity', id],
    queryFn: () => apiRequest<{ code: number; data: Activity }>(`/events/${id}`),
    enabled: !!id,
  });

  const item = data?.data;

  if (isLoading) {
    return (
      <div className="px-4 py-4 space-y-3">
        <SkeletonLoader variant="image" className="!h-48" />
        <SkeletonLoader variant="text" className="!w-3/4" />
        <SkeletonLoader variant="text" className="!w-1/2" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="px-4 py-20 text-center">
        <p className="text-ink-muted">活动不存在</p>
        <button onClick={() => navigate(-1)} className="text-cinnabar-600 text-sm mt-2 hover:underline">返回</button>
      </div>
    );
  }

  const statusLabels: Record<string, string> = { open: '报名中', closed: '已结束', full: '已满' };
  const statusColors: Record<string, string> = {
    open: 'bg-jade-50 text-jade-600',
    closed: 'bg-ink-border/20 text-ink-muted',
    full: 'bg-orange-50 text-orange-600',
  };

  return (
    <div className="pb-8">
      {item.cover_url ? (
        <div className="h-48 bg-parchment-dark relative">
          <CoverImage coverUrl={item.cover_url} alt={item.title} className="w-full h-full object-cover" />
          <div className="absolute top-4 left-4">
            <button onClick={() => navigate(-1)} className="p-2 glass-card rounded-xl backdrop-blur-md">
              <ArrowLeft size={18} className="text-ink" />
            </button>
          </div>
        </div>
      ) : null}

      <div className="px-4">
        {!item.cover_url && (
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary mt-4 hover:text-ink transition-colors">
            <ArrowLeft size={16} /> 返回
          </button>
        )}

        <div className="flex items-center justify-between mt-4">
          <h1 className="text-xl font-serif font-bold text-ink flex-1">{item.title}</h1>
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium shrink-0 ${statusColors[item.status] || 'bg-parchment-dark text-ink-muted'}`}>
            {statusLabels[item.status] || item.status}
          </span>
        </div>

        <GlassCard className="mt-4 p-3.5 space-y-2.5">
          <div className="flex items-center gap-2 text-sm text-ink-secondary">
            <MapPin size={15} className="text-cinnabar-600" /> {item.location}
          </div>
          <div className="flex items-center gap-2 text-sm text-ink-secondary">
            <Calendar size={15} className="text-cinnabar-600" />
            {item.start_time?.slice(0, 10)} ~ {item.end_time?.slice(0, 10)}
          </div>
          {item.organizer && (
            <div className="flex items-center gap-2 text-sm text-ink-secondary">
              <User size={15} className="text-cinnabar-600" /> {item.organizer}
            </div>
          )}
          {item.max_participants && (
            <div className="flex items-center gap-2 text-sm text-ink-secondary">
              <Users size={15} className="text-cinnabar-600" />
              {item.current_participants || 0}/{item.max_participants} 人
            </div>
          )}
        </GlassCard>

        <div className="mt-5 text-sm text-ink leading-relaxed whitespace-pre-wrap font-sans">
          {item.description}
        </div>

        {item.status === 'open' && (
          <button
            onClick={() => navigate(`/activity/${id}/register`)}
            className="w-full mt-6 py-3 ink-btn ink-btn-primary !text-sm"
          >
            立即报名
          </button>
        )}
      </div>
    </div>
  );
}
