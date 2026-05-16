import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Settings, MapPin, Clock, BookOpen, LogOut, ChevronRight, ChevronDown, ChevronUp,
  Sparkles, BarChart3, Heart, Eye, MessageCircle, Calendar, MessageSquare, TrendingUp,
} from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { useChatStore } from '../../stores/chat-store';
import { User as UserType } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';
import { SealBadge } from '../../components/ui/SealBadge';
import { SkeletonLoader } from '../../components/ui/SkeletonLoader';

/* ──────────────────────────────────────────
   类型定义
   ────────────────────────────────────────── */

interface RecommendProfileData {
  portrait: {
    heritage_terms: string[];
    scene_terms: string[];
    region_terms: string[];
    sources: string[];
    summary_text: string;
  };
  radar: {
    dimensions: { name: string; value: number }[];
    top_keywords: string[];
  };
  feedback: Record<string, number>;
  action_breakdown: Record<string, number>;
  activity: {
    qa_count: number;
    registration_count: number;
    topic_count: number;
    comment_count: number;
    favorite_count: number;
    like_count: number;
  };
}

interface RegistrationItem {
  registration_id: number;
  activity_id: number;
  activity_title: string;
  status: string;
  remark: string | null;
  created_at: string;
}

interface RegistrationListData {
  items: RegistrationItem[];
  total: number;
}

interface DiscussionTopicItem {
  id: number;
  user_id: number;
  title: string;
  comment_count: number;
  created_at: string;
}

interface DiscussionListData {
  items: DiscussionTopicItem[];
  total: number;
}

/* ──────────────────────────────────────────
   辅助函数
   ────────────────────────────────────────── */

type ConfidenceLabel = '已懂你' | '了解中' | '初识';

function getConfidenceInfo(confidence: number): {
  label: ConfidenceLabel;
  barGradient: string;
} {
  if (confidence > 70) {
    return {
      label: '已懂你',
      barGradient: 'bg-gradient-to-r from-jade-500 to-jade-200',
    };
  }
  if (confidence > 30) {
    return {
      label: '了解中',
      barGradient: 'bg-gradient-to-r from-indigo-500 to-indigo-500/60',
    };
  }
  return {
    label: '初识',
    barGradient: 'bg-gradient-to-r from-gold-400 to-gold-200',
  };
}

function getModeLabel(mode: string): string {
  switch (mode) {
    case 'precision':
      return '精准推荐';
    case 'mixed':
      return '混合模式';
    case 'cold_start':
    default:
      return '冷启动';
  }
}

function normalizePercent(value: number | undefined): number {
  if (value === undefined || value === null) return 0;
  return Math.round(Math.min(100, Math.max(0, Number(value) || 0)));
}

/* ──────────────────────────────────────────
   SignalCard 子组件
   ────────────────────────────────────────── */

