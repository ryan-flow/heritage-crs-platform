import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Trash2, Sparkles, ChevronDown, ChevronUp, RotateCcw, Volume2, VolumeX, ArrowLeft, Info } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { useChatStore } from '../../stores/chat-store';
import { AiChatResponse, RecommendCard, CrsAnswerResponse } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';

const DEFAULT_QUESTIONS = [
  '第一次接触非遗，适合先从什么体验项目开始？',
  '昆曲适合新手从哪里入门？',
  '云锦为什么会让人觉得工艺门槛很高？',
  '古琴为什么常被看作适合静心聆听的艺术？',
  '苏绣和湘绣在风格上有什么不同？',
  '中医针灸为什么能入选联合国非遗名录？',
  '剪纸艺术为什么能流传这么久？',
  '太极拳作为非遗有什么特别的文化价值？',
  '京剧脸谱的颜色分别代表什么含义？',
  '川剧变脸到底是怎么做到的？',
];

const CRS_MODE_QUESTIONS: Record<string, string[]> = {
  cold_start: [
    '第一次接触非遗，从哪类开始比较容易上手？',
    '传统工艺类和戏曲音乐类，哪个更适合零基础体验？',
    '有什么适合周末去现场感受的非遗活动？',
    '中国有多少项非遗被列入了联合国名录？',
    '二十四节气除了指导农事，还有什么文化意义？',
  ],
  mixed: [
    '云锦和苏绣，哪种工艺更值得深入看？',
    '古琴和古筝在听感上有什么本质区别？',
    '京剧和昆曲的表演风格差异在哪？',
    '非遗和乡村振兴是怎么结合的？',
  ],
  precision: [
    '景德镇的柴窑和气窑烧出来的瓷器差别在哪？',
    '侗族大歌的演唱技巧为什么很难用乐谱记录？',
    '有哪些冷门但非常值得了解的非遗项目？',
    '数字化技术对非遗保护带来了什么改变？',
  ],
};

