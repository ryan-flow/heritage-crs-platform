import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Calendar, Users } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { Activity } from '../../types';
import CoverImage from '../../components/ui/CoverImage';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

const statuses = ['全部', 'open', 'closed', 'full'] as const;
const statusLabels: Record<string, string> = { open: '报名中', closed: '已结束', full: '已满' };
const statusSealVariant: Record<string, 'gold' | 'jade' | 'cinnabar' | undefined> = {
  open: 'jade',
  closed: undefined,
  full: 'cinnabar',
};

export default function ActivityListPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState('全部');
  const { data, isLoading } = useQuery({
    queryKey: ['activities', status],
    queryFn: () => apiRequest<{ code: number; data: Activity[] }>(`/events/?status=${status === '全部' ? '' : status}`),
  });
  const activities = (data?.data || []) as Activity[];

  return (
    <div className="px-6 pb-9">
      {/* Hero Banner */}
      <div className="cinnabar-gradient rounded-[36px] p-5 mb-5 mt-4 shadow-[0_22px_46px_rgba(50,20,10,0.2)] rise-in">
        <span className="inline-block px-3.5 py-1 rounded-full bg-white/[0.14] text-amber-100 text-xs font-semibold mb-2.5 tracking-wide">
          活动日历中心
        </span>
        <h1 className="text-[26px] font-extrabold text-[#fff8f1] mt-0 mb-1 font-serif">非遗体验活动</h1>
        <p className="text-sm text-white/85 m-0">线下活动、体验工坊、文化节庆</p>
      </div>

      {/* Status Filter Chips */}
      <div className="flex gap-2 mb-4">
        {statuses.map(s => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`chip shrink-0 ${status === s ? 'chip-active' : ''}`}
          >
            {s === '全部' ? '全部' : statusLabels[s] || s}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex flex-col gap-3.5">
          {[1, 2, 3].map(i => (
            <SkeletonLoader key={i} variant="card" className="!h-[180px]" />
          ))}
        </div>
      ) : activities.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 text-ink-muted text-sm">
          <Calendar size={32} className="mx-auto mb-3 opacity-25" />
          <p>暂无活动</p>
        </div>
      ) : (
        /* Activity List */
        <div className="flex flex-col gap-3.5">
          {activities.map((item, idx) => (
            <GlassCard
              key={item.id}
              as="button"
              hover
              className="card-interactive p-0 overflow-hidden text-left"
              onClick={() => navigate(`/activity/${item.id}`)}
              style={{ animation: 'riseIn 0.44s ease-out both', animationDelay: `${0.1 + idx * 0.05}s` }}
            >
              {/* Cover Image */}
              <div className="h-[180px] bg-parchment-dark relative flex items-center justify-center">
                <CoverImage
                  coverUrl={item.cover_url}
                  alt=""
                  loading="lazy"
                  className="w-full h-full object-cover"
                  fallback={<Calendar size={48} className="text-gold-500 opacity-25" />}
                />
                {/* Gradient overlay for badge readability */}
                <div className="absolute inset-x-0 top-0 h-16 bg-gradient-to-b from-black/35 to-transparent pointer-events-none" />
                {/* Status Badge */}
                {item.status && item.status !== '全部' && (
                  <span className="absolute top-3 left-3">
                    <SealBadge variant={statusSealVariant[item.status]}>
                      {statusLabels[item.status] || item.status}
                    </SealBadge>
                  </span>
                )}
              </div>

              {/* Info Area */}
              <div className="p-4">
                <h3 className="text-base font-extrabold text-ink mb-2 leading-snug line-clamp-2">{item.title}</h3>
                <div className="flex flex-wrap gap-x-3.5 gap-y-1.5 text-[11px] text-ink-muted">
                  <span className="inline-flex items-center gap-1">
                    <MapPin size={10} /> {item.location}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Calendar size={10} /> {item.start_time?.slice(0, 10)}
                  </span>
                  {item.max_participants ? (
                    <span className="inline-flex items-center gap-1">
                      <Users size={10} /> {item.current_participants || 0}/{item.max_participants}
                    </span>
                  ) : null}
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
