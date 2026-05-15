import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { apiRequest, buildImageUrl } from '../../lib/api';
import { ContentItem } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

const categories = ['全部', '传统工艺', '戏曲音乐', '民俗节俗', '饮食医药', '民间文学', '传统美术'];

export default function ContentListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('全部');

  const { data, isLoading } = useQuery({
    queryKey: ['contents', category, search],
    queryFn: () => apiRequest<{ code: number; data: ContentItem[] }>(
      `/contents/?category=${category === '全部' ? '' : category}&search=${search}`),
  });

  const contents = (data?.data || []) as ContentItem[];

  return (
    <div className="px-4 py-5 space-y-4">
      <h1 className="text-xl font-serif font-bold text-ink">文化内容</h1>

      {/* Search */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索非遗内容..."
          className="w-full pl-9 pr-4 py-2.5 glass-card rounded-xl text-sm text-ink placeholder:text-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 focus:border-cinnabar-300/50 transition-all"
        />
      </div>

      {/* Category Filter */}
      <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`shrink-0 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all ${
              category === cat
                ? 'cinnabar-gradient text-white shadow-sm'
                : 'glass-card text-ink-secondary hover:text-ink hover:border-gold-200'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => <SkeletonLoader key={i} variant="card" />)}
        </div>
      ) : contents.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-ink-muted text-sm">暂无内容</p>
          <p className="text-ink-muted/60 text-xs mt-1">试试其他关键词或分类</p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {contents.map(item => (
            <button
              key={item.id}
              onClick={() => navigate(`/content/${item.id}`)}
              className="w-full glass-card overflow-hidden hover:border-gold-200 transition-all text-left flex card-lift"
            >
              {item.cover_url ? (
                <div className="w-24 h-24 shrink-0 bg-parchment-dark">
                  <img src={buildImageUrl(item.cover_url)} alt={item.title} className="w-full h-full object-cover" loading="lazy" />
                </div>
              ) : null}
              <div className="flex-1 p-3 min-w-0">
                {item.category && (
                  <SealBadge variant="gold">{item.category}</SealBadge>
                )}
                <h3 className="text-sm font-medium text-ink mt-1.5 line-clamp-2">{item.title}</h3>
                {item.summary && <p className="text-xs text-ink-muted mt-1 line-clamp-1">{item.summary}</p>}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex gap-1.5 mt-1.5 flex-wrap">
                    {item.tags.slice(0, 3).map((t, i) => (
                      <span key={i} className="text-[11px] text-ink-muted">#{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
