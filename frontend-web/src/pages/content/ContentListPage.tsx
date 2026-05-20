import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, Sparkles, BookOpen } from 'lucide-react';
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
  const allContents = (data?.data || []) as ContentItem[];

  // 拆分 featured、spotlight、waterfall 三部分（对标小程序）
  const featured = useMemo(() => allContents.find(c => c.is_featured), [allContents]);
  const spotlight = useMemo(() => allContents.filter(c => !c.is_featured).slice(0, 4), [allContents]);
  const waterfall = useMemo(() => {
    const rest = allContents.filter(c => !c.is_featured).slice(4);
    // 双列近似瀑布流分配
    const cols: ContentItem[][] = [[], []];
    rest.forEach((item, i) => {
      if (cols[0].length <= cols[1].length) {
        // 根据封面有无决定列分配 —— 有封面的放不同列更平衡
        if (cols[0].length === 0 || item.cover_url) cols[0].push(item);
        else cols[1].push(item);
      } else {
        cols[1].push(item);
      }
    });
    return cols;
  }, [allContents]);
  const recommendFirst = allContents.slice(0, 2);

  return (
    <div className="px-5 pb-9">

      {/* ═══════════════════════════════════════
          Hero 横幅 — 对标小程序 .heritage-hero（渐变背景）
         ═══════════════════════════════════════ */}
      <div className="relative rounded-[24px] overflow-hidden px-5 py-5 mt-3 mb-3"
        style={{
          background: 'linear-gradient(135deg, #5C3317 0%, #6B3A2A 40%, #8B5A3C 100%)',
          boxShadow: '0 22px 46px rgba(70, 35, 30, 0.24)',
        }}>
        <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/[0.04] blur-3xl pointer-events-none" />
        <span className="relative z-10 text-[11px] font-semibold text-[rgba(255,244,232,0.8)] tracking-[2px] mb-1 block">非遗数字期刊</span>
        <h1 className="relative z-10 text-[20px] font-bold text-[#fff8f1] mb-1 leading-tight"
          style={{ textShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>本周策展精选</h1>
        <p className="relative z-10 text-[12px] text-[rgba(255,244,232,0.85)] leading-relaxed">从一篇主专题开始，再按栏目浏览重点内容，像读一本非遗杂志。</p>
      </div>

      {/* ═══════════════════════════════════════
          为你推荐的内容 — 对标小程序 .recommend-inline
         ═══════════════════════════════════════ */}
      {recommendFirst.length > 0 && (
        <GlassCard className="px-4 py-3 mb-3">
          <span className="text-[12px] font-bold text-ink mb-2 block">为你推荐的内容</span>
          {recommendFirst.map((item, idx) => (
            <button key={item.id} onClick={() => navigate(`/content/${item.id}`)}
              className="w-full border-none bg-transparent p-0 cursor-pointer flex items-center gap-3 py-2.5 text-left
                border-t border-[rgba(143,108,73,0.1)] first:border-t-0 group">
              <div className="w-[80px] h-[45px] rounded-[10px] overflow-hidden shrink-0 bg-parchment-dark">
                {item.cover_url
                  ? <CoverImage coverUrl={item.cover_url} alt="" loading="lazy" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" />
                  : <div className="w-full h-full flex items-center justify-center text-xs text-ink-muted/40">封面</div>}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-bold text-ink line-clamp-1 leading-snug transition-colors group-hover:text-brand">{item.title}</div>
                <div className="text-[10px] text-ink-muted line-clamp-1 mt-0.5">{item.summary || '点击进入详情页'}</div>
                {item.reason && <div className="text-[10px] text-accent line-clamp-1 mt-0.5">{item.reason}</div>}
              </div>
              <span className="text-[16px] text-ink-muted/50 shrink-0">›</span>
            </button>
          ))}
        </GlassCard>
      )}

      {/* ═══════════════════════════════════════
          主专题卡片 — 对标小程序 .featured-card
         ═══════════════════════════════════════ */}
      {featured && (
        <GlassCard hover as="button" onClick={() => navigate(`/content/${featured.id}`)}
          className="p-0 overflow-hidden cursor-pointer text-left mb-3 w-full border-none">
          {featured.cover_url && (
            <div className="h-[140px] overflow-hidden">
              <CoverImage coverUrl={featured.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 hover:scale-105" loading="lazy" />
            </div>
          )}
          <div className="p-4">
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[10px] font-bold text-brand bg-brand-soft px-2 py-0.5 rounded-full">主专题</span>
              <span className="text-[10px] text-ink-muted">{featured.category || '非遗文化'}</span>
            </div>
            <h2 className="text-[16px] font-bold text-ink leading-snug mb-1">{featured.title}</h2>
            <p className="text-[11px] text-ink-secondary line-clamp-2 mb-1">{featured.summary || '点击查看完整专题导读'}</p>
            <span className="text-[10px] text-ink-muted">{featured.chapter || '非遗文化'} · {featured.sub_chapter || '专题'}</span>
          </div>
        </GlassCard>
      )}

      {/* ═══════════════════════════════════════
          搜索 + 分类筛选
         ═══════════════════════════════════════ */}
      <GlassCard className="px-4 py-3 mb-3">
        <div className="relative mb-2.5">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="搜索标题..."
            className="w-full h-8 rounded-full pl-[32px] pr-3 bg-parchment border border-[#ead7c0] text-[11px] text-ink outline-none box-border focus:border-cinnabar-200/60 transition-colors"
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1 whitespace-nowrap scrollbar-hide">
          {categories.map(cat => (
            <button key={cat} onClick={() => setCategory(cat)}
              className="shrink-0 inline-flex items-center px-3 py-1.5 rounded-full text-[11px] font-medium border-none cursor-pointer transition-all duration-200"
              style={{
                background: category === cat ? 'linear-gradient(135deg, #9f2d22, #bf563f)' : '#f7e7dc',
                color: category === cat ? '#fff' : '#9f2d22',
                boxShadow: category === cat ? '0 4px 10px rgba(159,45,34,0.2)' : 'none',
              }}>
              {cat}
            </button>
          ))}
        </div>
      </GlassCard>

      {/* ═══════════════════════════════════════
          聚焦横滑 — 对标小程序 .spotlight-row
         ═══════════════════════════════════════ */}
      {spotlight.length > 0 && (
        <div className="mb-3">
          <span className="text-[12px] font-bold text-ink mb-2 block px-1">聚焦</span>
          <div className="flex gap-2.5 overflow-x-auto pb-1 snap-x snap-mandatory scrollbar-hide -mx-1 px-1">
            {spotlight.map(item => (
              <button key={item.id} onClick={() => navigate(`/content/${item.id}`)}
                className="snap-start shrink-0 w-[130px] rounded-[14px] overflow-hidden text-left border-none bg-white cursor-pointer group
                  transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
                style={{
                  background: 'rgba(255, 251, 245, 0.96)',
                  boxShadow: '0 6px 16px rgba(121,58,31,0.06)',
                  border: '1px solid rgba(219,191,155,0.18)',
                }}>
                <div className="h-[80px] bg-parchment-dark overflow-hidden">
                  {item.cover_url
                    ? <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
                    : <div className="w-full h-full flex items-center justify-center text-2xl opacity-30">📖</div>}
                </div>
                <div className="p-2.5">
                  {item.category && (
                    <span className="text-[9px] text-jade-600 bg-jade-50 px-1.5 py-0.5 rounded-full font-medium">{item.category}</span>
                  )}
                  <div className="text-[12px] font-bold text-ink line-clamp-2 leading-snug mt-1 group-hover:text-brand transition-colors">{item.title}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════
          瀑布流主内容区 — 对标小程序 .waterfall + .column
         ═══════════════════════════════════════ */}
      {isLoading ? (
        <div className="flex gap-3">
          <div className="flex-1 space-y-3">
            {[1, 2].map(i => <SkeletonLoader key={i} variant="card" className="!h-[160px]" />)}
          </div>
          <div className="flex-1 space-y-3">
            {[1, 2].map(i => <SkeletonLoader key={i} variant="card" className="!h-[200px]" />)}
          </div>
        </div>
      ) : waterfall[0].length === 0 && waterfall[1].length === 0 ? (
        <div className="text-center py-16 text-ink-muted text-sm">
          <span className="text-4xl opacity-20 block mb-3">📖</span>
          <p>暂无内容</p>
        </div>
      ) : (
        <div className="flex gap-3" style={{ alignItems: 'flex-start' }}>
          {/* 左列 */}
          <div className="flex-1 flex flex-col gap-3">
            {waterfall[0].map(item => (
              <button key={item.id} onClick={() => navigate(`/content/${item.id}`)}
                className="w-full rounded-[14px] overflow-hidden text-left border-none bg-white cursor-pointer group
                  transition-all duration-200 hover:-translate-y-[2px] hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: 'rgba(255, 251, 245, 0.96)',
                  boxShadow: '0 6px 16px rgba(121,58,31,0.06)',
                  border: '1px solid rgba(219,191,155,0.18)',
                }}>
                {item.cover_url && (
                  <div className="h-[100px] bg-parchment-dark overflow-hidden">
                    <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
                  </div>
                )}
                <div className="p-3">
                  {item.category && (
                    <span className="text-[9px] text-jade-600 bg-jade-50 px-1.5 py-0.5 rounded-full font-medium">{item.category}</span>
                  )}
                  <div className="text-[13px] font-bold text-ink leading-snug mt-1 line-clamp-2 group-hover:text-brand transition-colors">{item.title}</div>
                  {item.summary && (
                    <p className="text-[10px] text-ink-secondary mt-1 line-clamp-2 leading-relaxed">{item.summary}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
          {/* 右列 */}
          <div className="flex-1 flex flex-col gap-3">
            {waterfall[1].map(item => (
              <button key={item.id} onClick={() => navigate(`/content/${item.id}`)}
                className="w-full rounded-[14px] overflow-hidden text-left border-none bg-white cursor-pointer group
                  transition-all duration-200 hover:-translate-y-[2px] hover:shadow-lg active:scale-[0.98]"
                style={{
                  background: 'rgba(255, 251, 245, 0.96)',
                  boxShadow: '0 6px 16px rgba(121,58,31,0.06)',
                  border: '1px solid rgba(219,191,155,0.18)',
                }}>
                {item.cover_url && (
                  <div className="h-[120px] bg-parchment-dark overflow-hidden">
                    <CoverImage coverUrl={item.cover_url} alt="" className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy" />
                  </div>
                )}
                <div className="p-3">
                  {item.category && (
                    <span className="text-[9px] text-jade-600 bg-jade-50 px-1.5 py-0.5 rounded-full font-medium">{item.category}</span>
                  )}
                  <div className="text-[13px] font-bold text-ink leading-snug mt-1 line-clamp-2 group-hover:text-brand transition-colors">{item.title}</div>
                  {item.summary && (
                    <p className="text-[10px] text-ink-secondary mt-1 line-clamp-2 leading-relaxed">{item.summary}</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
