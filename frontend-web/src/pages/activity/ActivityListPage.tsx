import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Calendar, Users } from 'lucide-react';
import { apiRequest, buildImageUrl } from '../../lib/api';
import { Activity } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

const statuses = ['全部', 'open', 'closed', 'full'];

const statusLabels: Record<string, string> = { open: '报名中', closed: '已结束', full: '已满' };
const statusBg: Record<string, string> = {
  open: 'bg-jade-50 text-jade-600',
  closed: 'bg-ink-border/30 text-ink-muted',
  full: 'bg-orange-50 text-orange-600',
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
    <div className="px-4 py-5 space-y-4">
      <h1 className="text-xl font-serif font-bold text-ink">非遗活动</h1>

      {/* Status filter */}
      <div className="flex gap-2">
        {statuses.map(s => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
              status === s
                ? 'cinnabar-gradient text-white shadow-sm'
                : 'glass-card text-ink-secondary hover:text-ink'
            }`}
          >
            {s === '全部' ? '全部' : statusLabels[s] || s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <SkeletonLoader key={i} variant="card" />)}
        </div>
      ) : activities.length === 0 ? (
        <div className="text-center py-16">
          <Calendar size={40} className="text-ink-muted/40 mx-auto mb-2" />
          <p className="text-ink-muted text-sm">暂无活动</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {activities.map(item => (
            <button
              key={item.id}
              onClick={() => navigate(`/activity/${item.id}`)}
              className="w-full glass-card overflow-hidden hover:border-gold-200 transition-all text-left flex card-lift"
            >
              {item.cover_url ? (
                <div className="w-24 h-28 shrink-0 bg-parchment-dark">
                  <img src={buildImageUrl(item.cover_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" />
                </div>
              ) : (
                <div className="w-24 h-28 shrink-0 bg-jade-50 flex items-center justify-center">
                  <Calendar size={24} className="text-jade-400" />
                </div>
              )}
              <div className="flex-1 p-3 min-w-0">
                <h3 className="text-sm font-medium text-ink line-clamp-2">{item.title}</h3>
                <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5 text-xs text-ink-muted">
                  <span className="flex items-center gap-1"><MapPin size={11} /> {item.location}</span>
                  <span className="flex items-center gap-1"><Calendar size={11} /> {item.start_time?.slice(0, 10)}</span>
                  {item.current_participants !== undefined && (
                    <span className="flex items-center gap-1"><Users size={11} /> {item.current_participants}/{item.max_participants || '-'}</span>
                  )}
                </div>
                <span className={`inline-block mt-2 text-[11px] px-1.5 py-0.5 rounded-full ${statusBg[item.status] || 'bg-parchment-dark text-ink-muted'}`}>
                  {statusLabels[item.status] || item.status}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
