import { create } from 'zustand'
import { ChatMessage, RecommendCard, CrsState, FixedCta, KgState, ActionTask } from '../types'

const CRS_MODE_QUESTIONS: Record<string, string[]> = {
  cold_start: ['第一次接触非遗，从哪类开始比较容易上手？', '传统工艺类和戏曲音乐类，哪个更适合零基础体验？', '有什么适合周末去现场感受的非遗活动？', '中国有多少项非遗被列入了联合国名录？', '皮影戏、木偶戏、布袋戏，这些有什么不同？', '二十四节气除了指导农事，还有什么文化意义？', '非遗和普通手艺最大的区别在哪里？', '想带小朋友了解非遗，从哪个方向切入比较好？', '非遗传承人是怎么培养出来的？', '非遗和乡村振兴是怎么结合的？', '现在最热门的非遗体验活动有哪些？', '想系统地了解一个非遗类别，推荐什么顺序？'],
  mixed: ['云锦和苏绣，哪种工艺更值得深入看？', '古琴和古筝在听感上有什么本质区别？', '京剧和昆曲的表演风格差异在哪？', '端午节在不同地区有什么不同的庆祝方式？', '非遗传承中活态传承是什么意思？', '有没有适合自己动手体验的非遗项目？', '中医里的经络理论和非遗有什么关系？', '花灯制作属于哪一类非遗？入门难度如何？', '非遗进校园活动一般会包含哪些内容？', '非遗和乡村振兴是怎么结合的？', '现在最热门的非遗体验活动有哪些？', '想系统地了解一个非遗类别，推荐什么顺序？'],
  precision: ['景德镇的柴窑和气窑烧出来的瓷器差别在哪？', '侗族大歌的演唱技巧为什么很难用乐谱记录？', '蜀锦的挑花结本工艺具体是怎么操作的？', '中医针灸和艾灸在传承路线上有什么不同？', '皮影戏的雕刻刀法对最终演出效果有多大影响？', '非遗文创产品为什么经常被说不够原汁原味？', '有哪些冷门但非常值得了解的非遗项目？', '非遗保护中的生产性保护是什么概念？', '如何判断一场非遗演出的质量好不好？', '数字化技术对非遗保护带来了什么改变？'],
}

const KEYWORD_FOLLOWUP_MAP = [
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
]

const HISTORY_KEY = 'ai_chat_history'
const RECOMMEND_STATE_KEY = 'ai_recommend_state'
const MAX_MESSAGES = 20