interface SignalCardProps {
  icon: React.ElementType;
  title: string;
  briefValue: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function SignalCard({
  icon: Icon,
  title,
  briefValue,
  expanded,
  onToggle,
  children,
}: SignalCardProps) {
  return (
    <div className="border-b border-gold-200/20 last:border-b-0">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 bg-transparent cursor-pointer text-left transition-colors hover:bg-gold-50/30"
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-brand-soft shrink-0">
            <Icon size={17} className="text-brand" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-ink m-0 font-sans">{title}</p>
            <p className="text-xs text-ink-muted m-0 mt-0.5 truncate">{briefValue}</p>
          </div>
        </div>
        <span className="shrink-0 ml-3 text-ink-muted/60">
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </span>
      </button>

      {expanded && (
        <div className="px-5 pb-4 pt-1">
          {children}
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────
   StatCard 子组件
   ────────────────────────────────────────── */

const STAT_COLORS = [
  'text-cinnabar-600',
  'text-brand',
  'text-jade-600',
  'text-gold-600',
];

const STAT_ICONS = [Eye, TrendingUp, BookOpen, Calendar];

function StatCard({
  label,
  value,
  index,
  loading,
}: {
  label: string;
  value: string | number;
  index: number;
  loading?: boolean;
}) {
  const Icon = STAT_ICONS[index] || TrendingUp;
  return (
    <GlassCard className="!p-4 text-center !rounded-[28px]">
      {loading ? (
        <div className="flex flex-col items-center gap-2">
          <SkeletonLoader variant="text" className="!h-6 !w-12" />
          <SkeletonLoader variant="text" className="!h-3 !w-10" />
        </div>
      ) : (
        <>
          <div className="flex items-center justify-center gap-1.5 mb-1">
            <Icon size={14} className={STAT_COLORS[index]} />
            <p className={`text-[22px] font-extrabold m-0 leading-none font-serif ${STAT_COLORS[index]}`}>
              {value}
            </p>
          </div>
          <p className="text-xs text-ink-muted mt-1">{label}</p>
        </>
      )}
    </GlassCard>
  );
}

/* ──────────────────────────────────────────
   主页面组件
   ────────────────────────────────────────── */

export default function ProfilePage() {
  const navigate = useNavigate();
  const { session, logout } = useAuthStore();
  const crsState = useChatStore((s) => s.crsState);
  const userId = session?.userId;

  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());

  const toggleCard = (id: number) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  /* ── API 查询 ── */

  const { data: userData, isLoading: userLoading } = useQuery({
    queryKey: ['user-profile', userId],
    queryFn: () => apiRequest<{ code: number; data: UserType }>(`/users/${userId}`),
    enabled: !!userId,
  });
  const user = userData?.data;

  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: ['recommend-profile', userId],
    queryFn: () =>
      apiRequest<{ code: number; data: RecommendProfileData }>(
        `/users/${userId}/recommend-profile`,
      ),
    enabled: !!userId,
  });
  const profile = profileData?.data;

  const { data: topicsData } = useQuery({
    queryKey: ['user-topics', userId],
    queryFn: () =>
      apiRequest<{ code: number; data: DiscussionListData }>(
        `/discussion/topics?user_id=${userId}`,
      ),
    enabled: !!userId,
  });

  const { data: registrationsData } = useQuery({
    queryKey: ['user-registrations', userId],
    queryFn: () =>
      apiRequest<{ code: number; data: RegistrationListData }>(
        `/users/${userId}/registrations`,
      ),
    enabled: !!userId,
  });

  /* ── 衍生数据 ── */

  const confidence = useMemo(() => {
    const us = user?.confidence_score;
    if (us !== undefined && us !== null) return Math.round(Number(us));
    const ps = profile?.activity?.qa_count;
    return ps ? Math.min(100, ps * 15) : 0;
  }, [user, profile]);

  const { label: confidenceLabel, barGradient: confidenceBarColor } =
    getConfidenceInfo(confidence);

  const crsMode = (crsState.mode as string) || 'cold_start';
  const modeLabel = getModeLabel(crsMode);

  const dims = useMemo(() => crsState.dimensions || {}, [crsState.dimensions]);

  const stats = useMemo(() => {
    const ab = profile?.action_breakdown;
    const ac = profile?.activity;
    return {
      views:
        (ab?.['content_view'] || 0) +
        (ab?.['content_click'] || 0) +
        (ab?.['event_view'] || 0),
      favorites: ac?.favorite_count || 0,
      posts: ac?.topic_count || 0,
      registrations: ac?.registration_count || 0,
    };
  }, [profile]);

  const userTopics = useMemo(() => {
    const raw = topicsData?.data?.items || [];
    return raw.filter((t) => t.user_id === userId).slice(0, 5);
  }, [topicsData, userId]);

  const registrations = useMemo(() => {
    const raw = registrationsData?.data?.items || [];
    return raw.slice(0, 5);
  }, [registrationsData]);

  const heritageCategories = useMemo(() => {
    const portrait = profile?.portrait?.heritage_terms;
    if (portrait && portrait.length) return portrait;
    const raw = user?.preferred_heritage_types;
    if (!raw) return [] as string[];
    if (Array.isArray(raw)) return raw as string[];
    try {
      const parsed = JSON.parse(String(raw));
      return Array.isArray(parsed) ? parsed : [String(raw)];
    } catch {
      return [String(raw)];
    }
  }, [profile, user]);

  const expPercent = normalizePercent(dims['explicit']);
  const impPercent = normalizePercent(dims['implicit']);
  const diaPercent = normalizePercent(dims['dialogue']);

  /* ── 菜单项 ── */

  const menuItems = useMemo(
    () => [
      { icon: Settings, label: '偏好设置', path: '/preferences' },
      { icon: Clock, label: '浏览历史', path: '/history' },
      { icon: BookOpen, label: '我的收藏', path: '/history?tab=favorites' },
    ],
    [],
  );

  const allLoading = userLoading && profileLoading;

  /* ── 渲染 ── */

  return (
    <div className="px-6 pb-9 pt-0 space-y-[18px]">

      {/* ═══ Hero Banner — 用户信息头部 ═══ */}
      <div className="relative overflow-hidden rounded-[30px] bg-gradient-to-br from-[#2a1611] via-cinnabar-700 to-gold-400 p-7 mt-4">
        {/* 背景装饰 */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

        <div className="relative z-10 flex items-center gap-4">
          {/* 头像 — CSS 绘制 */}
          <div className="relative w-[50px] h-[50px] shrink-0">
            <div className="absolute left-1 top-1 w-[42px] h-[42px] rounded-full bg-gradient-to-b from-[#ede1ff] via-[#cfb6ff] to-[#b38af0]">
              {/* 头发 */}
              <div className="absolute -top-1.5 left-1 w-[34px] h-[18px] bg-[#2d2344] rounded-full" />
              {/* 脸 */}
              <div className="absolute top-2.5 left-2.5 w-[22px] h-[18px] rounded-[45%] bg-[#fff3f7] shadow-[0_2px_0_rgba(93,66,132,0.06)]">
                {/* 左眼 */}
                <div className="absolute top-1 left-[3px] w-1.5 h-2.5 rounded-full bg-gradient-to-b from-[#9f71ff] to-[#5a3ab5]" />
                {/* 右眼 */}
                <div className="absolute top-1 right-[3px] w-1.5 h-2.5 rounded-full bg-gradient-to-b from-[#9f71ff] to-[#5a3ab5]" />
                {/* 嘴 */}
                <div className="absolute bottom-[3px] left-[9px] w-1 h-0.5 rounded-full bg-[#8f6b86]" />
              </div>
            </div>
          </div>

          <div className="min-w-0">
            <h2 className="text-xl font-bold text-[#fff8ef] m-0 truncate font-serif">
              {user?.nickname || session?.nickname || '用户'}
            </h2>
            <p className="text-[13px] text-white/70 mt-1">
              @{user?.username || session?.username || '---'}
            </p>
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              {user?.role && user.role !== 'user' && (
                <SealBadge variant="gold">{user.role}</SealBadge>
              )}
              <SealBadge variant={crsMode === 'precision' ? 'jade' : crsMode === 'mixed' ? 'gold' : 'cinnabar'}>
                {modeLabel}
              </SealBadge>
            </div>
          </div>
        </div>

        {/* CRS 置信度条 */}
        <div className="relative z-10 mt-4 pt-3.5 border-t border-white/15">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[13px] text-white/80 font-semibold inline-flex items-center gap-1">
              <Sparkles size={12} className="text-gold-200" />
              {confidenceLabel}
            </span>
            <span className="text-[15px] font-extrabold text-white font-serif">
              {confidence}%
            </span>
          </div>
          <div className="mt-1.5 h-2.5 rounded-full bg-black/15 overflow-hidden">
            <div
              className={`h-full rounded-full transition-[width] duration-600 ease-out ${confidenceBarColor}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
        </div>
      </div>

      {/* ═══ 统计数据行（P0.3） ═══ */}
      <div className="grid grid-cols-4 gap-2.5">
        {[
          { label: '浏览数', value: stats.views },
          { label: '收藏数', value: stats.favorites },
          { label: '发帖数', value: stats.posts },
          { label: '活动报名', value: stats.registrations },
        ].map((stat, i) => (
          <StatCard
            key={stat.label}
            label={stat.label}
            value={allLoading ? '-' : stat.value}
            index={i}
            loading={allLoading}
          />
        ))}
      </div>

      {/* ═══ Behavior Signal Panel — 6维信号面板（P0.2） ═══ */}
      <GlassCard className="!p-0 overflow-hidden">
        {/* 面板标题 */}
        <div className="px-5 py-4 border-b border-gold-200/20">
          <h3 className="text-base font-bold text-ink m-0 font-serif flex items-center gap-2">
            <BarChart3 size={18} className="text-brand" />
            用户画像信号
          </h3>
          <p className="text-xs text-ink-muted mt-0.5 m-0">
            基于你的偏好、行为与对话，系统综合分析
          </p>
        </div>

        <div className="rise-in-stagger">
          {/* 1. 兴趣偏好 */}
          <SignalCard
            icon={Heart}
            title="兴趣偏好"
            briefValue={
              heritageCategories.length
                ? heritageCategories.slice(0, 3).join('、')
                : '暂无偏好数据'
            }
            expanded={expandedCards.has(1)}
            onToggle={() => toggleCard(1)}
          >
            {heritageCategories.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {heritageCategories.map((cat, i) => {
                  const chipColors = [
                    'bg-cinnabar-100 text-cinnabar-700 border-cinnabar-200',
                    'bg-jade-100 text-jade-700 border-jade-200',
                    'bg-gold-100 text-gold-700 border-gold-200',
                    'bg-indigo-100 text-indigo-600 border-indigo-200',
                  ];
                  const color = chipColors[i % chipColors.length];
                  return (
                    <span
                      key={cat}
                      className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium border ${color}`}
                    >
                      {cat}
                    </span>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-ink-muted m-0">
                完成偏好设置后，这里将展示你感兴趣的非遗类目
              </p>
            )}
          </SignalCard>

          {/* 2. 浏览记录 */}
          <SignalCard
            icon={Eye}
            title="浏览记录"
            briefValue={`近期浏览 ${stats.views} 次`}
            expanded={expandedCards.has(2)}
            onToggle={() => toggleCard(2)}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-secondary font-sans">
                  累计浏览次数
                </span>
                <span className="text-lg font-bold text-cinnabar-600 font-serif">
                  {stats.views}
                </span>
              </div>
              <InkButton
                variant="outline"
                size="sm"
                onClick={() => navigate('/history')}
                className="!w-full !text-xs"
              >
                查看浏览历史 <ChevronRight size={14} />
              </InkButton>
            </div>
          </SignalCard>

          {/* 3. AI 对话 */}
          <SignalCard
            icon={MessageCircle}
            title="AI 对话"
            briefValue={`已对话 ${profile?.activity?.qa_count || 0} 次 · 置信度 ${confidence}%`}
            expanded={expandedCards.has(3)}
            onToggle={() => toggleCard(3)}
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-secondary font-sans">
                  对话轮次
                </span>
                <span className="text-lg font-bold text-indigo-600 font-serif">
                  {profile?.activity?.qa_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-secondary font-sans">
                  综合置信度
                </span>
                <span className="text-lg font-bold text-jade-600 font-serif">
                  {confidence}%
                </span>
              </div>
              <div className="h-2 rounded-full bg-parchment-dark overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-jade-400 transition-[width] duration-500"
                  style={{ width: `${confidence}%` }}
                />
              </div>
              <InkButton
                variant="outline"
                size="sm"
                onClick={() => navigate('/ai')}
                className="!w-full !text-xs"
              >
                与黑塔对话 <Sparkles size={14} />
              </InkButton>
            </div>
          </SignalCard>

          {/* 4. 活动报名 */}
          <SignalCard
            icon={Calendar}
            title="活动报名"
            briefValue={`已报名 ${stats.registrations} 场活动`}
            expanded={expandedCards.has(4)}
            onToggle={() => toggleCard(4)}
          >
            {registrations.length > 0 ? (
              <div className="space-y-2">
                {registrations.map((reg) => (
                  <div
                    key={reg.registration_id}
                    className="flex items-center justify-between py-2 px-3 rounded-xl bg-parchment"
                  >
                    <span className="text-sm text-ink-secondary font-sans truncate flex-1 mr-2">
                      {reg.activity_title}
                    </span>
                    <SealBadge
                      variant={
                        reg.status === 'registered'
                          ? 'jade'
                          : reg.status === 'checked_in'
                            ? 'gold'
                            : 'cinnabar'
                      }
                    >
                      {reg.status === 'registered'
                        ? '已报名'
                        : reg.status === 'checked_in'
                          ? '已签到'
                          : reg.status === 'completed'
                            ? '已完成'
                            : reg.status}
                    </SealBadge>
                  </div>
                ))}
                <InkButton
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/places')}
                  className="!w-full !text-xs mt-2"
                >
                  浏览更多活动 <MapPin size={14} />
                </InkButton>
              </div>
            ) : (
              <div className="text-center py-2">
                <p className="text-sm text-ink-muted m-0">暂无活动报名记录</p>
                <InkButton
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/places')}
                  className="!mt-2 !text-xs"
                >
                  发现活动
                </InkButton>
              </div>
            )}
          </SignalCard>

          {/* 5. 社区互动 */}
          <SignalCard
            icon={MessageSquare}
            title="社区互动"
            briefValue={`发布 ${stats.posts} 帖 · ${profile?.activity?.comment_count || 0} 评论`}
            expanded={expandedCards.has(5)}
            onToggle={() => toggleCard(5)}
          >
            {userTopics.length > 0 ? (
              <div className="space-y-2">
                {userTopics.map((topic) => (
                  <div
                    key={topic.id}
                    className="flex items-center justify-between py-2 px-3 rounded-xl bg-parchment"
                  >
                    <span className="text-sm text-ink-secondary font-sans truncate flex-1 mr-2">
                      {topic.title}
                    </span>
                    <span className="text-xs text-ink-muted shrink-0">
                      {topic.comment_count || 0} 评论
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-2">
                <p className="text-sm text-ink-muted m-0">暂无发帖记录</p>
                <p className="text-xs text-ink-muted/70 mt-1 m-0">
                  去社区分享你的非遗见解
                </p>
              </div>
            )}
          </SignalCard>

          {/* 6. 综合兴趣画像 */}
          <SignalCard
            icon={Sparkles}
            title="综合兴趣画像"
            briefValue={`显式${expPercent}% · 隐式${impPercent}% · 对话${diaPercent}%`}
            expanded={expandedCards.has(6)}
            onToggle={() => toggleCard(6)}
          >
            <div className="space-y-4">
              {/* 维度一：显式 (主动选择) */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-ink-secondary font-sans">
                    你的选择
                  </span>
                  <span className="text-xs font-bold text-gold-600 font-sans">
                    {expPercent}%
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-parchment-dark overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-gold-300 to-gold-500 transition-[width] duration-500"
                    style={{ width: `${expPercent}%` }}
                  />
                </div>
                <p className="text-[11px] text-ink-muted/70 mt-1 m-0">
                  基于你主动填写的偏好设置
                </p>
              </div>

              {/* 维度二：隐式 (浏览行为) */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-ink-secondary font-sans">
                    你的行为
                  </span>
                  <span className="text-xs font-bold text-indigo-600 font-sans">
                    {impPercent}%
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-parchment-dark overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-indigo-600 transition-[width] duration-500"
                    style={{ width: `${impPercent}%` }}
                  />
                </div>
                <p className="text-[11px] text-ink-muted/70 mt-1 m-0">
                  基于你的浏览与收藏行为
                </p>
              </div>

              {/* 维度三：对话 (对话偏好) */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-ink-secondary font-sans">
                    你的对话
                  </span>
                  <span className="text-xs font-bold text-cinnabar-600 font-sans">
                    {diaPercent}%
                  </span>
                </div>
                <div className="h-2.5 rounded-full bg-parchment-dark overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cinnabar-400 to-cinnabar-600 transition-[width] duration-500"
                    style={{ width: `${diaPercent}%` }}
                  />
                </div>
                <p className="text-[11px] text-ink-muted/70 mt-1 m-0">
                  基于你与AI的对话内容分析
                </p>
              </div>
            </div>
          </SignalCard>
        </div>
      </GlassCard>

      {/* ═══ 置信维度条（P0.2） ═══ */}
      <GlassCard>
        <h3 className="text-sm font-bold text-ink m-0 mb-4 font-serif">
          置信维度
        </h3>

        <div className="space-y-4">
          {/* 显式 — 橙色 */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[13px] text-ink-secondary font-sans">
                主动选择
              </span>
              <span className="text-sm font-extrabold text-gold-500 font-serif">
                {expPercent}%
              </span>
            </div>
            <div className="h-2 rounded-full bg-parchment-dark overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-gold-300 to-gold-500 transition-[width] duration-500"
                style={{ width: `${expPercent}%` }}
              />
            </div>
          </div>

          {/* 隐式 — 紫色 */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[13px] text-ink-secondary font-sans">
                浏览行为
              </span>
              <span className="text-sm font-extrabold text-indigo-600 font-serif">
                {impPercent}%
              </span>
            </div>
            <div className="h-2 rounded-full bg-parchment-dark overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-indigo-600 transition-[width] duration-500"
                style={{ width: `${impPercent}%` }}
              />
            </div>
          </div>

          {/* 对话 — 红色 */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[13px] text-ink-secondary font-sans">
                对话偏好
              </span>
              <span className="text-sm font-extrabold text-cinnabar-600 font-serif">
                {diaPercent}%
              </span>
            </div>
            <div className="h-2 rounded-full bg-parchment-dark overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cinnabar-400 to-cinnabar-600 transition-[width] duration-500"
                style={{ width: `${diaPercent}%` }}
              />
            </div>
          </div>
        </div>

        {expPercent === 0 && impPercent === 0 && diaPercent === 0 && (
          <p className="text-xs text-ink-muted text-center mt-4 m-0">
            与AI对话后，系统将逐步构建你的兴趣画像
          </p>
        )}
      </GlassCard>

      {/* ═══ 菜单列表 ═══ */}
      <GlassCard className="!p-0 overflow-hidden">
        {menuItems.map((item, i) => {
          const Icon = item.icon;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center justify-between px-6 py-[18px] bg-transparent cursor-pointer text-ink-secondary text-sm transition-colors hover:bg-ink/4 ${
                i < menuItems.length - 1
                  ? 'border-b border-gold-200/20'
                  : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon size={18} className="text-brand" />
                <span className="font-medium font-sans">{item.label}</span>
              </div>
              <ChevronRight size={16} className="text-ink-muted/60" />
            </button>
          );
        })}
      </GlassCard>

      {/* ═══ 退出登录 ═══ */}
      <InkButton
        variant="outline"
        size="lg"
        onClick={() => {
          logout();
          navigate('/login', { replace: true });
        }}
        className="!w-full"
      >
        <LogOut size={16} /> 退出登录
      </InkButton>
    </div>
  );
}
