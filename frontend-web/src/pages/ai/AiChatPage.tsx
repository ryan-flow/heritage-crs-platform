import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Trash2, Sparkles, RotateCcw, Volume2, VolumeX, ArrowLeft, Info, ChevronRight } from 'lucide-react';
import { apiRequest, buildImageUrl, shortenReason } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { useChatStore } from '../../stores/chat-store';
import { AiChatResponse, RecommendCard, CrsAnswerResponse } from '../../types';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';

const CRS_MODE_QUESTIONS: Record<string, string[]> = {
  cold_start: ['第一次接触非遗，从哪类开始比较容易上手？', '传统工艺类和戏曲音乐类，哪个更适合零基础体验？', '有什么适合周末去现场感受的非遗活动？', '中国有多少项非遗被列入了联合国名录？'],
  mixed: ['云锦和苏绣，哪种工艺更值得深入看？', '古琴和古筝在听感上有什么本质区别？', '京剧和昆曲的表演风格差异在哪？', '非遗和乡村振兴是怎么结合的？'],
  precision: ['景德镇的柴窑和气窑烧出来的瓷器差别在哪？', '侗族大歌的演唱技巧为什么很难用乐谱记录？', '有哪些冷门但非常值得了解的非遗项目？', '数字化技术对非遗保护带来了什么改变？'],
};

function loadPersistedRecommendState() {
  try { const raw = localStorage.getItem('ai_recommend_state'); return raw ? JSON.parse(raw) : {}; }
  catch { return {}; }
}

