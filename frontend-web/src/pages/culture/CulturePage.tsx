import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ChevronRight } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { ContentItem } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

const CHAPTERS = [
  { key: 'intangible_heritage_overview', label: '非遗总览' },
  { key: 'traditional_crafts', label: '传统工艺' },
  { key: 'performing_arts', label: '表演艺术' },
  { key: 'folk_customs', label: '民俗节庆' },
  { key: 'oral_literature', label: '口头文学' },
  { key: 'heritage_medicine', label: '传统医药' },
];

export default function CulturePage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [activeChapter, setActiveChapter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['culture', activeChapter, search],
    queryFn: () => apiRequest<{ code: number; data: ContentItem[] }>(`/contents/?chapter=${activeChapter}&search=${search}`),
  });

  const items = (data?.data || []) as ContentItem[];

  return (
    <div className="px-4 py-5 space-y-4">
      <h1 className="text-xl font-serif font-bold text-ink">非遗文化</h1>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索非遗文化知识..."
          className="w-full pl-9 pr-4 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15"
        />
      </div>

      <div className="grid grid-cols-3 gap-2">
        {CHAPTERS.map(ch => (
          <button
            key={ch.key}
            onClick={() => { setActiveChapter(ch.key); setSearch(''); }}
            className={`p-3 rounded-xl text-center text-xs font-medium transition-all ${
              activeChapter === ch.key ? 'cinnabar-gradient text-white shadow-sm' : 'glass-card text-ink-secondary hover:text-ink'
            }`}
          >
            {ch.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => <SkeletonLoader key={i} variant="card" className="!h-20" />)}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-ink-muted text-sm">{activeChapter ? '该分类暂无内容' : '请选择一个分类查看'}</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map(item => (
            <button
              key={item.id}
              onClick={() => navigate(`/culture/${item.id}`)}
              className="w-full glass-card p-3 hover:border-gold-200 transition-all text-left flex items-center gap-3 card-lift"
            >
              {item.cover_url && (
                <div className="w-14 h-14 shrink-0 rounded-lg overflow-hidden bg-parchment-dark">
                  <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-ink line-clamp-2">{item.title}</h3>
                <p className="text-xs text-ink-muted mt-0.5 line-clamp-1">{item.summary}</p>
              </div>
              <ChevronRight size={16} className="text-ink-muted shrink-0" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
