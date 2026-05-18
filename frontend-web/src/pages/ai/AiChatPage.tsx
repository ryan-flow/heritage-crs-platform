import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Trash2, Sparkles, Volume2, VolumeX, ArrowLeft, ChevronRight, ChevronDown, ChevronUp, BookOpen, Calendar } from 'lucide-react';
import { apiRequest, shortenReason } from '../../lib/api';
import CoverImage from '../../components/ui/CoverImage';
import { useAuthStore } from '../../stores/auth-store';
import { useChatStore } from '../../stores/chat-store';
import { AiChatResponse, RecommendCard, CrsAnswerResponse, ActionTask } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';

/* ================================================================
   AI Chat Page — fully featured, matching mini-program layout
   ================================================================ */

const CRS_MODE_QUESTIONS: Record<string, string[]> = {
  cold_start: ['第一次接触非遗，从哪类开始比较容易上手？', '传统工艺类和戏曲音乐类，哪个更适合零基础体验？', '有什么适合周末去现场感受的非遗活动？', '中国有多少项非遗被列入了联合国名录？', '皮影戏、木偶戏、布袋戏，这些有什么不同？', '二十四节气除了指导农事，还有什么文化意义？', '非遗和普通手艺最大的区别在哪里？', '想带小朋友了解非遗，从哪个方向切入比较好？', '非遗传承人是怎么培养出来的？', '非遗和乡村振兴是怎么结合的？', '现在最热门的非遗体验活动有哪些？', '想系统地了解一个非遗类别，推荐什么顺序？'],
  mixed: ['云锦和苏绣，哪种工艺更值得深入看？', '古琴和古筝在听感上有什么本质区别？', '京剧和昆曲的表演风格差异在哪？', '端午节在不同地区有什么不同的庆祝方式？', '非遗传承中活态传承是什么意思？', '有没有适合自己动手体验的非遗项目？', '中医里的经络理论和非遗有什么关系？', '如果想系统地了解一个非遗类别，推荐什么顺序？', '花灯制作属于哪一类非遗？入门难度如何？', '非遗进校园活动一般会包含哪些内容？', '非遗和乡村振兴是怎么结合的？', '现在最热门的非遗体验活动有哪些？'],
  precision: ['景德镇的柴窑和气窑烧出来的瓷器差别在哪？', '侗族大歌的演唱技巧为什么很难用乐谱记录？', '蜀锦的挑花结本工艺具体是怎么操作的？', '中医针灸和艾灸在传承路线上有什么不同？', '皮影戏的雕刻刀法对最终演出效果有多大影响？', '非遗文创产品为什么经常被说不夠原汁原味？', '有哪些冷门但非常值得了解的非遗项目？', '非遗保护中的生产性保护是什么概念？', '如何判断一场非遗演出的质量好不好？', '数字化技术对非遗保护带来了什么改变？'],
};

const KEYWORD_FOLLOWUP_MAP: { keyword: string; questions: string[] }[] = [
  { keyword: '皮影', questions: ['皮影戏适合从哪些代表作品入门？', '现在哪里还能看到皮影戏现场表演？', '皮影戏和木偶戏有什么区别？', '如果想现场体验皮影戏，先看什么最容易入门？'] },
  { keyword: '昆曲', questions: ['昆曲适合先听哪几段经典唱段？', '第一次看昆曲演出，最值得注意什么？', '昆曲和京剧在观演体验上有什么差别？', '如果想线下体验昆曲，应该优先选讲座还是演出？'] },
  { keyword: '云锦', questions: ['云锦最值得先了解的工艺步骤是什么？', '云锦和普通织锦最大的区别在哪里？', '看云锦时怎样才算看懂门道？', '如果想深入了解云锦，可以先看内容还是先看展览？'] },
  { keyword: '古琴', questions: ['古琴适合从哪些代表曲目开始听？', '古琴为什么会给人特别静心的感觉？', '古琴和古筝在听感上有什么差别？', '如果想体验古琴，先听讲解还是先听完整曲子更合适？'] },
  { keyword: '端午', questions: ['除了吃粽子，端午还有哪些核心习俗值得了解？', '端午背后的文化象征可以怎么理解？', '端午习俗为什么会因地区不同而变化？', '如果想做端午主题活动，适合先选哪类体验项目？'] },
  { keyword: '书法', questions: ['书法作为非遗，最适合从哪种字体开始认识？', '书法欣赏时可以先看哪些基本线索？', '书法为什么也被纳入非遗保护？', '如果是初学者，先看名作还是先了解工具更合适？'] },
  { keyword: '苏绣', questions: ['苏绣和湘绣最大的风格差异在哪？', '苏绣的双面绣工艺为什么被认为是最难的？', '想近距离看苏绣作品，推荐去哪里？', '苏绣入门可以从哪些小件绣品开始了解？'] },
  { keyword: '京剧', questions: ['京剧脸谱的颜色分别代表什么含义？', '京剧的四大行当分别有什么特点？', '第一次看京剧，选哪出戏最容易看进去？', '京剧的唱腔体系和其他戏曲有什么不同？'] },
  { keyword: '中医', questions: ['中医针灸为什么能入选联合国非遗名录？', '中医的望闻问切和现代医学诊断有什么互补？', '有没有适合普通人体验的中医养生方法？', '中药材炮制工艺本身也是非遗吗？'] },
  { keyword: '剪纸', questions: ['剪纸艺术为什么能流传这么久？', '中国南北方剪纸风格有什么明显不同？', '想学剪纸，从什么基本技法开始练？', '剪纸在现代设计中是怎么被应用的？'] },
  { keyword: '陶瓷', questions: ['景德镇为什么被称为瓷都？', '青花瓷的制作流程包含哪些关键步骤？', '古代陶瓷工艺是怎么传承到今天的？', '现代陶艺和传统制瓷工艺最大的区别是什么？'] },
  { keyword: '太极', questions: ['太极拳作为非遗有什么特别的文化价值？', '太极拳的不同流派之间差异大吗？', '太极的养生效果从现代科学角度怎么解释？', '学太极拳零基础可以从哪里开始？'] },
  { keyword: '非遗', questions: ['非遗和普通传统文化项目有什么区别？', '中国目前有多少项世界级非遗？', '非遗传承人需要满足什么条件？', '为什么非遗保护越来越受到重视？'] },
];

