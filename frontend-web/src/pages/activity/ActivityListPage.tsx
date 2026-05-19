import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Calendar, MapPin, Users } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { Activity } from '../../types';
import CoverImage from '../../components/ui/CoverImage';
import { GlassCard } from '../../components/ui/GlassCard';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

const monthOptions = ['all', 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] as const;

export default function ActivityListPage() {
  const navigate = useNavigate();
  const [monthFilter, setMonthFilter] = useState<string>('all');
  const { data, isLoading } = useQuery({
    queryKey: ['activities', monthFilter],
    queryFn: () => apiRequest<{ code: number; data: Activity[] }>(`/events/?status=`),
  });
  const activities = (data?.data || []) as Activity[];

  // 按月份筛选
  const filtered = useMemo(() => {
    if (monthFilter === 'all') return activities;
    return activities.filter(a => {
      if (!a.start_time) return false;
      const m = new Date(a.start_time).getMonth() + 1;
      return m === Number(monthFilter);
    });
  }, [activities, monthFilter]);

  // 推荐活动（取前2条）
  const recommended = filtered.slice(0, 2);

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
          <span className="inline-block px-3 py-1 rounded-full bg-white/12 text-[#ffe1bc] text-xs font-semibold mb-2.5 tracking-wide">
            活动日历中心
          </span>
          <h1 className="font-serif text-[26px] font-extrabold text-[#fff8f1] leading-tight mb-1">
            非遗体验活动
          </h1>
          <p className="text-sm text-white/85 font-sans">
            按月份筛选活动，快速定位你的时间窗口。
          </p>
        </div>

        {/* ── 月份筛选 ── */}
        <div className="flex gap-2 overflow-x-auto pb-2 mb-4 whitespace-nowrap scrollbar-hide">
          {monthOptions.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMonthFilter(String(m))}
              className={`chip shrink-0 transition-all ${
                monthFilter === String(m)
                  ? '!bg-[#9f2d22] !text-white'
                  : ''
              }`}
            >
              {m === 'all' ? '全年' : `${m}月`}
            </button>
          ))}
        </div>

        {/* ── 推荐活动 ── */}
        {recommended.length > 0 && (
          <div className="mb-4">
            <h2 className="text-base font-bold text-[#3a2619] mb-2.5">为你推荐的活动</h2>
            <div className="flex flex-col gap-2.5">
              {recommended.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => navigate(`/activity/${item.id}`)}
                  className="card-interactive w-full text-left bg-gradient-to-b from-[rgba(255,252,247,0.98)] to-[rgba(249,239,225,0.98)]"
                  style={{
                    background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
                  }}
                >
                  <GlassCard hover className="p-3.5 flex items-center gap-3">
                    {/* 封面缩略图 */}
                    <div className="w-[80px] h-[60px] rounded-lg overflow-hidden bg-parchment-dark shrink-0">
                      <CoverImage
                        coverUrl={item.cover_url}
                        alt={item.title}
                        className="w-full h-full object-cover"
                        loading="lazy"
                        fallback={<Calendar size={20} className="text-gold-500 opacity-40" />}
                      />
                    </div>
                    {/* 文字信息 */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-bold text-[#3d2719] mb-0.5 line-clamp-1">{item.title}</h3>
                      <p className="text-[11px] text-[#84674c] line-clamp-1">
                        {item.location || '地点待定'} · {item.status === 'open' ? '开放报名' : '已关闭'}
                      </p>
                    </div>
                    {/* 箭头 */}
                    <span className="text-[#a8713c] text-xl shrink-0">›</span>
                  </GlassCard>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ── 加载状态 ── */}
        {isLoading ? (
          <div className="flex flex-col gap-3.5">
            {[1, 2, 3].map(i => (
              <SkeletonLoader key={i} variant="card" className="!h-[180px]" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16 text-ink-muted text-sm">
            <Calendar size={32} className="mx-auto mb-3 opacity-25" />
            <p>当前月份暂无活动，试试切换到全年看看</p>
          </div>
        ) : (
          /* ── 活动列表 ── */
          <div className="flex flex-col gap-3.5">
            {filtered.map((item, idx) => (
              <GlassCard
                key={item.id}
                as="button"
                hover
                className="card-interactive p-0 overflow-hidden text-left"
                onClick={() => navigate(`/activity/${item.id}`)}
                style={{ animation: 'riseIn 0.44s ease-out both', animationDelay: `${0.1 + idx * 0.05}s` }}
              >
                {/* 封面图 */}
                <div className="relative h-[190px] bg-parchment-dark flex items-center justify-center">
                  <CoverImage
                    coverUrl={item.cover_url}
                    alt={item.title}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    fallback={<Calendar size={48} className="text-gold-500 opacity-25" />}
                  />
                  {/* 状态徽章 */}
                  <div className="absolute left-3 top-3 px-2.5 py-1 rounded-full bg-black/35 text-[#fff1de] text-[11px]">
                    {item.status === 'open' ? '报名中' : item.status === 'closed' ? '已关闭' : '已满'}
                  </div>
                </div>

                {/* 信息区域 */}
                <div className="p-4">
                  {/* 标题 + 状态 */}
                  <div className="flex items-center gap-2.5 mb-2.5">
                    <h3 className="flex-1 text-base font-extrabold text-[#342519] line-clamp-1">{item.title}</h3>
                    <span className={`shrink-0 px-2.5 py-1 rounded-full text-[11px] font-semibold ${
                      item.status === 'open'
                        ? 'bg-[#f8e4db] text-[#8d2b21]'
                        : 'bg-[#efe5d9] text-[#6e5a46]'
                    }`}>
                      {item.status === 'open' ? '报名中' : '已关闭'}
                    </span>
                  </div>

                  {/* 元信息标签 */}
                  <div className="flex flex-wrap gap-2 mb-2.5">
                    {item.start_time && (
                      <span className="chip !bg-[#f3e6d6] !text-[#8a6545] !min-h-0 !py-0.5 !px-2.5 !text-[11px]">
                        {new Date(item.start_time).getMonth() + 1}月
                      </span>
                    )}
                    {item.max_participants && (
                      <span className="chip !bg-[#f3e6d6] !text-[#8a6545] !min-h-0 !py-0.5 !px-2.5 !text-[11px]">
                        限{item.max_participants}人
                      </span>
                    )}
                  </div>

                  {/* 地点 */}
                  <p className="text-[13px] text-[#73583d] leading-relaxed mb-3">
                    地点：{item.location || '待定'}
                  </p>

                  {/* 报名按钮 */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/activity/${item.id}`);
                    }}
                    className="w-full py-2 rounded-full text-sm font-semibold text-white guofeng-press"
                    style={{
                      background: 'linear-gradient(135deg, #9f2d22, #c04833)',
                    }}
                  >
                    立即报名
                  </button>
                </div>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    );
  }