function loadPersistedRecommendState() {
  try {
    const raw = localStorage.getItem('ai_recommend_state');
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export default function AiChatPage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const store = useChatStore();
  const [input, setInput] = useState('');
  const [waitingTip, setWaitingTip] = useState('');
  const [webSearching, setWebSearching] = useState(false);
  const [sourceTag, setSourceTag] = useState('');
  const [presetMode, setPresetMode] = useState<'default' | 'followup'>('default');
  const [presets, setPresets] = useState<{ text: string; display: string }[]>([]);
  const [crsDetailExpanded, setCrsDetailExpanded] = useState(false);
  const [crsTimeline, setCrsTimeline] = useState<{ ask_id: string; question_text: string; answer?: string; score_delta?: number }[]>([]);
  const [modeCelebrating, setModeCelebrating] = useState(false);
  const [celebrationMode, setCelebrationMode] = useState('');
  const [speaking, setSpeaking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [store.messages, scrollToBottom]);

  useEffect(() => {
    loadCrsState();
    loadPersistedData();
    inputRef.current?.focus();
  }, []);

  const loadPersistedData = () => {
    const state = loadPersistedRecommendState();
    if (state.recommendCards?.length && !store.recommendCards.length) {
      store.setRecommendCards(state.recommendCards);
    }
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
        triggerColdStartAsk(data.session_id as string);
      }
    } catch {}
  };

  const triggerColdStartAsk = (_sessionId?: string) => {
    store.setAsk('你最想了解哪类非物质文化遗产？', ['传统工艺', '戏曲音乐', '民俗节俗', '饮食医药'], 'A01');
  };

  const handleTTS = async (text: string) => {
    if (speaking) {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0; }
      setSpeaking(false);
      return;
    }
    try {
      const res = await apiRequest<{ code: number; data: { audio_url: string } }>('/ai/tts', {
        method: 'POST',
        data: { text },
        timeout: 30000,
      });
      if (res.code === 0 && res.data?.audio_url) {
        const url = res.data.audio_url.startsWith('http') ? res.data.audio_url
          : `${import.meta.env.VITE_API_BASE?.replace('/api/v1', '') || ''}${res.data.audio_url}`;
        if (!audioRef.current) audioRef.current = new Audio();
        audioRef.current.src = url;
        audioRef.current.onended = () => setSpeaking(false);
        setSpeaking(true);
        await audioRef.current.play();
      }
    } catch {}
  };

  const handleSend = async (overrideText?: string) => {
    const q = (overrideText || input).trim();
    if (!q || store.sending) return;
    store.addMessage({ id: 'u' + Date.now(), role: 'user', text: q });
    setInput('');
    store.setSending(true);
    setWebSearching(false);
    setWaitingTip('黑塔正在思考...');
    setSourceTag('');
    store.clearAsk();

    const waitingTimer = setTimeout(() => {
      setWebSearching(true);
      setWaitingTip('正在仔细斟酌中...');
    }, 1500);

    const prevCards = store.recommendCards;

    try {
      const res = await apiRequest<{ code: number; data: AiChatResponse }>('/ai/chat', {
        method: 'POST',
        timeout: 90000,
        data: { question: q, user_id: session?.userId || null, context_cards: prevCards.length ? prevCards : undefined },
      });

      const payload = res.data || {};
      const answer = payload.answer || '未获取到回答';
      const source = payload.source || '';
      store.addMessage({ id: 'a' + Date.now(), role: 'ai', text: answer });

      const sourceTagMap: Record<string, string> = {
        local_kb: '知识库', kb_enhanced: '知识库+AI', web_search: '联网',
        web_enhanced: '联网+AI', doubao: 'AI模型', fallback: '回复',
      };
      setSourceTag(sourceTagMap[source] || 'AI回答');
      setWebSearching(false);

      if (payload.recommend_cards?.length) {
        store.setRecommendCards(payload.recommend_cards);
        localStorage.setItem('ai_recommend_state', JSON.stringify({ recommendCards: payload.recommend_cards }));
      }

      const newMode = payload.crs_mode || store.crsState.mode;
      const oldMode = store.crsState.mode;
      store.setCrsState({ mode: newMode, confidence_score: payload.crs_confidence?.confidence_score || 0, session_id: payload.crs_session_id });
      if (oldMode !== newMode && newMode !== 'cold_start') triggerModeCelebration(newMode as string);
      if (payload.ask_prompt) store.setAsk(payload.ask_prompt, payload.ask_options || [], payload.ask_id || '');
      generatePresets(q, payload);
    } catch {
      store.addMessage({ id: 'a_err', role: 'ai', text: '提问失败，请稍后重试。' });
    } finally {
      clearTimeout(waitingTimer);
      store.setSending(false);
      setWaitingTip('');
    }
  };

  const generatePresets = (_lastQuestion: string, payload: AiChatResponse) => {
    const followups = payload.recommended_questions?.length
      ? payload.recommended_questions
      : payload.followup_questions?.slice(0, 4) || [];
    if (followups.length) {
      setPresets(followups.map((t: string) => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })));
      setPresetMode('followup');
    } else {
      const mode = store.crsState.mode || 'cold_start';
      const pool = CRS_MODE_QUESTIONS[mode] || CRS_MODE_QUESTIONS.cold_start;
      const shuffled = [...pool].sort(() => Math.random() - 0.5).slice(0, 4);
      setPresets(shuffled.map((t: string) => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })));
      setPresetMode('default');
    }
  };

  const handleAskAnswer = async (answer: string) => {
    const askId = store.askId;
    const sessionId = store.crsState.session_id || '';
    if (!askId || !sessionId || !session?.userId) return;
    store.addMessage({ id: 'u_ask_' + Date.now(), role: 'user', text: answer });
    store.setSending(true);
    store.clearAsk();
    try {
      const res = await apiRequest<{ code: number; data: CrsAnswerResponse }>('/ai/crs/answer', {
        method: 'POST',
        data: { user_id: session.userId, session_id: sessionId, ask_id: askId, answer },
      });
      const data = res.data || {};
      const oldMode = store.crsState.mode;
      const newMode = data.mode || oldMode;
      store.setCrsState({ mode: newMode, confidence_score: data.confidence_score || 0 });
      if (data.ask_timeline) setCrsTimeline(data.ask_timeline);
      if (data.recommend_cards?.length) store.setRecommendCards(data.recommend_cards);
      if (data.transition_msg) store.addMessage({ id: 'trans_' + Date.now(), role: 'ai', text: data.transition_msg, isTransition: true });
      if (oldMode !== newMode && newMode && newMode !== 'cold_start') triggerModeCelebration(newMode);
    } catch {} finally {
      store.setSending(false);
    }
  };

  const triggerModeCelebration = (mode: string) => {
    setModeCelebrating(true);
    setCelebrationMode(mode);
    setTimeout(() => { setModeCelebrating(false); setCelebrationMode(''); }, 3000);
  };

  const trackCard = useCallback((card: RecommendCard, action: string) => {
    apiRequest('/recommend/track', {
      method: 'POST',
      data: { user_id: session?.userId, action, target_type: card.type, target_id: card.id, source_scene: 'ai_chat', explain: card.explain },
    }).catch(() => {});
  }, [session]);

  const swapPresets = () => {
    const mode = store.crsState.mode || 'cold_start';
    const pool = CRS_MODE_QUESTIONS[mode] || CRS_MODE_QUESTIONS.cold_start;
    const shuffled = [...pool].sort(() => Math.random() - 0.5).slice(0, 4);
    setPresets(shuffled.map((t: string) => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })));
    setPresetMode('default');
  };

  const handleClear = () => {
    store.clearHistory();
    setCrsTimeline([]);
    setSourceTag('');
    setPresets([]);
    setPresetMode('default');
    if (session?.userId) {
      apiRequest('/ai/crs/reset', { method: 'POST', data: { user_id: session.userId } }).catch(() => {});
    }
  };

  const confidence = store.crsState.confidence_score || 0;
  const mode = store.crsState.mode || 'cold_start';
  const mood = mode === 'precision' ? 'confident' : mode === 'mixed' ? 'thinking' : 'curious';
  const modeLabels: Record<string, string> = { cold_start: '初识', mixed: '探索', precision: '精准' };

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto bg-parchment relative">
      {/* Header */}
      <header className="sticky top-0 z-40 glass-card-elevated border-b border-ink-border/30 rounded-none px-4 h-14 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <button onClick={() => navigate('/')} className="p-1 hover:bg-parchment-dark/50 rounded-lg transition-colors">
            <ArrowLeft size={20} className="text-ink-secondary" />
          </button>
          <div className="scale-75 -my-8">
            <DigitalHumanModel variant="ai" mood={mood} speaking={store.sending} size={100} />
          </div>
          <div>
            <h1 className="text-sm font-serif font-bold text-ink">黑塔</h1>
            <div className="flex items-center gap-1.5">
              <SealBadge variant={mood === 'confident' ? 'cinnabar' : mood === 'thinking' ? 'jade' : 'gold'}>
                {modeLabels[mode]}
              </SealBadge>
              <span className="text-[11px] text-ink-muted">{Math.round(confidence)}%</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setCrsDetailExpanded(!crsDetailExpanded)}
            className="p-2 hover:bg-parchment-dark/50 rounded-lg transition-colors">
            <Info size={18} className={crsDetailExpanded ? 'text-cinnabar-600' : 'text-ink-muted'} />
          </button>
          <button onClick={handleClear} className="p-2 hover:bg-parchment-dark/50 rounded-lg transition-colors">
            <Trash2 size={18} className="text-ink-muted" />
          </button>
        </div>
      </header>

      {/* CRS Detail Panel */}
      {crsDetailExpanded && (
        <GlassCard className="m-3 p-3 text-xs text-ink-secondary space-y-1 rounded-2xl">
          <p>模式：{modeLabels[mode] || mode}</p>
          <p>置信度：显式={store.crsState.dimensions?.explicit ?? '-'} 隐式={store.crsState.dimensions?.implicit ?? '-'} 对话={store.crsState.dimensions?.dialogue ?? '-'}</p>
          {crsTimeline.length > 0 && (
            <div>
              <p className="font-medium mt-1">ASK 记录：</p>
              {crsTimeline.map((log, i) => (
                <p key={i} className="ml-2">#{log.ask_id}: {log.question_text} → {log.answer || '待回答'} ({log.score_delta || 0})</p>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* Mode Celebration Toast */}
      {modeCelebrating && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 cinnabar-gradient text-white px-5 py-2.5 rounded-2xl shadow-lg animate-bounce text-sm font-medium">
           {celebrationMode === 'precision' ? '精准模式已开启！黑塔已了解你的偏好' : '探索模式已开启！'}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {store.messages.length === 0 && (
          <div className="text-center py-12">
            <DigitalHumanModel variant="ai" mood="curious" size={200} />
            <h2 className="text-base font-serif font-bold text-ink mt-2">我是黑塔，你的非遗导览官</h2>
            <p className="text-sm text-ink-muted mt-1.5">问我任何关于非遗的问题，或选择一个话题开始</p>
          </div>
        )}

        {store.messages.map((msg, idx) => (
          <div key={msg.id || idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[82%] ${msg.role === 'user' ? '' : ''}`}>
              {msg.role === 'user' ? (
                <div className="cinnabar-gradient text-white px-4 py-2.5 rounded-2xl rounded-tr-md text-sm shadow-sm">
                  {msg.text}
                </div>
              ) : (
                <GlassCard className="px-4 py-2.5 rounded-2xl rounded-tl-md">
                  <div className="whitespace-pre-wrap leading-relaxed text-sm text-ink">{msg.text}</div>
                  {msg.isTransition && (
                    <div className="mt-1 text-xs text-cinnabar-600 font-medium">—— 黑塔的反馈</div>
                  )}
                  {idx === store.messages.length - 1 && sourceTag && !msg.isTransition && !store.sending && (
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-[11px] bg-parchment-dark text-ink-secondary px-1.5 py-0.5 rounded-full">{sourceTag}</span>
                      <button onClick={() => handleTTS(msg.text)}
                        className="p-1 hover:bg-parchment-dark/50 rounded-full transition-colors">
                        {speaking ? <VolumeX size={14} className="text-cinnabar-600" /> : <Volume2 size={14} className="text-ink-muted" />}
                      </button>
                    </div>
                  )}
                </GlassCard>
              )}
            </div>
          </div>
        ))}

        {/* Loading */}
        {store.sending && (
          <div className="flex justify-start">
            <GlassCard className="px-4 py-3 rounded-2xl rounded-tl-md">
              <div className="flex items-center gap-2.5">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-cinnabar-300 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-cinnabar-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <span className="w-2 h-2 bg-cinnabar-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
                <span className="text-xs text-ink-muted">{waitingTip}</span>
              </div>
            </GlassCard>
          </div>
        )}

        {/* ASK Prompt */}
        {store.askPrompt && !store.sending && (
          <GlassCard className="p-4 border-gold-200/50">
            <p className="text-sm font-serif font-bold text-ink mb-3">{store.askPrompt}</p>
            <div className="flex flex-wrap gap-2">
              {store.askOptions.map((opt, i) => (
                <button key={i} onClick={() => handleAskAnswer(opt)}
                  className="px-4 py-2 bg-white/80 border border-ink-border/40 rounded-xl text-sm text-ink-secondary hover:border-cinnabar-300 hover:text-cinnabar-700 hover:bg-cinnabar-50/50 transition-all shadow-sm">
                  {opt}
                </button>
              ))}
            </div>
          </GlassCard>
        )}

        {/* Recommend Cards */}
        {store.recommendCards.length > 0 && !store.sending && (
          <div>
            <h4 className="text-xs font-medium text-ink-muted mb-2 flex items-center gap-1">
              <Sparkles size={12} className="text-gold-500" /> 推荐内容
            </h4>
            <div className="space-y-2">
              {store.recommendCards.map((card, idx) => (
                <button
                  key={`${card.type}-${card.id}-${idx}`}
                  onClick={() => {
                    trackCard(card, 'click');
                    const path = card.type === 'content' ? `/content/${card.id}` : card.type === 'event' ? `/activity/${card.id}` : `/discussion/${card.id}`;
                    navigate(path);
                  }}
                  className="w-full glass-card p-3 flex gap-3 hover:border-gold-200 transition-all text-left card-lift"
                >
                  {card.cover_url && (
                    <img src={buildImageUrl(card.cover_url)} alt="" className="w-14 h-14 rounded-lg object-cover shrink-0 bg-parchment-dark" loading="lazy" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                        card.type === 'content' ? 'bg-blue-50 text-blue-600' : card.type === 'event' ? 'bg-jade-50 text-jade-500' : 'bg-gold-50 text-gold-600'
                      }`}>
                        {card.type === 'content' ? '文化' : card.type === 'event' ? '活动' : '讨论'}
                      </span>
                    </div>
                    <h5 className="text-sm font-medium text-ink">{card.title}</h5>
                    <p className="text-xs text-ink-muted mt-0.5 line-clamp-1">{shortenReason(card.reason, card.summary || '')}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Presets */}
        {presets.length > 0 && !store.sending && !store.askPrompt && (
          <div className="pt-1">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-ink-muted">
                {presetMode === 'followup' ? '继续探索' : '推荐发问'}
              </span>
              <button onClick={swapPresets} className="flex items-center gap-1 text-xs text-ink-muted hover:text-ink-secondary transition-colors">
                <RotateCcw size={11} /> 换一批
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {presets.map((p, i) => (
                <button key={i} onClick={() => handleSend(p.text)}
                  className="px-3 py-1.5 glass-card rounded-full text-xs text-ink-secondary hover:border-cinnabar-300 hover:text-cinnabar-700 transition-all">
                  {p.display || p.text}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="shrink-0 px-4 py-3 bg-parchment/95 backdrop-blur-sm border-t border-ink-border/30">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="输入你的问题..."
            className="flex-1 px-4 py-2.5 glass-card rounded-xl text-sm text-ink placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 focus:border-cinnabar-300/50 transition-all"
            disabled={store.sending}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || store.sending}
            className={`p-2.5 rounded-xl transition-all ${
              input.trim() && !store.sending
                ? 'cinnabar-gradient text-white shadow-md hover:shadow-lg active:scale-95'
                : 'bg-parchment-dark text-ink-muted'
            }`}
          >
            <Send size={18} />
          </button>
        </div>
      </div>

      <audio ref={audioRef} />
    </div>
  );
}
