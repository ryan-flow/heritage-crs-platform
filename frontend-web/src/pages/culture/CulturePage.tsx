import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ChevronRight, BookOpen } from 'lucide-react';
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
    <div className="pb-8 space-y-5">

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-[36px] bg-gradient-to-br from-cinnabar-700 via-brand to-gold-400 mx-4 mt-4 p-6 pb-8">
        <div className="relative z-10">
          <h1 className="text-2xl font-serif font-bold text-white leading-snug">
            非遗文化
          </h1>
          <p className="text-sm text-white/70 mt-1 font-sans">
            探索中华非物质文化遗产的深厚底蕴
          </p>
        </div>
        {/* Decorative ink wash */}
        <div className="absolute inset-0 bg-radial from-white/5 to-transparent pointer-events-none" />
      </div>

      {/* Search */}
      <div className="px-4 relative">
        <Search size={16} className="absolute left-7 top-1/2 -translate-y-1/2 text-ink-muted pointer-events-none z-10" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="搜索非遗文化知识..."
          className="w-full pl-9 pr-4 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 font-sans placeholder:text-ink-muted/50"
        />
      </div>

      {/* Chapter Tabs */}
      <div className="px-4">
        <div className="grid grid-cols-3 gap-2">
          {CHAPTERS.map((ch, i) => (
            <button
              key={ch.key}
              onClick={() => { setActiveChapter(ch.key); setSearch(''); }}
              className={`rise-in p-3 rounded-xl text-center text-xs font-medium transition-all font-sans ${
                activeChapter === ch.key
                  ? 'cinnabar-gradient text-white shadow-md'
                  : 'glass-card text-ink-secondary hover:text-ink card-lift'
              }`}
              style={{ animationDelay: `${i * 0.04}s` }}
            >
              {ch.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="px-4">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map(i => (
              <SkeletonLoader key={i} variant="card" className="!h-20" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-parchment-dark flex items-center justify-center">
              <BookOpen size={28} className="text-ink-muted/40" />
            </div>
            <p className="text-ink-muted text-sm font-sans">
              {activeChapter ? '该分类暂无内容' : '请选择一个分类查看'}
            </p>
            {activeChapter && (
              <button
                onClick={() => setActiveChapter('')}
                className="mt-3 text-sm text-brand hover:underline font-sans"
              >
                查看全部
              </button>
            )}
          </div>
        ) : (
          <div className="space-y-2 rise-in-stagger">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => navigate(`/culture/${item.id}`)}
                className="w-full glass-card p-3 card-interactive text-left flex items-center gap-3 guofeng-press"
              >
                {item.cover_url && (
                  <div className="w-14 h-14 shrink-0 rounded-lg overflow-hidden bg-parchment-dark">
                    <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover" loading="lazy" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-ink line-clamp-2 font-sans">{item.title}</h3>
                  <p className="text-xs text-ink-muted mt-0.5 line-clamp-1 font-sans">{item.summary}</p>
                </div>
                <ChevronRight size={16} className="text-ink-muted shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
