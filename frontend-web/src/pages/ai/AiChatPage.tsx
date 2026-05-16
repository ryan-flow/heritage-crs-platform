import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Trash2, Sparkles, RotateCcw, Volume2, VolumeX, ArrowLeft, Info, ChevronRight, ChevronDown, ChevronUp, ThumbsUp, ThumbsDown, Copy, BookOpen, Calendar, MessageCircle } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { useChatStore } from '../../stores/chat-store';
import { AiChatResponse, RecommendCard, CrsAnswerResponse } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';

/* ================================================================
   AI Chat Page — fully featured, matching mini-program layout
   ================================================================ */

const CRS_MODE_QUESTIONS: Record<string, string[]> = {
  cold_start: ['第一次接触非遗，从哪类开始比较容易上手？', '传统工艺类和戏曲音乐类，哪个更适合零基础体验？', '有什么适合周末去现场感受的非遗活动？', '中国有多少项非遗被列入了联合国名录？'],
  mixed: ['云锦和苏绣，哪种工艺更值得深入看？', '古琴和古筝在听感上有什么本质区别？', '京剧和昆曲的表演风格差异在哪？', '非遗和乡村振兴是怎么结合的？'],
  precision: ['景德镇的柴窑和气窑烧出来的瓷器差别在哪？', '侗族大歌的演唱技巧为什么很难用乐谱记录？', '有哪些冷门但非常值得了解的非遗项目？', '数字化技术对非遗保护带来了什么改变？'],
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
  const [presetMode, setPresetMode] = useState<'default' | 'followup'>('default');
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

  const bottomRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const typingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const scrollToBottom = () => bottomRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => { scrollToBottom(); }, [store.messages]);
  useEffect(() => { loadCrsState(); return () => { if (typingTimerRef.current) clearInterval(typingTimerRef.current); }; }, []);

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
      generatePresets(payload);
    } catch { store.addMessage({ id: 'a_err', role: 'ai', text: '提问失败，请稍后重试。' }); }
    finally { store.setSending(false); setWaitingTip(''); }
  };

  const generatePresets = (payload: AiChatResponse) => {
    const f = payload.recommended_questions?.length ? payload.recommended_questions : payload.followup_questions?.slice(0, 4) || [];
    if (f.length) setPresets(f.map((t: string) => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
    else {
      const pool = CRS_MODE_QUESTIONS[store.crsState.mode || 'cold_start'] || CRS_MODE_QUESTIONS.cold_start;
      setPresets([...pool].sort(() => Math.random() - 0.5).slice(0, 4).map((t: string) => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
    }
    setPresetMode(f.length ? 'followup' : 'default');
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
    setModeCelebrating(true); setCelebrationMode(mode);
    setTimeout(() => { setModeCelebrating(false); setCelebrationMode(''); }, 3000);
  };

  const trackCard = (card: RecommendCard, action: string) => {
    apiRequest('/recommend/track', { method: 'POST', data: { user_id: session?.userId, action, target_type: card.type, target_id: card.id, source_scene: 'ai_chat', explain: card.explain } }).catch(() => {});
  };

  const handleClear = () => {
    store.clearHistory(); setCrsTimeline([]); setSourceTag(''); setPresets([]); setRewriteSuggestions([]);
    if (session?.userId) apiRequest('/ai/crs/reset', { method: 'POST', data: { user_id: session.userId } }).catch(() => {});
  };

  const swapPresets = () => {
    const pool = CRS_MODE_QUESTIONS[store.crsState.mode || 'cold_start'] || CRS_MODE_QUESTIONS.cold_start;
    setPresets([...pool].sort(() => Math.random() - 0.5).slice(0, 4).map((t: string) => ({ text: t, display: t.length > 16 ? t.slice(0, 16) + '…' : t })));
    setPresetMode('default');
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
        <div className="fixed inset-0 z-[9999] flex flex-col items-center justify-center gap-4" style={{ background: 'rgba(62,39,20,0.72)', backdropFilter: 'blur(8px)' }}>
          <div className="w-[210px] h-[210px] rounded-full border-2 border-amber-300/60 animate-ping" />
          <span className="text-5xl animate-bounce">🎉</span>
          <h2 className="text-2xl font-extrabold text-white m-0" style={{ textShadow: '0 0 20px rgba(200,60,30,0.5)' }}>
            {celebrationMode === 'precision' ? '精准模式已开启' : '探索模式已开启'}
          </h2>
          <span className="px-6 py-1.5 rounded-full text-3xl font-black text-white"
            style={{ background: celebrationMode === 'precision' ? 'rgba(76,175,80,0.7)' : 'rgba(33,150,243,0.7)' }}>
            {MODE_LABELS[celebrationMode] || celebrationMode}
          </span>
        </div>
      )}

      {/* Header */}
      <header className="px-4 py-2.5 flex items-center justify-between shrink-0 z-10 relative"
        style={{ background: 'rgba(255,250,243,0.78)', backdropFilter: 'blur(16px)', borderBottom: '1px solid rgba(219,191,155,0.15)' }}>
        <button onClick={() => navigate('/')} className="p-2 border-none bg-transparent cursor-pointer text-[#5a4430] hover:text-[#2f2419] transition-colors"><ArrowLeft size={20} /></button>
        <div className="flex items-center gap-2.5">
          <span className="text-[16px] font-bold text-[#2f2419] tracking-wide">黑塔</span>
          <span className="text-[11px] px-2.5 py-0.5 rounded-full font-semibold"
            style={{
              background: mode === 'precision' ? 'rgba(76,175,80,0.12)' : mode === 'mixed' ? 'rgba(33,150,243,0.12)' : 'rgba(255,152,0,0.12)',
              color: mode === 'precision' ? '#388e3c' : mode === 'mixed' ? '#1976d2' : '#e65100',
            }}>{MODE_LABELS[mode]}</span>
          <button onClick={() => setCrsExpanded(!crsExpanded)} className={`p-1.5 rounded-lg border-none cursor-pointer transition-colors ${crsExpanded ? 'text-brand bg-[#fdf3ed]' : 'text-[#9c846d] hover:text-[#5a4430]'}`}
            style={{ background: crsExpanded ? 'rgba(159,45,34,0.08)' : 'transparent' }}>
            <Info size={16} /></button>
          <button onClick={handleClear} className="p-1.5 rounded-lg border-none bg-transparent cursor-pointer text-[#9c846d] hover:text-[#5a4430] transition-colors"><Trash2 size={16} /></button>
        </div>
      </header>

      {/* CRS Detail Panel */}
      {crsExpanded && (
        <div className="mx-4 mb-3 rounded-[20px] px-5 py-4 text-sm text-[#5a4430] shrink-0"
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
        {/* Empty state — Hero stage */}
        {store.messages.length === 0 && (
          <div className="rounded-[30px] px-5 py-6 text-center relative overflow-hidden mb-5"
            style={{
              background: 'linear-gradient(160deg, #3d2340 0%, #6b3a5b 25%, #8b4513 60%, #5c3a20 100%)',
              boxShadow: '0 20px 48px rgba(60,25,35,0.24), 0 0 0 1px rgba(255,238,220,0.06)',
            }}>
            {/* Background decorative glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 rounded-full bg-[radial-gradient(circle,rgba(255,200,140,0.1)_0%,transparent_65%)] pointer-events-none" />
            <div className="absolute bottom-0 left-1/4 w-48 h-32 rounded-full bg-[radial-gradient(circle,rgba(175,130,200,0.08)_0%,transparent_65%)] pointer-events-none" />

            <span className="relative inline-block px-3.5 py-1 rounded-full text-xs font-semibold bg-white/[0.14] text-[#ffe1bc] mb-3 tracking-wider">
              ✦ 黑塔 · Heritage AI
            </span>
            <h1 className="relative text-[28px] font-black text-[#fff9f1] m-0 mb-2 tracking-wide" style={{ textShadow: '0 4px 18px rgba(0,0,0,0.2)' }}>
              {MODE_HERO_TITLES[mode]}
            </h1>
            <p className="relative text-sm text-white/85 mb-4 leading-relaxed">我是你的非遗文化导览官，问我任何关于非遗的问题</p>
            <div className="relative flex justify-center">
              <DigitalHumanModel variant="ai" mood={mood} size={200} />
            </div>
            {/* Floating decorative dots */}
            <div className="absolute top-8 right-8 w-1.5 h-1.5 rounded-full bg-amber-200/30 ping-slow" />
            <div className="absolute bottom-20 left-6 w-1 h-1 rounded-full bg-purple-200/30 ping-slow" style={{ animationDelay: '1s' }} />
          </div>
        )}

        {/* Messages */}
        {store.messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[86%] ${msg.role === 'user' ? '' : 'w-full'}`}>
              {/* Role label */}
              <p className={`text-[11px] mb-1.5 ${msg.role === 'user' ? 'text-right mr-2 text-[#9a7757]' : 'ml-2 text-[#9a7757]'}`}>
                {msg.role === 'user' ? '我' : '黑塔'}
              </p>
              {msg.role === 'user' ? (
                <div className="px-4 py-3 rounded-[20px] rounded-tr-md text-sm text-[#fff9f4] leading-relaxed"
                  style={{
                    background: 'linear-gradient(135deg, #b84835, #d4684f)',
                    boxShadow: '0 6px 16px rgba(160,50,30,0.12)',
                  }}>{msg.text}</div>
              ) : (
                <div className="px-4 py-3 rounded-[20px] rounded-tl-md text-sm text-[#473022] leading-relaxed"
                  style={{
                    background: 'linear-gradient(180deg, #fdf8f0, #f7ebd8)',
                    border: '1px solid rgba(219,191,155,0.22)',
                    boxShadow: '0 3px 12px rgba(121,58,31,0.03)',
                  }}>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                  {msg.isTransition && <div className="mt-1.5 text-xs text-brand font-semibold">—— 黑塔的反馈</div>}
                  {/* Per-message action buttons */}
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
        ))}

        {/* Loading */}
        {store.sending && (
          <div className="flex justify-start">
            <div>
              <p className="text-[11px] mb-1.5 ml-2 text-[#9a7757]">黑塔</p>
              <div className="px-5 py-3.5 rounded-[20px] rounded-tl-md flex items-center gap-2.5"
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

        {/* ASK prompt */}
        {store.askPrompt && !store.sending && (
          <div className="rounded-[20px] px-5 py-4 animate-fade-in-up"
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

        {/* Recommend cards */}
        {store.recommendCards.length > 0 && !store.sending && (
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-[#8b6a4b] flex items-center gap-1.5 px-1">
              <Sparkles size={13} style={{ color: '#d7a445' }} /> 延伸推荐
              <span className="text-xs font-normal text-[#a08868]">· {MODE_LABELS[mode]}推荐</span>
            </h4>
            {store.recommendCards.map((card, idx) => {
              const expanded = explainExpanded[idx] || false;
              const fb = feedbackGiven[idx];
              return (
                <div key={idx} className="rounded-[18px] overflow-hidden"
                  style={{
                    background: 'rgba(255,250,243,0.92)',
                    border: '1px solid rgba(238,216,191,0.82)',
                    boxShadow: '0 8px 20px rgba(121,58,31,0.04)',
                  }}>
                  <button onClick={() => {
                    trackCard(card, 'click');
                    navigate(card.type === 'content' ? `/content/${card.id}` : card.type === 'event' ? `/activity/${card.id}` : `/discussion/${card.id}`);
                  }}
                  className="w-full text-left border-none bg-transparent cursor-pointer p-4 flex gap-3.5 items-start">
                    {card.cover_url ? (
                      <img src={buildImageUrl(card.cover_url)} alt="" className="w-[52px] h-[52px] rounded-xl object-cover shrink-0" style={{ background: '#f5e8d5' }} />
                    ) : (
                      <div className="w-[52px] h-[52px] rounded-xl shrink-0 flex items-center justify-center text-xl"
                        style={{ background: 'linear-gradient(135deg, #f5e8d5, #eadcc8)', color: '#c08a3e' }}>
                        {card.type === 'content' ? '📖' : card.type === 'event' ? '📅' : '💬'}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                          style={{
                            background: card.type === 'content' ? 'rgba(192,57,43,0.1)' : card.type === 'event' ? 'rgba(192,138,62,0.1)' : 'rgba(91,140,90,0.1)',
                            color: card.type === 'content' ? '#b5342e' : card.type === 'event' ? '#a07230' : '#4a7a49',
                          }}>
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

                  {/* Explain toggle */}
                  {card.explain && (
                    <>
                      <button onClick={() => setExplainExpanded({ ...explainExpanded, [idx]: !expanded })}
                        className="w-full flex items-center justify-center gap-1 py-2 px-4 text-xs text-[#8a5a2b] border-none bg-[#faf3e8] cursor-pointer hover:bg-[#f5e8d5] transition-colors">
                        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        {expanded ? '收起解释' : '展开解释'}
                      </button>
                      {expanded && (
                        <div className="px-4 py-3 space-y-2 text-xs text-[#5a4430] bg-[#fdf9f2] border-t border-[rgba(238,216,191,0.5)]">
                          {card.explain.match_score_text && <p>📊 匹配度：{card.explain.match_score_text}</p>}
                          {card.explain.final_score_text && <p>⭐ 综合分：{card.explain.final_score_text}</p>}
                          {card.explain.novelty_score_text && <p>🆕 新颖度：{card.explain.novelty_score_text}</p>}
                          {card.explain.diversity_penalty_text && <p>🔄 多样性：{card.explain.diversity_penalty_text}</p>}
                        </div>
                      )}
                    </>
                  )}

                  {/* Feedback per card */}
                  {fb ? (
                    <div className="px-4 py-2 text-xs text-center text-[#8a5a2b] bg-[#faf3e8] border-t border-[rgba(238,216,191,0.5)]">
                      {fb === 'like' ? '👍 感谢反馈' : '👎 会继续优化'}
                    </div>
                  ) : null}
                </div>
              );
            })}

            {/* Overall feedback */}
            {!overallFeedback && (
              <div className="flex items-center justify-center gap-3 py-2.5">
                <span className="text-xs text-[#a08868]">这些推荐对你有帮助吗？</span>
                <button onClick={() => feedbackOverall('like')} className="px-3.5 py-1.5 rounded-full text-xs cursor-pointer border-none transition-all duration-200 hover:shadow-sm active:scale-[0.97]"
                  style={{ background: 'rgba(76,175,80,0.08)', color: '#388e3c' }}>
                  👍 有帮助
                </button>
                <button onClick={() => feedbackOverall('dislike')} className="px-3.5 py-1.5 rounded-full text-xs cursor-pointer border-none transition-all duration-200 hover:shadow-sm active:scale-[0.97]"
                  style={{ background: 'rgba(192,57,43,0.06)', color: '#b5342e' }}>
                  👎 没帮助
                </button>
              </div>
            )}
          </div>
        )}

        {/* Rewrite suggestions */}
        {rewriteSuggestions.length > 0 && !store.sending && (
          <div className="rounded-[18px] px-4 py-3"
            style={{ background: 'rgba(247,240,227,0.72)', border: '1px solid rgba(219,191,155,0.18)' }}>
            <h4 className="text-xs font-bold text-[#8b6a4b] mb-2.5">💡 换个问法试试</h4>
            <div className="flex flex-wrap gap-2">
              {rewriteSuggestions.map((s, i) => (
                <button key={i} onClick={() => handleSend(s)}
                  className="px-3 py-1.5 rounded-full text-xs cursor-pointer border-none hover:opacity-80 transition-opacity"
                  style={{ background: 'rgba(244,228,208,0.52)', color: '#7b4d27', border: '1px solid rgba(213,185,153,0.26)' }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Presets */}
        {presets.length > 0 && !store.sending && !store.askPrompt && (
          <div>
            <div className="flex justify-between items-center mb-2.5">
              <span className="text-xs font-semibold text-[#9c846d] flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-[#c08a3e]" />
                {presetMode === 'followup' ? '继续探索' : '推荐发问'}
              </span>
              <button onClick={swapPresets} className="flex items-center gap-1 text-xs text-[#9c846d] border-none bg-transparent cursor-pointer hover:text-[#5a4430] transition-colors">
                <RotateCcw size={11} /> 换一批
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {presets.map((p, i) => (
                <button key={i} onClick={() => handleSend(p.text)}
                  className="px-4 py-2.5 rounded-full text-xs cursor-pointer border-none whitespace-nowrap transition-all duration-200 hover:shadow-md active:scale-[0.97]"
                  style={{
                    background: 'linear-gradient(180deg, #fbefe3, #f3e2cf)',
                    border: '1px solid rgba(217,184,147,0.26)', color: '#7b4d27',
                  }}>{p.display || p.text}</button>
              ))}
            </div>
          </div>
        )}

        {/* CTA bar */}
        {store.recommendCards.length > 0 && !store.sending && (
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
            className="flex-1 h-[46px] rounded-[22px] px-5 text-sm outline-none box-border disabled:opacity-50 transition-all duration-200 focus:shadow-md"
            style={{
              background: '#fffdf8',
              border: input.trim() ? '1.5px solid #d4b896' : '1.5px solid #eadbc8',
              color: '#2f2419',
              boxShadow: input.trim() ? '0 0 0 3px rgba(192,138,62,0.06)' : 'none',
            }} />
          <button onClick={() => handleSend()} disabled={!input.trim() || store.sending}
            className="w-[46px] h-[46px] rounded-[22px] flex items-center justify-center border-none cursor-pointer shrink-0 disabled:opacity-40 transition-all duration-200"
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
