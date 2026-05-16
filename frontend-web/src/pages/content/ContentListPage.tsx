import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { ContentItem } from '../../types';
import CoverImage from '../../components/ui/CoverImage';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

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
    <div className="px-6 pb-9">
      {/* Hero Banner */}
      <div className="cinnabar-gradient rounded-[36px] p-5 mb-5 mt-4 shadow-[0_22px_46px_rgba(50,20,10,0.2)] rise-in">
        <span className="inline-block px-3.5 py-1 rounded-full bg-white/[0.14] text-amber-100 text-xs font-semibold mb-2.5 tracking-wide">
          非遗数字期刊
        </span>
        <h1 className="text-[26px] font-extrabold text-[#fff8f1] mt-0 mb-1 font-serif">非遗文化</h1>
        <p className="text-sm text-white/85 m-0">探索传统文化的精髓与传承</p>
      </div>

      {/* Search */}
      <div className="relative mb-3.5">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索非遗内容..."
          className="w-full h-10 rounded-full pl-[38px] pr-[18px] bg-parchment border border-[#ead7c0] text-sm text-ink outline-none box-border focus:border-cinnabar-200/60 focus:ring-2 focus:ring-cinnabar-800/10 transition-colors"
        />
      </div>

      {/* Category Chips */}
      <div className="flex gap-2 overflow-auto pb-2 mb-3.5 whitespace-nowrap">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`chip shrink-0 ${category === cat ? 'chip-active' : ''}`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="flex flex-col gap-3.5">
          {[1, 2, 3, 4].map(i => (
            <SkeletonLoader key={i} variant="card" className="!h-[90px]" />
          ))}
        </div>
      ) : contents.length === 0 ? (
        /* Empty State */
        <div className="text-center py-16 text-ink-muted text-sm">
          <span className="text-4xl opacity-20 block mb-3">📖</span>
          <p>暂无内容</p>
        </div>
      ) : (
        /* Content List */
        <div className="flex flex-col gap-3">
          {contents.map((item, idx) => (
            <GlassCard
              key={item.id}
              as="button"
              hover
              className="card-interactive p-3 flex gap-3 items-center text-left"
              onClick={() => navigate(`/content/${item.id}`)}
              style={{ animation: 'riseIn 0.44s ease-out both', animationDelay: `${0.1 + idx * 0.05}s` }}
            >
              {/* Thumbnail */}
              <div className="w-[88px] h-[88px] rounded-2xl shrink-0 bg-parchment-dark flex items-center justify-center overflow-hidden">
                {item.cover_url ? (
                  <CoverImage coverUrl={item.cover_url} alt="" loading="lazy" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-2xl opacity-30">📖</span>
                )}
              </div>

              {/* Text Content */}
              <div className="flex-1 min-w-0">
                {item.category && (
                  <span className="chip text-[10px] mb-1.5 inline-block !py-0.5 !px-2.5 !min-h-0">{item.category}</span>
                )}
                <h3 className="text-[15px] font-bold text-ink my-1 leading-snug line-clamp-2">{item.title}</h3>
                {item.summary && (
                  <p className="text-xs text-ink-secondary m-0 leading-relaxed line-clamp-2">{item.summary}</p>
                )}
              </div>
            </GlassCard>
          ))}
        </div>
      )}
    </div>
  );
}
