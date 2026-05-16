import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, MapPin, Calendar, Users, User } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { Activity } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { InkButton } from '../../components/ui/InkButton';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';
import FloatingAiButton from '../../components/ui/FloatingAiButton';

const statusLabels: Record<string, string> = { open: '报名中', closed: '已结束', full: '已满' };
const statusSealVariant: Record<string, 'jade' | 'cinnabar' | undefined> = {
  open: 'jade',
  closed: undefined,
  full: 'cinnabar',
};

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
        {[1, 2, 3].map(i => <SkeletonLoader key={i} variant="text" />)}
      </div>
    );
  }

  if (!item) {
    return (
      <div className="px-4 py-20 text-center">
        <span className="text-4xl opacity-20 block mb-4">🎭</span>
        <p className="text-ink-muted text-sm">活动不存在</p>
        <button onClick={() => navigate(-1)} className="text-cinnabar-600 text-sm mt-2 hover:underline transition-colors">返回</button>
      </div>
    );
  }

  return (
    <div className="pb-8">
      {/* Hero Image Area */}
      {item.cover_url ? (
        <div className="h-48 bg-parchment-dark relative">
          <CoverImage coverUrl={item.cover_url} alt={item.title} className="w-full h-full object-cover" />
          <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-black/30 to-transparent pointer-events-none" />
          <div className="absolute top-4 left-4">
            <GlassCard as="button" onClick={() => navigate(-1)} className="p-2 rounded-xl cursor-pointer backdrop-blur-md">
              <ArrowLeft size={18} className="text-ink" />
            </GlassCard>
          </div>
        </div>
      ) : (
        /* No Cover Fallback */
        <div className="h-32 bg-gradient-to-b from-parchment-dark/60 to-parchment-dark/20 flex items-end px-4 pb-2">
          <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary hover:text-ink transition-colors mb-2">
            <ArrowLeft size={16} /> 返回
          </button>
        </div>
      )}

      <div className="px-4">
        {/* Title + Status */}
        <div className="flex items-start justify-between gap-3 mt-4">
          <h1 className="text-xl font-serif font-bold text-ink flex-1 leading-snug">{item.title}</h1>
          {item.status && (
            <span className="shrink-0 mt-0.5">
              <SealBadge variant={statusSealVariant[item.status]}>
                {statusLabels[item.status] || item.status}
              </SealBadge>
            </span>
          )}
        </div>

        {/* Info Card */}
        <GlassCard className="mt-4 p-3.5 space-y-2.5">
          <div className="flex items-center gap-2.5 text-sm text-ink-secondary">
            <MapPin size={15} className="text-cinnabar-500 shrink-0" />
            <span>{item.location}</span>
          </div>
          <div className="flex items-center gap-2.5 text-sm text-ink-secondary">
            <Calendar size={15} className="text-cinnabar-500 shrink-0" />
            <span>{item.start_time?.slice(0, 10)} ~ {item.end_time?.slice(0, 10)}</span>
          </div>
          {item.organizer && (
            <div className="flex items-center gap-2.5 text-sm text-ink-secondary">
              <User size={15} className="text-cinnabar-500 shrink-0" />
              <span>{item.organizer}</span>
            </div>
          )}
          {item.max_participants ? (
            <div className="flex items-center gap-2.5 text-sm text-ink-secondary">
              <Users size={15} className="text-cinnabar-500 shrink-0" />
              <span>{item.current_participants || 0}/{item.max_participants} 人</span>
            </div>
          ) : null}
        </GlassCard>

        {/* Description */}
        <div className="mt-5 text-sm text-ink leading-relaxed whitespace-pre-wrap font-sans">
          {item.description}
        </div>

        {/* Register Button */}
        {item.status === 'open' && (
          <InkButton
            variant="primary"
            onClick={() => navigate(`/activity/${id}/register`)}
            className="w-full mt-6"
          >
            立即报名
          </InkButton>
        )}
      </div>
      <FloatingAiButton context={item?.title} />
    </div>
  );
}
