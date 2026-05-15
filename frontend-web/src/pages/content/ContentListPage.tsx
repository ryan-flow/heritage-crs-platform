import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { apiRequest, buildImageUrl } from '../../lib/api';
import { ContentItem } from '../../types';

const categories = ['全部', '传统工艺', '戏曲音乐', '民俗节俗', '饮食医药', '民间文学', '传统美术'];

export default function ContentListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('全部');
  const { data, isLoading } = useQuery({
    queryKey: ['contents', category, search],
    queryFn: () => apiRequest<{ code: number; data: ContentItem[] }>(`/contents/?category=${category === '全部' ? '' : category}&search=${search}`),
  });
  const contents = (data?.data || []) as ContentItem[];

  return (
    <div style={{ padding: '0 24rpx 36rpx' }}>
      {/* Hero Banner */}
      <div className="rise-in" style={{
        background: 'linear-gradient(135deg, #5C3317, #8B5A3C)',
        borderRadius: '36rpx', padding: '20rpx 24rpx', marginBottom: 20, marginTop: 16,
        boxShadow: '0 22rpx 46rpx rgba(50,20,10,0.2)',
      }}>
        <span style={{ display: 'inline-block', padding: '4rpx 14rpx', borderRadius: 999, background: 'rgba(255,245,230,0.14)', color: '#ffe1bc', fontSize: 12, fontWeight: 600, marginBottom: 10 }}>
          非遗数字期刊
        </span>
        <h1 className="page-title" style={{ color: '#fff8f1', margin: '0 0 4rpx', fontSize: 26, fontWeight: 800 }}>非遗文化</h1>
        <p style={{ fontSize: 14, color: 'rgba(255,244,232,0.86)', margin: 0 }}>探索传统文化的精髓与传承</p>
      </div>

      {/* Search */}
      <div style={{ position: 'relative', marginBottom: 14 }}>
        <Search size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#a08868' }} />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)}
          placeholder="搜索非遗内容..."
          style={{
            width: '100%', height: 40, borderRadius: 999, padding: '0 18rpx 0 38rpx',
            background: '#fffdf8', border: '1rpx solid #ead7c0', fontSize: 14,
            color: '#2f2419', outline: 'none', boxSizing: 'border-box',
          }} />
      </div>

      {/* Category chips */}
      <div style={{ display: 'flex', gap: 8, overflow: 'auto', paddingBottom: 8, marginBottom: 14, whiteSpace: 'nowrap' }}>
        {categories.map(cat => (
          <button key={cat} onClick={() => setCategory(cat)}
            className={`chip ${category === cat ? 'chip-active' : ''}`}
            style={{ flexShrink: 0 }}>
            {cat}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 90 }} />)}
        </div>
      ) : contents.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60rpx 0', color: '#a08868', fontSize: 14 }}>暂无内容</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {contents.map((item, idx) => (
            <button key={item.id} onClick={() => navigate(`/content/${item.id}`)}
              className="card rise-in"
              style={{ margin: 0, display: 'flex', gap: 12, alignItems: 'center', textAlign: 'left', border: 'none', cursor: 'pointer', width: '100%',
                animationDelay: `${0.1 + idx * 0.05}s` }}>
              <div style={{
                width: 72, height: 72, borderRadius: 14, flexShrink: 0,
                background: 'linear-gradient(135deg, #f5e8d5, #eadcc8)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, color: '#c08a3e', overflow: 'hidden',
              }}>
                {item.cover_url
                  ? <img src={buildImageUrl(item.cover_url)} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : '📖'}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                {item.category && <span className="chip" style={{ fontSize: 11, marginBottom: 6, display: 'inline-block' }}>{item.category}</span>}
                <h3 style={{ fontSize: 15, fontWeight: 700, color: '#332418', margin: '4rpx 0', lineHeight: 1.3 }}>{item.title}</h3>
                {item.summary && <p style={{ fontSize: 12, color: '#7c5f44', margin: 0, lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{item.summary}</p>}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