export default function AiChatPage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const store = useChatStore();
  const [input, setInput] = useState('');
  const [waitingTip, setWaitingTip] = useState('');
  const [sourceTag, setSourceTag] = useState('');
  const [presets, setPresets] = useState<{ text: string; display: string }[]>([]);
  const [presetMode, setPresetMode] = useState<'default' | 'followup'>('default');
  const [crsDetailExpanded, setCrsDetailExpanded] = useState(false);
  const [crsTimeline, setCrsTimeline] = useState<{ ask_id: string; question_text: string; answer?: string; score_delta?: number }[]>([]);
  const [modeCelebrating, setModeCelebrating] = useState(false);
  const [celebrationMode, setCelebrationMode] = useState('');
  const [speaking, setSpeaking] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const scrollToBottom = useCallback(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), []);

  useEffect(() => { scrollToBottom(); }, [store.messages, scrollToBottom]);
  useEffect(() => { loadCrsState(); loadPersistedData(); }, []);

  const loadPersistedData = () => {
    const state = loadPersistedRecommendState();
    if (state.recommendCards?.length && !store.recommendCards.length) store.setRecommendCards(state.recommendCards);
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
    if (speaking) { if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0; } setSpeaking(false); return; }
    try {
      const res = await apiRequest<{ code: number; data: { audio_url: string } }>('/ai/tts', { method: 'POST', data: { text }, timeout: 30000 });
      const url = res.data?.audio_url;
      if (url) {
        const fullUrl = url.startsWith('http') ? url : `${import.meta.env.VITE_API_BASE?.replace('/api/v1', '') || ''}${url}`;
        if (!audioRef.current) audioRef.current = new Audio();
        audioRef.current.src = fullUrl;
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
    setWaitingTip('黑塔正在思考...');
    setSourceTag('');
    store.clearAsk();
    const prevCards = store.recommendCards;
    try {
      const res = await apiRequest<{ code: number; data: AiChatResponse }>('/ai/chat', {
        method: 'POST', timeout: 90000,
        data: { question: q, user_id: session?.userId || null, context_cards: prevCards.length ? prevCards : undefined },
      });
      const payload = res.data || {};
      store.addMessage({ id: 'a' + Date.now(), role: 'ai', text: payload.answer || '未获取到回答' });
      const srcMap: Record<string, string> = { local_kb: '知识库', kb_enhanced: '知识库+AI', web_search: '联网', doubao: 'AI模型', fallback: '回复' };
      setSourceTag(srcMap[payload.source || ''] || 'AI回答');
      if (payload.recommend_cards?.length) store.setRecommendCards(payload.recommend_cards);
      const newMode = payload.crs_mode || store.crsState.mode;
      const oldMode = store.crsState.mode;
      store.setCrsState({ mode: newMode, confidence_score: payload.crs_confidence?.confidence_score || 0, session_id: payload.crs_session_id });
      if (oldMode !== newMode && newMode !== 'cold_start') triggerModeCelebration(newMode as string);
      if (payload.ask_prompt) store.setAsk(payload.ask_prompt, payload.ask_options || [], payload.ask_id || '');
      generatePresets(payload);
    } catch {
      store.addMessage({ id: 'a_err', role: 'ai', text: '提问失败，请稍后重试。' });
    } finally {
      store.setSending(false);
      setWaitingTip('');
    }
  };

  const generatePresets = (payload: AiChatResponse) => {
    const f = payload.recommended_questions?.length ? payload.recommended_questions : payload.followup_questions?.slice(0, 4) || [];
    if (f.length) {
      setPresets(f.map((t: string) => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })));
      setPresetMode('followup');
    } else {
      const pool = CRS_MODE_QUESTIONS[store.crsState.mode || 'cold_start'] || CRS_MODE_QUESTIONS.cold_start;
      const shuffled = [...pool].sort(() => Math.random() - 0.5).slice(0, 4);
      setPresets(shuffled.map((t: string) => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })));
      setPresetMode('default');
    }
  };

  const handleAskAnswer = async (answer: string) => {
    const askId = store.askId, sessionId = store.crsState.session_id || '';
    if (!askId || !sessionId || !session?.userId) return;
    store.addMessage({ id: 'u_ask_' + Date.now(), role: 'user', text: answer });
    store.setSending(true); store.clearAsk();
    try {
      const res = await apiRequest<{ code: number; data: CrsAnswerResponse }>('/ai/crs/answer', { method: 'POST', data: { user_id: session.userId, session_id: sessionId, ask_id: askId, answer } });
      const data = res.data || {};
      const oldMode = store.crsState.mode, newMode = data.mode || oldMode;
      store.setCrsState({ mode: newMode, confidence_score: data.confidence_score || 0 });
      if (data.ask_timeline) setCrsTimeline(data.ask_timeline);
      if (data.recommend_cards?.length) store.setRecommendCards(data.recommend_cards);
      if (data.transition_msg) store.addMessage({ id: 'trans_' + Date.now(), role: 'ai', text: data.transition_msg, isTransition: true });
      if (oldMode !== newMode && newMode && newMode !== 'cold_start') triggerModeCelebration(newMode);
    } catch {} finally { store.setSending(false); }
  };

  const triggerModeCelebration = (mode: string) => {
    setModeCelebrating(true); setCelebrationMode(mode);
    setTimeout(() => { setModeCelebrating(false); setCelebrationMode(''); }, 3000);
  };

  const trackCard = useCallback((card: RecommendCard, action: string) => {
    apiRequest('/recommend/track', { method: 'POST', data: { user_id: session?.userId, action, target_type: card.type, target_id: card.id, source_scene: 'ai_chat', explain: card.explain } }).catch(() => {});
  }, [session]);

  const swapPresets = () => {
    const pool = CRS_MODE_QUESTIONS[store.crsState.mode || 'cold_start'] || CRS_MODE_QUESTIONS.cold_start;
    const shuffled = [...pool].sort(() => Math.random() - 0.5).slice(0, 4);
    setPresets(shuffled.map((t: string) => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })));
    setPresetMode('default');
  };  // <- this is for swapPresets

  const handleClear = () => {
    store.clearHistory(); setCrsTimeline([]); setSourceTag(''); setPresets([]); setPresetMode('default');
    if (session?.userId) apiRequest('/ai/crs/reset', { method: 'POST', data: { user_id: session.userId } }).catch(() => {});
  };

  const confidence = store.crsState.confidence_score || 0;
  const mode = store.crsState.mode || 'cold_start';
  const mood = mode === 'precision' ? 'confident' : mode === 'mixed' ? 'thinking' : 'curious';
  const modeLabels: Record<string, string> = { cold_start: '初识', mixed: '探索', precision: '精准' };

  return (
    <div className="ai-page-bg" style={{ display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: 480, margin: '0 auto', position: 'relative' }}>
      {/* Aurora blobs */}
      <div style={{ position: 'fixed', width: 200, height: 200, left: '-5%', top: '5%', background: 'radial-gradient(circle, rgba(255,201,135,0.22), transparent 70%)', filter: 'blur(20rpx)', pointerEvents: 'none', zIndex: 0 }} />
      <div style={{ position: 'fixed', width: 240, height: 240, right: '-8%', top: '8%', background: 'radial-gradient(circle, rgba(142,122,240,0.13), transparent 70%)', filter: 'blur(20rpx)', pointerEvents: 'none', zIndex: 0 }} />

      {/* Mode Celebration Overlay */}
      {modeCelebrating && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: 'rgba(62,39,20,0.72)', backdropFilter: 'blur(8rpx)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexDirection: 'column', gap: 16,
        }}>
          <div style={{
            width: 210, height: 210, borderRadius: '50%',
            border: '2rpx solid rgba(212,175,86,0.6)',
            animation: 'celebRing 1.5s ease-out forwards',
          }} />
          <span style={{ fontSize: 48, animation: 'celebIcon 0.6s cubic-bezier(0.34,1.56,0.64,1) both' }}>{'🎉'}</span>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: '#fffaf3', textShadow: '0 0 20rpx rgba(200,60,30,0.5)', margin: 0 }}>
            {celebrationMode === 'precision' ? '精准模式已开启' : '探索模式已开启'}
          </h2>
          <span style={{ padding: '8rpx 24rpx', borderRadius: 999, fontWeight: 900, fontSize: 28, color: '#fff',
            background: celebrationMode === 'precision' ? 'rgba(76,175,80,0.7)' : celebrationMode === 'mixed' ? 'rgba(33,150,243,0.7)' : 'rgba(255,152,0,0.7)',
          }}>{celebrationMode === 'precision' ? '已懂你' : celebrationMode === 'mixed' ? '思考中' : '了解中'}</span>
        </div>
      )}

      {/* Header */}
      <header style={{
        padding: '8rpx 16rpx', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'transparent', position: 'relative', zIndex: 10,
      }}>
        <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#5a4430', padding: 8 }}>
          <ArrowLeft size={20} />
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 15, fontWeight: 700, color: '#2f2419' }}>黑塔</span>
          <button onClick={() => setCrsDetailExpanded(!crsDetailExpanded)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: crsDetailExpanded ? '#9f2d22' : '#9c846d', padding: 6 }}>
            <Info size={16} />
          </button>
          <button onClick={handleClear}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9c846d', padding: 6 }}>
            <Trash2 size={16} />
          </button>
        </div>
      </header>

      {/* CRS Detail Panel */}
      {crsDetailExpanded && (
        <div className="card" style={{ margin: '0 16rpx 12rpx', padding: '16rpx 20rpx', fontSize: 12, color: '#5a4430' }}>
          <p style={{ margin: '0 0 4rpx' }}>模式：{modeLabels[mode]} | 置信度：{Math.round(confidence)}%</p>
          <p style={{ margin: 0 }}>显式={store.crsState.dimensions?.explicit ?? '-'} 隐式={store.crsState.dimensions?.implicit ?? '-'} 对话={store.crsState.dimensions?.dialogue ?? '-'}</p>
          {crsTimeline.length > 0 && crsTimeline.map((log, i) => (
            <p key={i} style={{ margin: '2rpx 0 2rpx 12rpx', fontSize: 11 }}>#{log.ask_id}: {log.question_text} → {log.answer || '?'} ({log.score_delta || 0})</p>
          ))}
        </div>
      )}

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 16rpx 20rpx', position: 'relative', zIndex: 1 }}>
        {/* Empty state with stage */}
        {store.messages.length === 0 && (
          <div style={{
            background: `radial-gradient(circle at 50% 30%, rgba(255,220,172,0.08), transparent 50%), linear-gradient(135deg, #5B3A7A 0%, #8B4513 100%)`,
            borderRadius: 30, padding: '18rpx 22rpx 14rpx',
            boxShadow: '0 18rpx 42rpx rgba(70,35,49,0.18)',
            border: '1rpx solid rgba(255,238,220,0.08)',
            position: 'relative', marginBottom: 20, textAlign: 'center',
          }}>
            <span style={{ display: 'inline-block', padding: '4rpx 14rpx', borderRadius: 999, background: 'rgba(255,245,230,0.14)', color: '#ffe1bc', fontSize: 12, marginBottom: 8 }}>
              黑塔 · Heritage AI
            </span>
            <h1 style={{ fontSize: 26, fontWeight: 900, color: '#fff9f1', textShadow: '0 4rpx 18rpx rgba(0,0,0,0.14)', margin: '0 0 8rpx' }}>
              你好，我是黑塔
            </h1>
            <p style={{ fontSize: 13, color: 'rgba(255,244,232,0.92)', margin: '0 0 14rpx' }}>
              你的非遗文化导览官，问我任何关于非遗的问题
            </p>
            <DigitalHumanModel variant="ai" mood="curious" size={160} />
          </div>
        )}

        {store.messages.map((msg, idx) => (
          <div key={msg.id || idx} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', marginBottom: 12 }}>
            <div style={{ maxWidth: '86%' }}>
              {msg.role === 'user' ? (
                <div style={{
                  padding: '14rpx 18rpx', borderRadius: '20rpx 20rpx 8rpx 20rpx',
                  background: 'linear-gradient(135deg, #aa4634, #c65b43)',
                  color: '#fff9f4', fontSize: 14, lineHeight: 1.7,
                  boxShadow: '0 8rpx 18rpx rgba(122,87,51,0.05)',
                }}>
                  {msg.text}
                </div>
              ) : (
                <div style={{
                  padding: '14rpx 18rpx', borderRadius: '20rpx 20rpx 20rpx 8rpx',
                  background: 'linear-gradient(180deg, #fbf4ea, #f7ead7)',
                  color: '#473022', fontSize: 14, lineHeight: 1.7,
                  border: '1rpx solid rgba(226,197,163,0.34)',
                  boxShadow: '0 4rpx 12rpx rgba(121,58,31,0.04)',
                }}>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                  {msg.isTransition && <div style={{ marginTop: 6, fontSize: 12, color: '#9f2d22', fontWeight: 600 }}>—— 黑塔的反馈</div>}
                  {idx === store.messages.length - 1 && sourceTag && !msg.isTransition && !store.sending && (
                    <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center' }}>
                      <span style={{ fontSize: 11, padding: '2rpx 10rpx', borderRadius: 999, background: '#f6e8d8', color: '#8a5a20' }}>{sourceTag}</span>
                      <button onClick={() => handleTTS(msg.text)}
                        style={{ background: '#f4e4d0', border: 'none', borderRadius: 999, width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#8c5a31' }}>
                        {speaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {store.sending && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 12 }}>
            <div style={{
              padding: '14rpx 18rpx', borderRadius: 20, minWidth: 80,
              background: '#faf0e3', border: '1rpx solid rgba(226,197,163,0.34)',
              display: 'flex', gap: 6, alignItems: 'center',
            }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 8, height: 8, borderRadius: '50%', background: '#c28a3d',
                  animation: `typingBounce 1.4s ease-in-out ${i * 0.15}s infinite`,
                }} />
              ))}
              <span style={{ fontSize: 12, color: '#8b6a4b', marginLeft: 4 }}>{waitingTip}</span>
            </div>
          </div>
        )}

        {/* ASK Prompt */}
        {store.askPrompt && !store.sending && (
          <div style={{
            marginBottom: 14, padding: '18rpx 20rpx', borderRadius: 24,
            background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
            boxShadow: '0 12rpx 28rpx rgba(112,74,41,0.06)',
            border: '1rpx solid rgba(219,191,155,0.22)',
          }}>
            <p style={{ margin: '0 0 12rpx', fontSize: 14, fontWeight: 600, color: '#2f2419' }}>{store.askPrompt}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {store.askOptions.map((opt, i) => (
                <button key={i} onClick={() => handleAskAnswer(opt)}
                  style={{
                    padding: '10rpx 18rpx', borderRadius: 999, border: '1rpx solid rgba(217,184,147,0.26)',
                    background: 'linear-gradient(180deg, #fbefe3, #f3e2cf)', color: '#7b4d27',
                    fontSize: 12, cursor: 'pointer', fontWeight: 500,
                  }}>
                  {opt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Recommend Cards */}
        {store.recommendCards.length > 0 && !store.sending && (
          <div style={{ marginBottom: 14 }}>
            <h4 style={{ fontSize: 13, color: '#8b6a4b', marginBottom: 8, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
              <Sparkles size={12} style={{ color: '#d7a445' }} /> 推荐内容
            </h4>
            {store.recommendCards.map((card, idx) => (
              <button key={idx} onClick={() => {
                trackCard(card, 'click');
                navigate(card.type === 'content' ? `/content/${card.id}` : card.type === 'event' ? `/activity/${card.id}` : `/discussion/${card.id}`);
              }}
              style={{
                width: '100%', textAlign: 'left', border: '1rpx solid rgba(238,216,191,0.82)',
                borderRadius: 18, padding: '14rpx 16rpx', marginBottom: 8,
                background: 'rgba(255,250,243,0.92)', cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  {card.cover_url && <img src={buildImageUrl(card.cover_url)} alt="" style={{ width: 48, height: 48, borderRadius: 10, objectFit: 'cover' }} />}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontSize: 10, padding: '2rpx 8rpx', borderRadius: 999, background: '#f4e4d0', color: '#8a5a2b' }}>
                        {card.type === 'content' ? '文化' : card.type === 'event' ? '活动' : '讨论'}
                      </span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#2f2419' }}>{card.title}</span>
                    </div>
                    <p style={{ fontSize: 11, color: '#7b6141', margin: 0, lineHeight: 1.4 }}>
                      {shortenReason(card.reason, card.summary || '')}
                    </p>
                  </div>
                  <ChevronRight size={14} style={{ color: '#d4c4aa' }} />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Presets */}
        {presets.length > 0 && !store.sending && !store.askPrompt && (
          <div style={{ marginBottom: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: '#9c846d', fontWeight: 600 }}>{presetMode === 'followup' ? '继续探索' : '推荐发问'}</span>
              <button onClick={swapPresets} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#9c846d', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
                <RotateCcw size={11} /> 换一批
              </button>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {presets.map((p, i) => (
                <button key={i} onClick={() => handleSend(p.text)}
                  style={{
                    padding: '10rpx 16rpx', borderRadius: 999, fontSize: 12, cursor: 'pointer',
                    background: 'linear-gradient(180deg, #fbefe3, #f3e2cf)',
                    border: '1rpx solid rgba(217,184,147,0.26)',
                    color: '#7b4d27',
                  }}>
                  {p.display || p.text}
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{
        padding: '10rpx 16rpx', paddingBottom: 'calc(10rpx + env(safe-area-inset-bottom, 16rpx))',
        background: 'rgba(255,250,243,0.92)', backdropFilter: 'blur(12rpx)',
        borderTop: '1rpx solid rgba(219,191,155,0.22)', position: 'relative', zIndex: 10,
      }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="输入你的问题..."
            disabled={store.sending}
            style={{
              flex: 1, height: 44, borderRadius: 20, padding: '0 16rpx', fontSize: 14,
              background: '#fffdf8', border: '1rpx solid #eadbc8', color: '#2f2419',
              outline: 'none', boxSizing: 'border-box',
            }}
          />
          <button onClick={() => handleSend()} disabled={!input.trim() || store.sending}
            style={{
              width: 44, height: 44, borderRadius: 20, display: 'flex', alignItems: 'center', justifyContent: 'center',
              border: 'none', cursor: 'pointer', flexShrink: 0,
              background: input.trim() && !store.sending
                ? 'linear-gradient(135deg, #ba7f34, #d9ab53)'
                : '#e8d8c0',
              color: input.trim() && !store.sending ? '#fff' : '#b8a080',
              boxShadow: input.trim() && !store.sending ? '0 4rpx 10rpx rgba(184,125,51,0.12)' : 'none',
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
        @keyframes celebRing {
          0% { transform: scale(0.8); opacity: 1; }
          100% { transform: scale(1.6); opacity: 0; }
        }
        @keyframes celebIcon {
          0% { transform: scale(0) rotate(-30deg); opacity: 0; }
          100% { transform: scale(1) rotate(0deg); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
