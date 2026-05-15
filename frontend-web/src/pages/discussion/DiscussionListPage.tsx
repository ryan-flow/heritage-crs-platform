import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Heart, MessageCircle, Bookmark, Plus } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { DiscussionTopic } from '../../types';

export default function DiscussionListPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ['discussions'],
    queryFn: () => apiRequest<{ code: number; data: DiscussionTopic[] }>('/discussion/'),
  });
  const topics = (data?.data || []) as DiscussionTopic[];

  return (
    <div style={{ padding: '0 24rpx 36rpx' }}>
      {/* Hero */}
      <div className="rise-in" style={{
        background: 'linear-gradient(135deg, #6B3A2A, #9B4F3C)',
        borderRadius: '36rpx', padding: '20rpx 24rpx', marginBottom: 20, marginTop: 16,
        boxShadow: '0 22rpx 46rpx rgba(60,20,10,0.2)',
      }}>
        <span style={{ display: 'inline-block', padding: '4rpx 14rpx', borderRadius: 999, background: 'rgba(255,245,230,0.14)', color: '#ffe1bc', fontSize: 12, fontWeight: 600, marginBottom: 10 }}>
          非遗社区交流
        </span>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: '#fff8f1', margin: '0 0 4rpx' }}>社区讨论</h1>
        <p style={{ fontSize: 14, color: 'rgba(255,244,232,0.86)', margin: 0 }}>分享和探讨非遗文化的方方面面</p>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
      ) : topics.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60rpx 0', color: '#a08868', fontSize: 14 }}>
          <MessageCircle size={32} style={{ display: 'block', margin: '0 auto 12rpx', opacity: 0.4 }} />
          <p>暂无讨论</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {topics.map((item, idx) => (
            <button key={item.id} onClick={() => navigate(`/discussion/${item.id}`)}
              className="card rise-in"
              style={{
                margin: 0, textAlign: 'left', border: 'none', cursor: 'pointer', width: '100%',
                animationDelay: `${0.1 + idx * 0.05}s`,
              }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
                  background: 'linear-gradient(135deg, #9f2d22, #bf563f)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff7ef', fontSize: 16, fontWeight: 700,
                }}>
                  {(item.nickname || '匿')[0]}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: '#322418', margin: '0 0 6rpx' }}>{item.title}</h3>
                  <p style={{ fontSize: 13, color: '#674d36', margin: '0 0 8rpx', lineHeight: 1.6, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.content?.replace(/<[^>]*>/g, '').slice(0, 200)}
                  </p>
                  <div style={{ display: 'flex', gap: 14, fontSize: 11, color: '#8b6a4b' }}>
                    {item.nickname && <span>{item.nickname}</span>}
                    <span>👍 {item.like_count || 0}</span>
                    <span>💬 {item.comment_count || 0}</span>
                    <span>🔖 {item.favorite_count || 0}</span>
                    <span style={{ marginLeft: 'auto', color: '#a08868' }}>{item.created_at?.slice(0, 10)}</span>
                  </div>
                  {item.tags && item.tags.length > 0 && (
                    <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                      {item.tags.slice(0, 3).map((t, i) => (
                        <span key={i} className="chip" style={{ fontSize: 11 }}>#{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Composer FAB */}
      <button onClick={() => navigate('/discussion')}
        style={{
          position: 'fixed', right: 20, bottom: 100, zIndex: 90,
          width: 56, height: 56, borderRadius: '50%',
          background: 'linear-gradient(135deg, #7a2f25, #b74f3b)',
          boxShadow: '0 14rpx 30rpx rgba(126,45,35,0.28)',
          border: 'none', cursor: 'pointer',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          color: '#fff',
        }}>
      <Plus size={24} />
      <span style={{ fontSize: 9, fontWeight: 700, marginTop: -2 }}>发帖</span>
    </button>
    </div>
  );
}