function loadHistory(): ChatMessage[] {
  try { const raw = localStorage.getItem(HISTORY_KEY); return raw ? JSON.parse(raw).slice(-MAX_MESSAGES) : [] } catch { return [] }
}
function loadPersistedState() {
  try { const raw = localStorage.getItem(RECOMMEND_STATE_KEY); return raw ? JSON.parse(raw) : {} } catch { return {} }
}
function savePersistedState(state: Record<string, unknown>) {
  try { localStorage.setItem(RECOMMEND_STATE_KEY, JSON.stringify(state)) } catch {}
}
function uniqueQuestions(list: string[]): string[] {
  const seen = new Set<string>(); return (list || []).filter(q => { const n = (q || '').trim(); if (!n || seen.has(n)) return false; seen.add(n); return true })
}
function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] }; return a
}
function getLastMeaningfulUserQuestion(messages: ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) { const m = messages[i]; if (m.role === 'user' && m.text && !['围绕这个方向', '能再详细说说吗', '怎么继续？'].some(k => m.text.includes(k))) return m.text }; return ''
}
function deriveFollowupAnchor(opts: { question?: string; kgEntity?: string; messages: ChatMessage[] }): string {
  if (opts.kgEntity) return opts.kgEntity; const lastQ = getLastMeaningfulUserQuestion(opts.messages); for (const e of KEYWORD_FOLLOWUP_MAP) { if (lastQ.includes(e.keyword)) return e.keyword }; return lastQ || opts.question || ''
}
function buildGenericFollowups(topic: string): string[] {
  const s = topic.replace(/[？?。！!，,]/g, '').slice(0, 10); if (!s) return []; return [`${s}怎么入门？`, `${s}先看什么最合适？`, `${s}怎么线下体验？`, `${s}下一步怎么继续？`, `${s}有哪些代表内容？`, `${s}和相关项目有什么区别？`]
}
function buildRecommendPrefixFn(cards: RecommendCard[], strategy: string): string {
  if (!cards?.length) return ''; const types = cards.map(c => c.type); if (strategy === 'ask_clarify') return '看起来你还在收窄方向，我先把最值得继续看的线索排出来。'; if (types.includes('content') && types.includes('event')) return '因为你刚才的问题已经有明确方向，我先帮你补了内容和活动两条继续探索路线。'; if (types.includes('topic')) return '除了直接回答，我也补了社区里的讨论线索，方便你继续顺着看。'; return '看起来你更像想找入门路径，所以我先给你排了一条继续探索路线。'
}
function buildActionTasksFromCards(cards: RecommendCard[]): ActionTask[] {
  const map: Record<string, { title: string; metaTitle: string }> = { content: { title: '先读 1 篇相关入门内容', metaTitle: '阅读内容' }, event: { title: '看看这个活动是否值得报名', metaTitle: '报名活动' }, topic: { title: '去社区看看大家怎么讨论', metaTitle: '参与讨论' } }
  return cards.slice(0, 3).map((card, idx) => { const f = map[card.type] || { title: '继续沿着这条线索探索', metaTitle: '探索' }; return { id: `${card.type}-${card.id}-${idx}`, title: f.title, type: card.type, desc: card.reason || card.title, targetId: card.id, done: false, recommended: idx === 0, metaTitle: f.metaTitle } })
}

interface ChatState {
  messages: ChatMessage[]; sending: boolean; recommendCards: RecommendCard[]; crsState: Partial<CrsState>
  askPrompt: string; askOptions: string[]; askId: string; presets: { text: string; display: string }[]
  fixedCta: FixedCta; kgState: KgState; actionTasks: ActionTask[]; rewriteSuggestions: string[]
  recommendSummary: { summary: string; brief: string; sources: string[]; expanded: boolean }
  strategyDisplay: string; dialogueStrategy: string; strategyNote: string; recommendPrefix: string
  currentFollowupAnchor: string; recentPresets: string[]
  addMessage: (msg: ChatMessage) => void; setMessages: (msgs: ChatMessage[]) => void; setSending: (v: boolean) => void
  setRecommendCards: (cards: RecommendCard[]) => void; setCrsState: (s: Partial<CrsState>) => void
  setAsk: (prompt: string, options: string[], askId: string) => void; clearAsk: () => void
  setPresets: (p: { text: string; display: string }[]) => void; clearHistory: () => void
  setFixedCta: (cta: FixedCta) => void; setKgState: (kg: Partial<KgState>) => void
  setActionTasks: (tasks: ActionTask[]) => void; setRewriteSuggestions: (s: string[]) => void
  setRecommendSummary: (s: Partial<ChatState['recommendSummary']>) => void
  setStrategyInfo: (info: { strategyDisplay?: string; dialogueStrategy?: string; strategyNote?: string; recommendPrefix?: string }) => void
  setCurrentFollowupAnchor: (anchor: string) => void; setRecentPresets: (q: string[]) => void
  processRecommendPayload: (payload: Record<string, unknown>) => void
  generatePresets: (payload?: Record<string, unknown>) => void; refreshPresets: () => void
}