const COLD_START_CATEGORIES: Record<string, string[]> = {
  '传统工艺': ['青花瓷是怎么制作的？', '苏绣和湘绣有什么区别？', '木雕工艺有哪些流派？'],
  '戏曲音乐': ['京剧和昆曲有什么不同？', '古琴有几根弦？', '什么是南音？'],
  '民俗节俗': ['端午节有哪些非遗习俗？', '二十四节气是怎么来的？', '庙会文化有哪些特色？'],
  '饮食医药': ['中药炮制有哪些讲究？', '茶道和茶艺有什么区别？', '针灸的原理是什么？'],
};

const MODE_HERO_TITLES: Record<string, string> = {
  cold_start: '想认识你',
  mixed: '正在了解你',
  precision: '已懂你，精准推荐',
};

const MODE_LABELS: Record<string, string> = { cold_start: '初识', mixed: '探索', precision: '精准' };

export default function AiChatPage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const store = useChatStore();

  const [input, setInput] = useState('');
  const [waitingTip, setWaitingTip] = useState('');
  const [sourceTag, setSourceTag] = useState('');
  const [presets, setPresets] = useState<{ text: string; display: string }[]>([]);
  const [presetQueue, setPresetQueue] = useState<string[]>([]);
  const [recentPresets, setRecentPresets] = useState<string[]>([]);
  const [crsExpanded, setCrsExpanded] = useState(false);
  const [crsTimeline, setCrsTimeline] = useState<{ ask_id: string; question_text: string; answer?: string; score_delta?: number }[]>([]);
  const [modeCelebrating, setModeCelebrating] = useState(false);
  const [celebrationMode, setCelebrationMode] = useState('');
  const [speaking, setSpeaking] = useState(false);
  const [typingText, setTypingText] = useState('');
  const [explainExpanded, setExplainExpanded] = useState<Record<number, boolean>>({});
  const [feedbackGiven, setFeedbackGiven] = useState<Record<string, string>>({});
  const [overallFeedback, setOverallFeedback] = useState('');
  const [rewriteSuggestions, setRewriteSuggestions] = useState<string[]>([]);
  const [actionTasks, setActionTasks] = useState<ActionTask[]>([]);
  const [kgEntity, setKgEntity] = useState('');
  const [kgPathText, setKgPathText] = useState('');
  const [kgSimilarNames, setKgSimilarNames] = useState<string[]>([]);
  const [kgExpandItems, setKgExpandItems] = useState<{ entity: string }[]>([]);
  const [celebrationParticles, setCelebrationParticles] = useState<{ id: number; x: number; y: number; color: string }[]>([]);

  const bottomRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const typingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const scrollToBottom = () => bottomRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => { scrollToBottom(); }, [store.messages]);
  useEffect(() => { loadCrsState(); generatePresets(); return () => { if (typingTimerRef.current) clearInterval(typingTimerRef.current); }; }, []);

  // Typewriter effect
  const startTyping = (text: string) => {
    if (typingTimerRef.current) clearInterval(typingTimerRef.current);
    setTypingText('');
    let i = 0;
    typingTimerRef.current = setInterval(() => {
      i++;
      setTypingText(text.slice(0, i));
      if (i >= text.length && typingTimerRef.current) {
        clearInterval(typingTimerRef.current);
        typingTimerRef.current = null;
      }
    }, 30);
  };

  const loadCrsState = async () => {
    if (!session?.userId) return;
    try {
      const res = await apiRequest<{ code: number; data: Record<string, unknown> }>(`/ai/crs/state?user_id=${session.userId}`);
      const data = res.data || {};
      const mode = (data.mode as string) || 'cold_start';
      store.setCrsState({ mode, confidence_score: data.confidence_score as number || 0, session_id: data.session_id as string });
      if (data.ask_timeline) setCrsTimeline(data.ask_timeline as typeof crsTimeline);
      if (mode === 'cold_start' && !store.messages.length && !(data.turn_count as number)) {
        store.setAsk('你最想了解哪类非物质文化遗产？', ['传统工艺', '戏曲音乐', '民俗节俗', '饮食医药'], 'A01');
      }
    } catch {}
  };

  const handleTTS = async (text: string) => {
    if (speaking) { if (audioRef.current) { audioRef.current.pause(); } setSpeaking(false); return; }
    setSpeaking(true);
    try {
      const res = await apiRequest<{ code: number; data: { audio_url: string } }>('/ai/tts', { method: 'POST', data: { text }, timeout: 15000 });
      const url = res.data?.audio_url;
      if (url) {
        const full = url.startsWith('http') ? url : `${import.meta.env.VITE_API_BASE?.replace('/api/v1', '') || ''}${url}`;
        if (!audioRef.current) audioRef.current = new Audio();
        audioRef.current.src = full;
        audioRef.current.onended = () => setSpeaking(false);
        await audioRef.current.play();
      } else { setSpeaking(false); }
    } catch { setSpeaking(false); }
  };

  const handleSend = async (overrideText?: string) => {
    const q = (overrideText || input).trim();
    if (!q || store.sending) return;
    store.addMessage({ id: 'u' + Date.now(), role: 'user', text: q });
    setInput(''); store.setSending(true); setWaitingTip('黑塔正在思考...'); setSourceTag(''); store.clearAsk();
    const prevCards = store.recommendCards;
    try {
      const res = await apiRequest<{ code: number; data: AiChatResponse }>('/ai/chat', {
        method: 'POST', timeout: 90000,
        data: { question: q, user_id: session?.userId || null, context_cards: prevCards.length ? prevCards : undefined },
      });
      const payload = res.data || {};
      const answer = payload.answer || '未获取到回答';
      store.addMessage({ id: 'a' + Date.now(), role: 'ai', text: answer });
      startTyping(answer);
      const srcMap: Record<string, string> = { local_kb: '本地知识库', kb_enhanced: '知识库+AI', web_search: '联网补充', doubao: 'AI模型', fallback: '兜底回复' };
      setSourceTag(srcMap[payload.source || ''] || 'AI回答');
      if (payload.recommend_cards?.length) store.setRecommendCards(payload.recommend_cards);
      const rw = (payload as unknown as Record<string,unknown>).rewrite_suggestions;
      if (Array.isArray(rw)) setRewriteSuggestions(rw as string[]);
      const newMode = (payload.crs_mode || store.crsState.mode || 'cold_start') as string;
      const oldMode = store.crsState.mode;
      store.setCrsState({ mode: newMode, confidence_score: payload.crs_confidence?.confidence_score || 0, session_id: payload.crs_session_id });
      if (oldMode !== newMode && newMode !== 'cold_start') triggerModeCelebration(newMode);
      if (payload.ask_prompt) store.setAsk(payload.ask_prompt, payload.ask_options || [], payload.ask_id || '');
      // KG info
      if (payload.kg_entity) setKgEntity(payload.kg_entity);
      if (payload.kg_path?.path) setKgPathText(payload.kg_path.path.map(p => p.entity || p.relation || '').filter(Boolean).join(' → '));
      if (payload.kg_similar?.items) setKgSimilarNames(payload.kg_similar.items.map(i => i.entity));
      if (payload.kg_expand?.items) setKgExpandItems(payload.kg_expand.items);
      // Build action tasks from recommend cards
      if (payload.recommend_cards?.length) {
        const tasks: ActionTask[] = payload.recommend_cards.map((c, i) => ({
          id: `${c.type}_${c.id}_${Date.now()}`,
          title: c.title,
          desc: shortenReason(c.reason, c.summary || ''),
          type: c.type,
          targetId: c.id,
          done: false,
          recommended: i === 0,
          metaTitle: c.type === 'content' ? '阅读内容' : c.type === 'event' ? '报名活动' : '参与讨论',
        }));
        setActionTasks(tasks);
      }
      generatePresets(payload);
    } catch { store.addMessage({ id: 'a_err', role: 'ai', text: '提问失败，请稍后重试。' }); }
    finally { store.setSending(false); setWaitingTip(''); }
  };

  const buildPresetQueue = (basePool: string[]) => {
    const pool = [...basePool].sort(() => Math.random() - 0.5);
    setPresetQueue(pool);
    return pool;
  };

  const generatePresets = (payload?: AiChatResponse) => {
    const mode = store.crsState.mode || 'cold_start';
    if (payload?.recommended_questions?.length) {
      const f = payload.recommended_questions.slice(0, 6);
      setPresetQueue(f);
      setPresets(f.slice(0, 4).map(t => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
      return;
    }
    if (payload?.followup_questions?.length) {
      const f = payload.followup_questions.slice(0, 6);
      setPresetQueue(f);
      setPresets(f.slice(0, 4).map(t => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
      return;
    }
    // Try keyword match from recent messages
    const lastMsg = store.messages.filter(m => m.role === 'user').slice(-1)[0]?.text || '';
    for (const entry of KEYWORD_FOLLOWUP_MAP) {
      if (lastMsg.includes(entry.keyword)) {
        const qs = [...entry.questions].sort(() => Math.random() - 0.5);
        setPresetQueue(qs);
        setPresets(qs.slice(0, 4).map(t => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
        return;
      }
    }
    const pool = CRS_MODE_QUESTIONS[mode] || CRS_MODE_QUESTIONS.cold_start;
    const shuffled = buildPresetQueue(pool);
    setPresets(shuffled.slice(0, 4).map(t => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
  };

  const refreshPresets = () => {
    const pool = presetQueue.length > 4 ? presetQueue : [...(CRS_MODE_QUESTIONS[store.crsState.mode || 'cold_start'] || CRS_MODE_QUESTIONS.cold_start)].sort(() => Math.random() - 0.5);
    const remaining = pool.filter(t => !recentPresets.includes(t));
    const picked = remaining.length >= 4 ? remaining.slice(0, 4) : pool.slice(0, 4);
    setPresets(picked.map(t => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
    setRecentPresets(prev => [...prev.slice(-6), ...picked]);
    apiRequest('/recommend/track', { method: 'POST', data: { user_id: session?.userId, action: 'skip', target_type: 'preset', source_scene: 'ai_chat' } }).catch(() => {});
  };

  const handleAskAnswer = async (answer: string) => {
    const askId = store.askId, sid = store.crsState.session_id || '';
    if (!askId || !sid || !session?.userId) return;
    store.addMessage({ id: 'u_ask_' + Date.now(), role: 'user', text: answer });
    store.setSending(true); store.clearAsk();
    try {
      const res = await apiRequest<{ code: number; data: CrsAnswerResponse }>('/ai/crs/answer', { method: 'POST', data: { user_id: session.userId, session_id: sid, ask_id: askId, answer } });
      const d = res.data || {};
      const old = store.crsState.mode, nw = d.mode || old;
      store.setCrsState({ mode: nw, confidence_score: d.confidence_score || 0 });
      if (d.ask_timeline) setCrsTimeline(d.ask_timeline);
      if (d.recommend_cards?.length) store.setRecommendCards(d.recommend_cards);
      if (d.transition_msg) store.addMessage({ id: 'trans_' + Date.now(), role: 'ai', text: d.transition_msg, isTransition: true });
      if (old !== nw && nw && nw !== 'cold_start') triggerModeCelebration(nw);
    } catch {} finally { store.setSending(false); }
  };

  const triggerModeCelebration = (mode: string) => {
    const colors = mode === 'precision' ? ['#4caf50','#81c784','#a5d6a7','#66bb6a','#2e7d32','#1b5e20'] : ['#2196f3','#64b5f6','#90caf9','#42a5f5','#1565c0','#0d47a1'];
    const particles = Array.from({ length: 16 }, (_, i) => ({
      id: i, x: (Math.random() - 0.5) * 300, y: (Math.random() - 0.5) * 300,
      color: colors[i % colors.length],
    }));
    setCelebrationParticles(particles);
    setModeCelebrating(true); setCelebrationMode(mode);
    setTimeout(() => { setModeCelebrating(false); setCelebrationMode(''); }, 3000);
  };

  const trackCard = (card: RecommendCard, action: string) => {
    apiRequest('/recommend/track', { method: 'POST', data: { user_id: session?.userId, action, target_type: card.type, target_id: card.id, source_scene: 'ai_chat', explain: card.explain } }).catch(() => {});
  };

  const handleClear = () => {
    store.clearHistory(); setCrsTimeline([]); setSourceTag(''); setPresets([]); setRewriteSuggestions([]);
    setActionTasks([]); setKgEntity(''); setKgPathText(''); setKgSimilarNames([]); setKgExpandItems([]);
    setRecentPresets([]); setPresetQueue([]);
    if (session?.userId) apiRequest('/ai/crs/reset', { method: 'POST', data: { user_id: session.userId } }).catch(() => {});
  };

  const feedbackOverall = async (v: string) => {
    store.recommendCards.forEach(c => trackCard(c, v === 'like' ? 'feedback_like' : 'feedback_dislike'));
    setOverallFeedback(v);
  };

  const confidence = store.crsState.confidence_score || 0;
  const mode = store.crsState.mode || 'cold_start';
  const mood = mode === 'precision' ? 'confident' : mode === 'mixed' ? 'thinking' : 'curious';
  const dims = store.crsState.dimensions || {};

  return (
    <div className="flex flex-col h-screen max-w-[480px] mx-auto relative overflow-hidden" style={{
      background: 'linear-gradient(180deg, #faf3e8 0%, #f3e7d6 30%, #efe0cd 60%, #e8d9c4 100%)',
    }}>
      {/* Background decorative elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-20 -left-20 w-72 h-72 rounded-full bg-[radial-gradient(circle,rgba(192,138,62,0.06)_0%,transparent_70%)]" />
        <div className="absolute top-1/4 -right-16 w-56 h-56 rounded-full bg-[radial-gradient(circle,rgba(159,45,34,0.04)_0%,transparent_70%)]" />
        <div className="absolute bottom-1/3 -left-10 w-48 h-48 rounded-full bg-[radial-gradient(circle,rgba(91,140,90,0.04)_0%,transparent_70%)]" />
      </div>

      {/* Mode celebration overlay */}
      {modeCelebrating && (
        <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center gap-3 overflow-hidden" style={{ background: 'rgba(62,39,20,0.72)', backdropFilter: 'blur(8px)' }}>
          {/* Particles */}
          {celebrationParticles.map(p => (
            <div key={p.id} className="celebrate-particle" style={{
              '--px': p.x + 'px', '--py': p.y + 'px',
              background: p.color, left: '50%', top: '50%',
              animationDelay: (p.id * 0.05) + 's',
            } as React.CSSProperties} />
          ))}
          <div className="w-[160px] h-[160px] rounded-full border-2 border-white/20 animate-ping absolute" />
          <span className="text-5xl animate-bounce relative">{celebrationMode === 'precision' ? '🎯' : '🔮'}</span>
          <h2 className="text-xl font-extrabold text-white m-0 relative" style={{ textShadow: '0 0 20px rgba(200,60,30,0.5)' }}>
            {celebrationMode === 'precision' ? '了解升级 · 精准模式已开启' : '了解升级 · 探索模式已开启'}
          </h2>
          <span className="px-6 py-1.5 rounded-full text-2xl font-black text-white relative"
            style={{ background: celebrationMode === 'precision' ? 'rgba(76,175,80,0.7)' : 'rgba(33,150,243,0.7)' }}>
            {MODE_LABELS[celebrationMode] || celebrationMode}
          </span>
          <p className="text-white/70 text-sm mt-1 relative">
            {celebrationMode === 'precision' ? '黑塔已深度理解你的偏好，精准推荐已开启' : '黑塔已初步了解你的偏好'}
          </p>
        </div>
      )}

      {/* Header — 简洁顶栏 */}
      <header className="px-4 py-2.5 flex items-center justify-between shrink-0 z-10 relative"
        style={{ background: 'rgba(255,250,243,0.78)', backdropFilter: 'blur(16px)', borderBottom: '1px solid rgba(219,191,155,0.15)' }}>
        <button onClick={() => navigate('/')} className="p-2 border-none bg-transparent cursor-pointer text-[#5a4430] hover:text-[#2f2419] transition-colors"><ArrowLeft size={20} /></button>
        <span className="text-[16px] font-bold text-[#2f2419]">黑塔 · 非遗导览</span>
        <button onClick={handleClear} className="p-1.5 rounded-[10px] border-none bg-transparent cursor-pointer text-[#9c846d] hover:text-[#5a4430] hover:bg-[#f5e8d5]/50 transition-colors" title="清空对话"><Trash2 size={15} /></button>
      </header>

      {/* CRS Status Bar — always visible, click to expand detail */}
      <div onClick={() => setCrsExpanded(!crsExpanded)} className="mx-4 mb-3 px-4 py-2.5 rounded-2xl flex items-center gap-3 cursor-pointer shrink-0 z-10 relative transition-shadow hover:shadow-md"
        style={{
          background: 'rgba(255,252,247,0.95)',
          border: '1px solid rgba(219,191,155,0.18)',
          boxShadow: crsExpanded ? '0 8px 20px rgba(112,74,41,0.08)' : '0 4px 12px rgba(112,74,41,0.04)',
        }}>
        <span className="text-xs font-bold px-2.5 py-1 rounded-full shrink-0"
          style={{
            background: mode === 'precision' ? 'rgba(76,175,80,0.14)' : mode === 'mixed' ? 'rgba(33,150,243,0.14)' : 'rgba(255,152,0,0.14)',
            color: mode === 'precision' ? '#2e7d32' : mode === 'mixed' ? '#1565c0' : '#e65100',
          }}>{MODE_LABELS[mode]}</span>
        <span className="text-xs text-[#8b6a4b] shrink-0">置信度</span>
        <div className="flex-1 h-2 rounded-full" style={{ background: 'rgba(0,0,0,0.06)' }}>
          <div className="h-full rounded-full transition-all duration-700" style={{
            width: `${Math.round(confidence)}%`,
            background: mode === 'precision' ? 'linear-gradient(90deg, #4caf50, #81c784)' : mode === 'mixed' ? 'linear-gradient(90deg, #2196f3, #64b5f6)' : 'linear-gradient(90deg, #ff9800, #ffb74d)',
          }} />
        </div>
        <span className="text-sm font-extrabold shrink-0"
          style={{ color: mode === 'precision' ? '#2e7d32' : mode === 'mixed' ? '#1565c0' : '#e65100' }}>
          {Math.round(confidence)}%
        </span>
        {crsExpanded ? <ChevronUp size={14} className="text-[#9c846d] shrink-0" /> : <ChevronDown size={14} className="text-[#9c846d] shrink-0" />}
      </div>

      {/* CRS Detail Panel — expandable on status bar click */}
      {crsExpanded && (
        <div className="mx-4 mb-3 rounded-[10px] px-5 py-4 text-sm text-[#5a4430] shrink-0 animate-fade-in-up"
          style={{ background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))', boxShadow: '0 12px 28px rgba(112,74,41,0.06)', border: '1px solid rgba(219,191,155,0.22)' }}>
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-base">了解进度 · {MODE_LABELS[mode]}</span>
            <span className="text-xl font-extrabold text-brand">{Math.round(confidence)}%</span>
          </div>
          {/* Confidence bar */}
          <div className="h-3 rounded-full mb-3" style={{ background: 'rgba(0,0,0,0.06)' }}>
            <div className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${Math.round(confidence)}%`,
                background: mode === 'precision' ? 'linear-gradient(90deg, #4caf50, #81c784)' : mode === 'mixed' ? 'linear-gradient(90deg, #2196f3, #64b5f6)' : 'linear-gradient(90deg, #ff9800, #ffb74d)',
              }} />
          </div>
          {/* Dimension bars */}
          {[
            { key: 'explicit', label: '你的选择', color: 'linear-gradient(90deg, #8B4513, #A0522D)' },
            { key: 'implicit', label: '你的行为', color: 'linear-gradient(90deg, #6A0DAD, #9370DB)' },
            { key: 'dialogue', label: '你的对话', color: 'linear-gradient(90deg, #B22222, #DC143C)' },
          ].map(d => (
            <div key={d.key} className="flex items-center gap-2 mb-2 text-xs">
              <span className="w-16 text-right text-[#8b6a4b]">{d.label}</span>
              <div className="flex-1 h-2.5 rounded-full" style={{ background: 'rgba(0,0,0,0.06)' }}>
                <div className="h-full rounded-full" style={{ width: `${Math.min((dims[d.key as keyof typeof dims] as number) || 0, 100)}%`, background: d.color }} />
              </div>
              <span className="w-8 text-xs text-[#8b6a4b]">{dims[d.key as keyof typeof dims] || 0}</span>
            </div>
          ))}
          {/* Timeline */}
          {crsTimeline.length > 0 && (
            <div className="mt-3 pt-3 border-t border-[rgba(219,191,155,0.2)]">
              <span className="text-xs font-bold text-[#8b6a4b] mb-2 block">了解历程</span>
              {crsTimeline.map((log, i) => (
                <div key={i} className="flex items-start gap-2 ml-2 mb-1.5 text-xs">
                  <div className="w-1.5 h-1.5 rounded-full bg-brand mt-1.5 shrink-0" />
                  <div>
                    <span className="text-[#5a4430]">{log.question_text}</span>
                    <span className="text-[#9c846d]"> → {log.answer || '待回答'}</span>
                    <span className="text-brand ml-1">(+{log.score_delta || 0})</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 z-10">

        {/* ═══════════════════════════════════════
           数字人专用区域 — 对标小程序 ai-top-stage
           无论是否有消息，始终可见
           ═══════════════════════════════════════ */}
        <div className="rounded-[18px] px-5 pt-4 pb-3 text-center relative overflow-hidden"
          style={{
            background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
            border: '1px solid rgba(219,191,155,0.22)',
            boxShadow: '0 8px 24px rgba(112,74,41,0.06)',
          }}>
          {/* 装饰光晕 */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-48 rounded-full bg-[radial-gradient(circle,rgba(192,138,62,0.06)_0%,transparent_65%)] pointer-events-none" />
          <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-[radial-gradient(circle,rgba(159,45,34,0.03)_0%,transparent_70%)] pointer-events-none" />

          {/* 文案 */}
          <div className="relative z-10 mb-2">
            <span className="inline-block px-3 py-0.5 rounded-full text-[10px] font-semibold bg-brand-soft text-brand mb-1.5 tracking-wider">
              ✦ 黑塔 · Heritage AI
            </span>
            <h2 className="text-[20px] font-black text-[#2f2419] m-0 leading-tight" style={{ letterSpacing: '0.5px' }}>
              {MODE_HERO_TITLES[mode] || '想认识你'}
            </h2>
          </div>

          {/* 数字人 — 居中展示 */}
          <div className="relative z-10 flex justify-center -my-1">
            <DigitalHumanModel variant="ai" mood={mood} size={140} />
          </div>

          {/* 提示文案 */}
          <p className="relative z-10 text-[11px] text-[#9c846d] mt-1 mb-0">轻触黑塔可播放语音讲解</p>
        </div>

        {/* Empty state */}
        {store.messages.length === 0 && (
          <div className="flex flex-col items-center pt-1 animate-fade-in-up">
            <div className="text-center mb-4 px-4">
              <p className="text-xs font-bold text-[#8b6a4b] mb-1.5">先和黑塔聊聊你想了解的非遗方向</p>
              <p className="text-[11px] text-[#9c846d]">支持本地知识优先回答，也会顺手给你补上活动和延伸推荐。</p>
            </div>
            {mode === 'cold_start' && Object.entries(COLD_START_CATEGORIES).map(([category, questions]) => (
              <div key={category} className="w-full mb-3">
                <h3 className="text-xs font-bold text-ink-muted mb-2 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand" />
                  {category}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {questions.map((q, qi) => (
                    <button key={qi} onClick={() => handleSend(q)}
                      className="px-4 py-2.5 rounded-full text-xs cursor-pointer border-none transition-all duration-200 hover:shadow-md active:scale-[0.97] bg-gradient-to-b from-gold-50 to-gold-100 text-gold-600 border border-gold-200/30"
                    >{q}</button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Messages */}
        {store.messages.map((msg, idx) => (
          <div key={msg.id || idx}>
            <div className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`${msg.role === 'user' ? 'max-w-[78%]' : 'max-w-[92%] w-full'}`}>
                <p className={`text-[11px] mb-1.5 ${msg.role === 'user' ? 'text-right mr-2 text-[#9a7757]' : 'ml-2 text-[#9a7757]'}`}>
                  {msg.role === 'user' ? '我' : '黑塔'}
                </p>
                {msg.role === 'user' ? (
                  <div className="px-4 py-3 rounded-[10px] rounded-tr-md text-sm text-[#fff9f4] leading-relaxed"
                    style={{
                      background: 'linear-gradient(135deg, #b84835, #d4684f)',
                      boxShadow: '0 6px 16px rgba(160,50,30,0.12)',
                    }}>{msg.text}</div>
                ) : (
                  <div className="px-4 py-3 rounded-[10px] rounded-tl-md text-sm text-[#473022] leading-relaxed relative"
                    style={{
                      background: 'linear-gradient(180deg, #fdf8f0, #f7ebd8)',
                      border: '1px solid rgba(219,191,155,0.22)',
                      boxShadow: '0 3px 12px rgba(121,58,31,0.03)',
                    }}>
                    {/* 品牌色左侧竖条 */}
                    <div className="absolute left-0 top-3 bottom-3 w-[3px] rounded-r-[2px]"
                      style={{ background: 'linear-gradient(180deg, #9f2d22, #c08a3e)' }} />
                    <div className="whitespace-pre-wrap">{msg.text}</div>
                    {msg.isTransition && <div className="mt-1.5 text-xs text-brand font-semibold">—— 黑塔的反馈</div>}
                    {!msg.isTransition && !store.sending && (
                      <div className="flex gap-2 mt-3 flex-wrap">
                        <button onClick={() => handleSend(msg.text.slice(0, 40))}
                          className="px-3.5 py-1.5 rounded-full text-xs cursor-pointer transition-all duration-200 hover:shadow-sm"
                          style={{ background: 'rgba(244,228,208,0.6)', color: '#8c5a31', border: '1px solid rgba(213,185,153,0.3)' }}>
                          ↪ 继续追问
                        </button>
                        <button onClick={() => handleTTS(msg.text)}
                          className={`px-3.5 py-1.5 rounded-full text-xs cursor-pointer flex items-center gap-1.5 transition-all duration-200 hover:shadow-sm ${
                            speaking ? 'bg-brand/10 text-brand' : ''
                          }`}
                          style={speaking ? {} : { background: 'rgba(244,228,208,0.6)', color: '#8c5a31', border: '1px solid rgba(213,185,153,0.3)' }}>
                          {speaking ? <VolumeX size={12} /> : <Volume2 size={12} />} {speaking ? '播放中' : '听语音'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            {/* Follow-up question chips after last non-transition AI message */}
            {!msg.isTransition && msg.role === 'ai' && idx === store.messages.length - 1 && presets.length > 0 && !store.sending && (
              <div className="flex flex-col gap-1.5 mt-2 ml-2">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-semibold text-[#9c846d] tracking-wider">推荐发问</span>
                  <button onClick={refreshPresets} className="text-[10px] px-2 py-0.5 rounded-full cursor-pointer border-none transition-colors"
                    style={{ background: 'rgba(219,191,155,0.18)', color: '#8a6b4b' }}>换一批</button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {presets.slice(0, 4).map((p, pi) => (
                    <button key={pi} onClick={() => handleSend(p.text)}
                      className="px-3.5 py-1.5 rounded-full text-xs cursor-pointer border-none transition-all duration-200 hover:shadow-sm active:scale-[0.97]"
                      style={{
                        background: 'rgba(244,228,208,0.45)',
                        border: '1px solid rgba(213,185,153,0.22)',
                        color: '#8c5a31',
                      }}>{p.display || p.text}</button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Loading */}
        {store.sending && (
          <div className="flex justify-start">
            <div>
              <p className="text-[11px] mb-1.5 ml-2 text-[#9a7757]">黑塔</p>
              <div className="px-5 py-3.5 rounded-[10px] rounded-tl-md flex items-center gap-2.5"
                style={{ background: '#faf2e6', border: '1px solid rgba(226,197,163,0.25)', boxShadow: '0 3px 10px rgba(121,58,31,0.02)' }}>
                <div className="flex gap-1">
                  {[0,1,2].map(i => (
                    <div key={i} className="w-2 h-2 rounded-full bg-[#c28a3d]" style={{ animation: `typingBounce 1.4s ease-in-out ${i*0.15}s infinite` }} />
                  ))}
                </div>
                <span className="text-xs text-[#8b6a4b] ml-1">{waitingTip}</span>
              </div>
            </div>
          </div>
        )}

        {/* ASK prompt — hidden in precision mode */}
        {store.askPrompt && !store.sending && mode !== 'precision' && (
          <div className="rounded-[10px] px-5 py-4 animate-fade-in-up"
            style={{
              background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
              boxShadow: '0 12px 28px rgba(112,74,41,0.06)', border: '1px solid rgba(219,191,155,0.22)',
            }}>
            <p className="text-sm font-semibold text-[#2f2419] mb-3 flex items-center gap-2">
              <span className="text-base">💭</span> {store.askPrompt}
            </p>
            <div className="flex flex-wrap gap-2">
              {store.askOptions.map((opt, i) => (
                <button key={i} onClick={() => handleAskAnswer(opt)}
                  className="px-4 py-2.5 rounded-full text-xs cursor-pointer font-medium transition-all duration-200 hover:shadow-md active:scale-[0.97]"
                  style={{
                    background: 'linear-gradient(180deg, #fbefe3, #f3e2cf)',
                    border: '1px solid rgba(217,184,147,0.26)', color: '#7b4d27',
                  }}>{opt}</button>
              ))}
            </div>
          </div>
        )}

        {/* ═══════ L2 本轮结果 ═══════ */}
        {store.recommendCards.length > 0 && !store.sending && (
          <>
            <div className="layer-divider">
              <div className="layer-divider-line" />
              <span className="layer-divider-label">本轮结果</span>
              <div className="layer-divider-line" />
            </div>

            <div className="animate-fade-in-up space-y-3">
              <h4 className="text-base font-bold text-[#2f2419] flex items-center gap-2 px-1">
                <Sparkles size={16} style={{ color: '#d7a445' }} /> 延伸推荐
                <span className="text-xs font-normal text-[#a08868]">· {MODE_LABELS[mode]}模式</span>
              </h4>
              {store.recommendCards.map((card, idx) => {
                const expanded = explainExpanded[idx] || false;
                const fb = feedbackGiven[idx];
                const display = card.explain?.display;
                return (
                  <div key={idx} className="rounded-[18px] overflow-hidden"
                    style={{
                      background: 'rgba(255,250,243,0.92)',
                      border: '1px solid rgba(238,216,191,0.82)',
                      boxShadow: '0 8px 20px rgba(121,58,31,0.04)',
                    }}>
                    <button onClick={() => { trackCard(card, 'click'); navigate(card.type === 'content' ? `/content/${card.id}` : card.type === 'event' ? `/activity/${card.id}` : `/discussion/${card.id}`); }}
                    className="w-full text-left border-none bg-transparent cursor-pointer p-4 flex gap-3.5 items-start">
                      {card.cover_url ? (
                        <CoverImage coverUrl={card.cover_url} alt="" className="w-[52px] h-[52px] rounded-xl object-cover shrink-0" style={{ background: '#f5e8d5' }} />
                      ) : (
                        <div className="w-[52px] h-[52px] rounded-xl shrink-0 flex items-center justify-center text-xl"
                          style={{ background: 'linear-gradient(135deg, #f5e8d5, #eadcc8)', color: '#c08a3e' }}>
                          {card.type === 'content' ? '📖' : card.type === 'event' ? '📅' : '💬'}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                            style={{ background: card.type === 'content' ? 'rgba(91,140,90,0.1)' : card.type === 'event' ? 'rgba(192,138,62,0.1)' : 'rgba(192,57,43,0.1)',
                              color: card.type === 'content' ? '#4a7a49' : card.type === 'event' ? '#a07230' : '#b5342e' }}>
                            {card.type === 'content' ? '文化' : card.type === 'event' ? '活动' : '讨论'}
                          </span>
                          <span className="text-[13px] font-semibold text-[#2f2419]">{card.title}</span>
                        </div>
                        <p className="text-[11px] text-[#7b6141] leading-relaxed line-clamp-2">
                          {shortenReason(card.reason, card.summary || '')}
                        </p>
                      </div>
                      <ChevronRight size={14} className="shrink-0 mt-1 text-[#d4c4aa]" />
                    </button>

                    {/* Action buttons per card: like/dislike */}
                    <div className="px-4 py-2 flex items-center gap-3 border-t border-[rgba(238,216,191,0.4)]">
                      {fb ? (
                        <span className="text-[11px] text-[#8a5a2b]">{fb === 'like' ? '👍 已推荐' : '👎 已过滤'}</span>
                      ) : (
                        <>
                          <button onClick={() => { trackCard(card, 'feedback_like'); setFeedbackGiven({...feedbackGiven, [idx]: 'like'}); }}
                            className="px-2.5 py-1 rounded-full text-[10px] cursor-pointer border-none transition-colors"
                            style={{ background: 'rgba(76,175,80,0.08)', color: '#388e3c' }}>👍</button>
                          <button onClick={() => { trackCard(card, 'feedback_dislike'); setFeedbackGiven({...feedbackGiven, [idx]: 'dislike'}); }}
                            className="px-2.5 py-1 rounded-full text-[10px] cursor-pointer border-none transition-colors"
                            style={{ background: 'rgba(192,57,43,0.06)', color: '#b5342e' }}>👎</button>
                          <span className="text-[10px] text-[#9c846d]">有帮助吗？</span>
                        </>
                      )}
                      <button onClick={() => setExplainExpanded({ ...explainExpanded, [idx]: !expanded })}
                        className="ml-auto px-2.5 py-1 rounded-full text-[10px] cursor-pointer border-none transition-colors flex items-center gap-1"
                        style={{ background: 'rgba(219,191,155,0.12)', color: '#8a6b4b' }}>
                        {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                        {expanded ? '收起' : '解释'}
                      </button>
                    </div>

                    {/* Expanded explain — L2 scores + L3 strategy + L4 KG */}
                    {expanded && (
                      <div className="px-4 py-3 space-y-2 text-[11px] text-[#5a4430] bg-[#fdf9f2] border-t border-[rgba(238,216,191,0.5)]">
                        {card.explain?.final_score_text && <p>📊 综合分：{card.explain.final_score_text}</p>}
                        {card.explain?.match_score_text && <p>📈 匹配度：{card.explain.match_score_text}</p>}
                        {card.explain?.novelty_score_text && <p>🆕 新颖度：{card.explain.novelty_score_text}</p>}
                        {card.explain?.diversity_penalty_text && <p>🔄 多样性：{card.explain.diversity_penalty_text}</p>}
                        {display?.matchDetailText && <p>🔍 匹配依据：{display.matchDetailText}</p>}
                        {card.explain?.crs_mode_label && <p>🎯 推荐方式：{card.explain.crs_mode_label}</p>}
                        {display?.sources?.length ? <p>📚 数据来源：{display.sources.join('、')}</p> : null}
                        {display?.heritageTerms?.length ? <p>🏷️ 兴趣维度：{display.heritageTerms.join('、')}</p> : null}
                        {display?.similarEntities?.length ? <p>🔗 相似推荐：{display.similarEntities.join(' / ')}</p> : null}
                        {display?.expandPath ? <p>🔄 关联路径：{display.expandPath}</p> : null}
                        {display?.kgReasonText ? <p>🧠 推荐原因：{display.kgReasonText}</p> : null}
                        {card.explain?.kg_score_text ? <p>⚡ 知识图谱相似度：{card.explain.kg_score_text}</p> : null}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Overall feedback */}
              {!overallFeedback && (
                <div className="flex items-center justify-center gap-3 py-2.5">
                  <span className="text-xs text-[#a08868]">这些推荐对你有帮助吗？</span>
                  <button onClick={() => feedbackOverall('like')} className="px-3.5 py-1.5 rounded-full text-xs cursor-pointer border-none transition-all duration-200 hover:shadow-sm active:scale-[0.97]"
                    style={{ background: 'rgba(76,175,80,0.08)', color: '#388e3c' }}>👍 有帮助</button>
                  <button onClick={() => feedbackOverall('dislike')} className="px-3.5 py-1.5 rounded-full text-xs cursor-pointer border-none transition-all duration-200 hover:shadow-sm active:scale-[0.97]"
                    style={{ background: 'rgba(192,57,43,0.06)', color: '#b5342e' }}>👎 没帮助</button>
                </div>
              )}
            </div>

            {/* Action tasks */}
            {actionTasks.length > 0 && (
              <div className="rounded-[18px] overflow-hidden animate-fade-in-up"
                style={{ background: 'rgba(255,250,243,0.92)', border: '1px solid rgba(238,216,191,0.82)', boxShadow: '0 8px 20px rgba(121,58,31,0.04)' }}>
                <h4 className="text-sm font-bold text-[#2f2419] px-4 pt-3 pb-1">📋 行动清单</h4>
                {actionTasks.map((task) => (
                  <div key={task.id} onClick={() => setActionTasks(prev => prev.map(t => t.id === task.id ? { ...t, done: !t.done } : t))}
                    className="flex items-start gap-3 px-4 py-2.5 cursor-pointer transition-colors hover:bg-[#faf3e8]">
                    <div className={`w-4 h-4 rounded-full mt-0.5 shrink-0 flex items-center justify-center text-[9px] font-bold transition-colors ${
                      task.done ? 'bg-[#5b8c5a] text-white' : task.recommended ? 'border-2 border-[#d7a445]' : 'border-2 border-[#d4c4aa]'
                    }`}>
                      {task.done ? '✓' : task.recommended ? '★' : ''}
                    </div>
                    <div className={`flex-1 min-w-0 ${task.done ? 'opacity-50' : ''}`}>
                      <div className={`text-xs font-semibold text-[#2f2419] ${task.done ? 'line-through' : ''}`}>{task.title}</div>
                      <div className="text-[10px] text-[#9c846d] mt-0.5">{task.metaTitle || (task.type === 'content' ? '阅读内容' : task.type === 'event' ? '报名活动' : '参与讨论')}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ═══════ L3 深入细节 ═══════ */}
            {(rewriteSuggestions.length > 0 || kgEntity || (store.crsState.mode && crsExpanded)) && (
              <div className="layer-divider dashed">
                <div className="layer-divider-line dashed" />
                <span className="layer-divider-label">深入细节</span>
                <div className="layer-divider-line dashed" />
              </div>
            )}

            {/* Rewrite suggestions */}
            {rewriteSuggestions.length > 0 && (
              <div className="rounded-[18px] px-4 py-3"
                style={{ background: 'rgba(247,240,227,0.72)', border: '1px solid rgba(219,191,155,0.18)' }}>
                <h4 className="text-xs font-bold text-[#8b6a4b] mb-2.5">💡 换个问法试试</h4>
                <div className="flex flex-wrap gap-2">
                  {rewriteSuggestions.map((s, i) => (
                    <button key={i} onClick={() => handleSend(s)}
                      className="px-3 py-1.5 rounded-full text-xs cursor-pointer border-none hover:opacity-80 transition-opacity"
                      style={{ background: 'rgba(244,228,208,0.52)', color: '#7b4d27', border: '1px solid rgba(213,185,153,0.26)' }}>{s}</button>
                  ))}
                </div>
              </div>
            )}

            {/* KG entity panel */}
            {kgEntity && (
              <div className="rounded-[18px] px-4 py-3"
                style={{ background: 'rgba(247,242,230,0.80)', border: '1px solid rgba(219,191,155,0.18)' }}>
                <h4 className="text-xs font-bold text-[#8b6a4b] mb-2.5">🧠 关联推荐依据</h4>
                <p className="text-[11px] text-[#5a4430] mb-1">当前识别实体：<span className="font-semibold text-brand">{kgEntity}</span></p>
                {kgPathText && <p className="text-[11px] text-[#7b6141] mb-2">关联路径：{kgPathText}</p>}
                {kgSimilarNames.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-1.5">
                    {kgSimilarNames.map((n, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-full text-[10px]" style={{ background: 'rgba(91,140,90,0.08)', color: '#4a7a49' }}>相似：{n}</span>
                    ))}
                  </div>
                )}
                {kgExpandItems.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {kgExpandItems.map((item, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-full text-[10px]" style={{ background: 'rgba(192,138,62,0.08)', color: '#a07230' }}>扩展：{item.entity}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* CTA bar */}
            <div className="flex gap-3 pt-2">
              <button onClick={() => navigate('/content')}
                className="flex-1 h-[48px] rounded-full text-sm font-bold text-white border-none cursor-pointer flex items-center justify-center gap-1.5 transition-all duration-200 hover:shadow-lg active:scale-[0.97]"
                style={{ background: 'linear-gradient(135deg, #9f2d22, #c04833)', boxShadow: '0 6px 16px rgba(159,45,34,0.18)' }}>
                <BookOpen size={14} /> 看相关内容
              </button>
              <button onClick={() => navigate('/activity')}
                className="flex-1 h-[48px] rounded-full text-sm font-bold text-white border-none cursor-pointer flex items-center justify-center gap-1.5 transition-all duration-200 hover:shadow-lg active:scale-[0.97]"
                style={{ background: 'linear-gradient(135deg, #b98535, #d7a953)', boxShadow: '0 6px 16px rgba(185,133,53,0.18)' }}>
                <Calendar size={14} /> 去报名活动
              </button>
            </div>
          </>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="px-4 py-3 shrink-0 z-10 relative" style={{
        background: 'rgba(255,250,243,0.88)', backdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(219,191,155,0.2)',
        boxShadow: '0 -4px 20px rgba(120,80,40,0.04)',
      }}>
        <div className="flex gap-2.5 items-center">
          <input
            value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="输入你的问题..."
            disabled={store.sending}
            className="flex-1 h-[46px] rounded-[10px] px-5 text-sm outline-none box-border disabled:opacity-50 transition-all duration-200
              focus:shadow-[0_0_0_3px_rgba(192,138,62,0.12),0_4px_12px_rgba(192,138,62,0.08)]
              focus:scale-[1.02] focus:border-[#d4b896]"
            style={{
              background: '#fffdf8',
              border: input.trim() ? '1.5px solid #d4b896' : '1.5px solid #eadbc8',
              color: '#2f2419',
            }} />
          <button onClick={() => handleSend()} disabled={!input.trim() || store.sending}
            className="w-[46px] h-[46px] rounded-[10px] flex items-center justify-center border-none cursor-pointer shrink-0 disabled:opacity-40 transition-all duration-200"
            style={{
              background: input.trim() && !store.sending ? 'linear-gradient(135deg, #c08a3e, #d9ab53)' : '#e8d8c0',
              color: input.trim() && !store.sending ? '#fff' : '#b8a080',
              boxShadow: input.trim() && !store.sending ? '0 6px 16px rgba(184,125,51,0.18)' : 'none',
            }}>
            <Send size={18} />
          </button>
        </div>
      </div>

      <audio ref={audioRef} />
      <style>{`
        @keyframes typingBounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
