import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Calendar, Users } from 'lucide-react';
import { apiRequest, buildImageUrl } from '../../lib/api';
import { Activity } from '../../types';

const statuses = ['全部', 'open', 'closed', 'full'] as const;
const statusLabels: Record<string, string> = { open: '报名中', closed: '已结束', full: '已满' };

export default function ActivityListPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState('全部');
  const { data, isLoading } = useQuery({
    queryKey: ['activities', status],
    queryFn: () => apiRequest<{ code: number; data: Activity[] }>(`/events/?status=${status === '全部' ? '' : status}`),
  });
  const activities = (data?.data || []) as Activity[];

  return (
    <div style={{ padding: '0 24rpx 36rpx' }}>
      {/* Hero */}
      <div className="rise-in" style={{
        background: 'linear-gradient(135deg, #6B3A2A, #9B4F3C)',
        borderRadius: '36rpx', padding: '20rpx 24rpx', marginBottom: 20, marginTop: 16,
        boxShadow: '0 22rpx 46rpx rgba(60,20,10,0.2)',
      }}>
        <span style={{ display: 'inline-block', padding: '4rpx 14rpx', borderRadius: 999, background: 'rgba(255,245,230,0.14)', color: '#ffe1bc', fontSize: 12, fontWeight: 600, marginBottom: 10 }}>
          活动日历中心
        </span>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#fff8f1', margin: '0 0 4rpx' }}>非遗体验活动</h1>
        <p style={{ fontSize: 14, color: 'rgba(255,244,232,0.86)', margin: 0 }}>线下活动、体验工坊、文化节庆</p>
      </div>

      {/* Status filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {statuses.map(s => (
          <button key={s} onClick={() => setStatus(s)}
            className={`chip ${status === s ? 'chip-active' : ''}`}>
            {s === '全部' ? '全部' : statusLabels[s] || s}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
      ) : activities.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60rpx 0', color: '#a08868', fontSize: 14 }}>
          <Calendar size={32} style={{ display: 'block', margin: '0 auto 12rpx', opacity: 0.4 }} />
          <p>暂无活动</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {activities.map((item, idx) => (
            <button key={item.id} onClick={() => navigate(`/activity/${item.id}`)}
              className="card rise-in"
              style={{
                margin: 0, textAlign: 'left', border: 'none', cursor: 'pointer', width: '100%',
                padding: 0, overflow: 'hidden',
                animationDelay: `${0.1 + idx * 0.05}s`,
              }}>
              <div style={{
                height: 160, background: 'linear-gradient(135deg, #f0e6d8, #e0d0b8)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                position: 'relative',
              }}>
                {item.cover_url
                  ? <img src={buildImageUrl(item.cover_url)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <Calendar size={48} style={{ color: '#c08a3e', opacity: 0.4 }} />}
                <span style={{
                  position: 'absolute', top: 12, left: 12,
                  padding: '5rpx 12rpx', borderRadius: 999, fontSize: 11, fontWeight: 600,
                  background: 'rgba(50,28,20,0.66)', color: '#ffe1bc',
                }}>
                  {statusLabels[item.status] || item.status}
                </span>
              </div>
              <div style={{ padding: '16rpx 18rpx' }}>
                <h3 style={{ fontSize: 16, fontWeight: 800, color: '#342114', margin: '0 0 8rpx' }}>{item.title}</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6rpx 14rpx', fontSize: 11, color: '#8b6a4b' }}>
                  <span><MapPin size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />{item.location}</span>
                  <span><Calendar size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />{item.start_time?.slice(0, 10)}</span>
                  {item.max_participants && (
                    <span><Users size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />{item.current_participants || 0}/{item.max_participants}</span>
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