export const useChatStore = create<ChatState>((set, get) => {
  const p = loadPersistedState()
  return {
    messages: loadHistory(), sending: false,
    recommendCards: p.recommendCards || [], crsState: p.crsState || {},
    askPrompt: p.askPrompt || '', askOptions: p.askOptions || [], askId: p.askId || '', presets: p.presets || [],
    fixedCta: p.fixedCta || { show: false, contentId: null, eventId: null },
    kgState: p.kgState || { entity: '', pathText: '', similarNames: [], expandItems: [] },
    actionTasks: p.actionTasks || [], rewriteSuggestions: p.rewriteSuggestions || [],
    recommendSummary: p.recommendSummary || { summary: '', brief: '', sources: [], expanded: false },
    strategyDisplay: p.strategyDisplay || '', dialogueStrategy: p.dialogueStrategy || '',
    strategyNote: p.strategyNote || '', recommendPrefix: p.recommendPrefix || '',
    currentFollowupAnchor: p.currentFollowupAnchor || '', recentPresets: [],
    addMessage: (msg) => { const msgs = [...get().messages, msg].slice(-MAX_MESSAGES); localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs)); set({ messages: msgs }) },
    setMessages: (msgs) => { const s = msgs.slice(-MAX_MESSAGES); localStorage.setItem(HISTORY_KEY, JSON.stringify(s)); set({ messages: s }) },
    setSending: (v) => set({ sending: v }),
    setRecommendCards: (cards) => { set({ recommendCards: cards }); savePersistedState({ ...loadPersistedState(), recommendCards: cards }) },
    setCrsState: (s) => set({ crsState: { ...get().crsState, ...s } }),
    setAsk: (prompt, options, askId) => set({ askPrompt: prompt, askOptions: options, askId }),
    clearAsk: () => set({ askPrompt: '', askOptions: [], askId: '' }),
    setPresets: (p) => set({ presets: p }),
    setFixedCta: (cta) => { set({ fixedCta: cta }); savePersistedState({ ...loadPersistedState(), fixedCta: cta }) },
    setKgState: (kg) => set({ kgState: { ...get().kgState, ...kg } }),
    setActionTasks: (tasks) => { set({ actionTasks: tasks }); savePersistedState({ ...loadPersistedState(), actionTasks: tasks }) },
    setRewriteSuggestions: (s) => set({ rewriteSuggestions: s }),
    setRecommendSummary: (s) => set({ recommendSummary: { ...get().recommendSummary, ...s } }),
    setStrategyInfo: (info) => set({ strategyDisplay: info.strategyDisplay ?? get().strategyDisplay, dialogueStrategy: info.dialogueStrategy ?? get().dialogueStrategy, strategyNote: info.strategyNote ?? get().strategyNote, recommendPrefix: info.recommendPrefix ?? get().recommendPrefix }),
    setCurrentFollowupAnchor: (anchor) => set({ currentFollowupAnchor: anchor }),
    setRecentPresets: (q) => set({ recentPresets: q }),
    processRecommendPayload: (payload) => {
      const cards = (payload.recommend_cards || []) as RecommendCard[]; const strategy = (payload.strategy || 'knowledge_answer') as string
      const tasks = buildActionTasksFromCards(cards); const cc = cards.find(c => c.type === 'content'); const ec = cards.find(c => c.type === 'event')
      const fixedCta: FixedCta = { show: !!(cc || ec), contentId: cc?.id || null, eventId: ec?.id || null }
      const ps = (payload.recommend_payload as Record<string, unknown>)?.profile_summary as Record<string, unknown> | undefined
      const summaryText = (ps?.summary_text as string) || ((ps?.sources as string[]) || []).join(' · ')
      const kgEntity = (payload.kg_entity as string) || ''
      set({
        recommendCards: cards, actionTasks: tasks, fixedCta, rewriteSuggestions: (payload.rewrite_suggestions as string[]) || [],
        kgState: { entity: kgEntity, pathText: (((payload.kg_path as Record<string, unknown>)?.path || []) as { entity?: string; relation?: string }[]).map(s => s.entity || (s.relation ? `[${s.relation}]` : '')).filter(Boolean).join(' → '), similarNames: (((payload.kg_similar as Record<string, unknown>)?.items || []) as { entity: string }[]).map(i => i.entity).filter(Boolean).slice(0, 3), expandItems: (((payload.kg_expand as Record<string, unknown>)?.items || []) as { entity: string }[]).slice(0, 3) },
        strategyDisplay: (payload.strategy_display || '') as string, dialogueStrategy: strategy, strategyNote: (payload.strategy_note || '') as string,
        recommendPrefix: (payload.recommend_prefix || buildRecommendPrefixFn(cards, strategy)) as string,
        recommendSummary: { summary: summaryText || '', brief: summaryText ? '基于当前问答 + 历史偏好' : '', sources: ((ps?.sources as string[]) || []), expanded: false },
      })
      savePersistedState({ ...loadPersistedState(), recommendCards: cards, actionTasks: tasks, fixedCta })
    },
    generatePresets: (payload) => {
      const st = get(); const mode = st.crsState.mode || 'cold_start'
      const rec = uniqueQuestions((payload?.recommended_questions as string[]) || [])
      if (rec.length) { set({ presets: shuffle(rec).slice(0, 4).map(t => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })) }); return }
      const fu = uniqueQuestions((payload?.followup_questions as string[]) || [])
      if (fu.length) { set({ presets: shuffle(fu).slice(0, 4).map(t => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })) }); return }
      const lastQ = getLastMeaningfulUserQuestion(st.messages); const anchor = deriveFollowupAnchor({ question: lastQ, kgEntity: st.kgState.entity, messages: st.messages })
      for (const e of KEYWORD_FOLLOWUP_MAP) { if (anchor.includes(e.keyword)) { set({ presets: shuffle(e.questions).slice(0, 4).map(t => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })) }); return } }
      if (anchor) { const g = buildGenericFollowups(anchor); if (g.length) { set({ presets: shuffle(g).slice(0, 4).map(t => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })) }); return } }
      set({ presets: shuffle(CRS_MODE_QUESTIONS[mode] || CRS_MODE_QUESTIONS.cold_start).slice(0, 4).map(t => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })) })
    },
    refreshPresets: () => {
      const st = get(); const mode = st.crsState.mode || 'cold_start'; const lastQ = getLastMeaningfulUserQuestion(st.messages)
      const anchor = deriveFollowupAnchor({ question: lastQ, kgEntity: st.kgState.entity, messages: st.messages })
      let pool: string[] = []; for (const e of KEYWORD_FOLLOWUP_MAP) { if (anchor.includes(e.keyword)) { pool = e.questions; break } }
      if (!pool.length && anchor) pool = buildGenericFollowups(anchor); if (!pool.length) pool = CRS_MODE_QUESTIONS[mode] || CRS_MODE_QUESTIONS.cold_start
      const filtered = pool.filter(q => !st.recentPresets.includes(q)); const picked = (filtered.length >= 4 ? filtered : pool).slice(0, 4)
      set({ presets: picked.map(t => ({ text: t, display: t.length > 18 ? t.slice(0, 18) + '…' : t })), recentPresets: [...st.recentPresets.slice(-8), ...picked] })
    },
    clearHistory: () => {
      localStorage.removeItem(HISTORY_KEY); localStorage.removeItem(RECOMMEND_STATE_KEY)
      set({ messages: [], recommendCards: [], crsState: {}, askPrompt: '', askOptions: [], askId: '', fixedCta: { show: false, contentId: null, eventId: null }, kgState: { entity: '', pathText: '', similarNames: [], expandItems: [] }, actionTasks: [], rewriteSuggestions: [], recommendSummary: { summary: '', brief: '', sources: [], expanded: false }, strategyDisplay: '', dialogueStrategy: '', strategyNote: '', recommendPrefix: '', currentFollowupAnchor: '', recentPresets: [], presets: [] })
    },
  }
})
