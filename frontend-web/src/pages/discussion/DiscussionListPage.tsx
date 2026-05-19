import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Heart, MessageCircle, Bookmark, Plus, Search, Flame } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { DiscussionTopic } from '../../types';
import CoverImage from '../../components/ui/CoverImage';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

const TAG_FILTERS = ['戏曲', '工艺', '节俗', '求科普', '传统音乐', '传统美术', '传统技艺', '民俗'];

export default function DiscussionListPage() {
  const navigate = useNavigate();
  const [sort, setSort] = useState<'new' | 'hot'>('hot');
  const [search, setSearch] = useState('');
  const [activeTag, setActiveTag] = useState('');
  const [favoriteOnly, setFavoriteOnly] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['discussions', sort, search, activeTag, favoriteOnly],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set('sort', sort);
      if (search.trim()) params.set('keyword', search.trim());
      if (activeTag) params.set('tag', activeTag);
      if (favoriteOnly) params.set('favorite', 'true');
      return apiRequest<{ code: number; data: DiscussionTopic[] }>(`/discussion/?${params.toString()}`);
    },
  });
  const topics = (data?.data || []) as DiscussionTopic[];

  // 推荐讨论（取前3条）
  const recommendedTopics = topics.slice(0, 3);
  // 热榜（按热度排序取前5）
  const hotList = [...topics].sort((a, b) => (b.heat_score || 0) - (a.heat_score || 0)).slice(0, 5);

  return (
    <div className="px-5 pb-28 pt-1">
      {/* ── Hero Banner ── */}
      <div
        className="rise-in relative overflow-hidden mb-4 mt-3 p-5 rounded-[24px]"
        style={{
          background: 'linear-gradient(135deg, #6B3A2A 0%, #9B4F3C 50%, #b85d47 100%)',
          boxShadow: '0 22px 46px rgba(60, 20, 10, 0.22)',
        }}
      >
        <span className="relative inline-block px-3 py-1 rounded-full text-xs font-semibold tracking-wide bg-white/12 text-[#ffe1bc] mb-2.5">
          非遗社区交流
        </span>
        <h1 className="relative font-serif text-[26px] font-extrabold text-[#fff8f1] leading-tight mb-1">
          讨论区 · 热榜与模板发帖
        </h1>
        <p className="relative text-sm text-white/85 font-sans">
          先看热点，再输出观点。
        </p>
      </div>

      {/* ── 推荐讨论 ── */}
      {recommendedTopics.length > 0 && (
        <div className="mb-4">
          <h2 className="text-base font-bold text-[#3a2619] mb-2.5">为你推荐的讨论</h2>
          <div className="flex flex-col gap-2">
            {recommendedTopics.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => navigate(`/discussion/${item.id}`)}
                className="card-interactive w-full text-left"
              >
                <GlassCard hover className="p-3 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#9f2d22] to-[#c08a3e] flex items-center justify-center text-white text-xs font-bold shrink-0">
                    荐
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-[#322418] mb-0.5 line-clamp-1">{item.title}</h3>
                    <p className="text-[11px] text-[#8a6b4a] line-clamp-1">
                      匹配你的兴趣标签
                    </p>
                  </div>
                  <span className="text-[#a8713c] text-xl shrink-0">›</span>
                </GlassCard>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── 今日热榜 ── */}
      {hotList.length > 0 && (
        <div className="mb-4">
          <h2 className="text-base font-bold text-[#3a2619] mb-2.5">今日热榜</h2>
          <div className="flex flex-col gap-2">
            {hotList.map((item, idx) => (
              <button
                key={item.id}
                type="button"
                onClick={() => navigate(`/discussion/${item.id}`)}
                className="card-interactive w-full text-left"
              >
                <GlassCard hover className="p-3 flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
                    style={{
                      background: idx === 0
                        ? 'linear-gradient(135deg, #9f2d22, #c56a2d)'
                        : idx === 1
                        ? 'linear-gradient(135deg, #8d4a24, #c69152)'
                        : idx === 2
                        ? 'linear-gradient(135deg, #7a3724, #b06d58)'
                        : '#9f2d22',
                    }}
                  >
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-bold text-[#322418] mb-0.5 line-clamp-1">{item.title_short || item.title}</h3>
                    <p className="text-[11px] text-[#8a6b4a] line-clamp-1">
                      {item.heat_level_text || '热门'} · {item.nickname}
                      {item.is_featured ? ' · 加精' : ''}
                    </p>
                  </div>
                  <span className="text-[#a8713c] text-xl shrink-0">›</span>
                </GlassCard>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── 搜索栏 ── */}
      <div className="relative mb-3.5">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-muted" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索标题/正文"
          className="w-full h-10 rounded-full pl-[38px] pr-[18px] bg-parchment border border-[#ead7c0] text-sm text-ink outline-none box-border focus:border-cinnabar-200/60 focus:ring-2 focus:ring-cinnabar-800/10 transition-colors font-sans"
        />
      </div>

      {/* ── 排序 + 收藏筛选 ── */}
      <div className="flex items-center gap-2 mb-3.5">
        <button
          type="button"
          onClick={() => setSort('hot')}
          className={`text-xs font-semibold px-3.5 py-1.5 rounded-full transition-all font-sans ${
            sort === 'hot'
              ? 'bg-[#9f2d22] text-white'
              : 'bg-parchment text-ink-muted'
          }`}
        >
          最热
        </button>
        <button
          type="button"
          onClick={() => setSort('new')}
          className={`text-xs font-semibold px-3.5 py-1.5 rounded-full transition-all font-sans ${
            sort === 'new'
              ? 'bg-[#9f2d22] text-white'
              : 'bg-parchment text-ink-muted'
          }`}
        >
          最新
        </button>
        <button
          type="button"
          onClick={() => setFavoriteOnly(!favoriteOnly)}
          className={`text-xs font-semibold px-3.5 py-1.5 rounded-full transition-all font-sans ${
            favoriteOnly
              ? 'bg-[#9f2d22] text-white'
              : 'bg-parchment text-ink-muted'
          }`}
        >
          我的收藏
        </button>
      </div>

      {/* ── 标签筛选 ── */}
      <div className="flex gap-2 overflow-auto pb-2 mb-3.5 whitespace-nowrap">
        {TAG_FILTERS.map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => setActiveTag(activeTag === tag ? '' : tag)}
            className={`chip !min-h-0 !py-1 !px-3 text-[11px] shrink-0 transition-all ${
              activeTag === tag ? 'chip-active' : ''
            }`}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* ── 发帖按钮（FAB） ── */}
      <button
        type="button"
        onClick={() => navigate('/discussion/create')}
        className="fixed right-5 bottom-28 z-50 w-14 h-14 rounded-full flex flex-col items-center justify-center border-none cursor-pointer guofeng-press"
        style={{
          background: 'linear-gradient(135deg, #7a2f25, #b74f3b)',
          boxShadow: '0 14px 30px rgba(126, 45, 35, 0.28)',
        }}
        aria-label="发帖"
      >
        <Plus size={24} className="text-white" />
        <span className="text-[9px] font-bold text-white -mt-0.5 tracking-wide">发帖</span>
      </button>

      {/* ── 加载状态 ── */}
      {isLoading ? (
        <div className="flex flex-col gap-3.5">
          {[1, 2, 3].map((i) => (
            <SkeletonLoader key={i} variant="card" className="!h-28" />
          ))}
        </div>
      ) : topics.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-full bg-parchment-dark flex items-center justify-center mb-4">
            <MessageCircle size={28} className="text-ink-muted opacity-40" />
          </div>
          <p className="text-ink-muted text-sm font-sans">还没有讨论内容</p>
          <p className="text-ink-muted text-xs mt-1 opacity-55 font-sans">
            快来发布第一条话题吧
          </p>
        </div>
      ) : (
        /* ── 话题列表 ── */
        <div className="rise-in-stagger flex flex-col gap-3">
          {topics.map((item, idx) => (
            <button
              key={item.id}
              type="button"
              onClick={() => navigate(`/discussion/${item.id}`)}
              className="card-interactive w-full text-left"
              style={{ animationDelay: `${0.08 + idx * 0.06}s` }}
            >
              <GlassCard hover className="p-4">
                {/* 封面图 */}
                {item.cover_url && (
                  <div className="mb-3 rounded-xl overflow-hidden h-[140px] bg-parchment-dark">
                    <CoverImage
                      coverUrl={item.cover_url}
                      alt={item.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>
                )}

                {/* 标题 + 热度 */}
                <div className="flex items-start gap-2.5 mb-2.5">
                  <h3 className="flex-1 font-serif text-[15px] font-bold text-ink mb-1.5 leading-snug line-clamp-2">
                    {item.title}
                  </h3>
                  <span className="shrink-0 chip !text-[11px] !min-h-0 !py-0.5 !px-2.5">
                    {item.heat_level_text || '普通'}
                  </span>
                </div>

                {/* 作者 + 时间 */}
                <p className="text-[11px] text-ink-muted mb-2 font-sans">
                  {item.nickname} · {item.created_at?.slice(0, 10)}
                  {item.is_featured ? ' · 加精' : ''}
                </p>

                {/* 标签 */}
                {item.tags && item.tags.length > 0 && (
                  <div className="flex gap-1.5 mb-2.5 flex-wrap">
                    {item.tags.slice(0, 3).map((t: string, i: number) => (
                      <span key={i} className="chip !text-[11px] !min-h-0 !py-0.5 !px-2.5">
                        #{t}
                      </span>
                    ))}
                  </div>
                )}

                {/* 内容预览 */}
                <p className="text-[13px] text-ink-secondary mb-2.5 leading-relaxed line-clamp-2 font-sans">
                  {item.content?.replace(/<[^>]*>/g, '').slice(0, 120)}
                </p>

                {/* 操作栏 */}
                <div className="flex items-center gap-3.5 text-[11px] text-ink-muted font-sans">
                  <span className="flex items-center gap-1">
                    <Heart size={11} /> {item.like_count || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <Bookmark size={11} /> {item.favorite_count || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageCircle size={11} /> {item.comment_count || 0}
                  </span>
                  <span className="ml-auto opacity-55 whitespace-nowrap">
                    {item.created_at?.slice(0, 10)}
                  </span>
                </div>
              </GlassCard>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
