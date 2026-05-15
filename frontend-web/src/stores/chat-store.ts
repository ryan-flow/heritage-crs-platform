import { create } from 'zustand'
import { ChatMessage, RecommendCard, CrsState } from '../types'

interface ChatState {
  messages: ChatMessage[]
  sending: boolean
  recommendCards: RecommendCard[]
  crsState: Partial<CrsState>
  askPrompt: string
  askOptions: string[]
  askId: string
  presets: { text: string; display: string }[]
  addMessage: (msg: ChatMessage) => void
  setMessages: (msgs: ChatMessage[]) => void
  setSending: (v: boolean) => void
  setRecommendCards: (cards: RecommendCard[]) => void
  setCrsState: (s: Partial<CrsState>) => void
  setAsk: (prompt: string, options: string[], askId: string) => void
  clearAsk: () => void
  setPresets: (p: { text: string; display: string }[]) => void
  clearHistory: () => void
}

const HISTORY_KEY = 'ai_chat_history'
const MAX_MESSAGES = 20

function loadHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? JSON.parse(raw).slice(-MAX_MESSAGES) : []
  } catch { return [] }
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: loadHistory(),
  sending: false,
  recommendCards: [],
  crsState: {},
  askPrompt: '',
  askOptions: [],
  askId: '',
  presets: [],
  addMessage: (msg) => {
    const msgs = [...get().messages, msg].slice(-MAX_MESSAGES)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs))
    set({ messages: msgs })
  },
  setMessages: (msgs) => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(msgs))
    set({ messages: msgs })
  },
  setSending: (v) => set({ sending: v }),
  setRecommendCards: (cards) => set({ recommendCards: cards }),
  setCrsState: (s) => set({ crsState: { ...get().crsState, ...s } }),
  setAsk: (prompt, options, askId) => set({ askPrompt: prompt, askOptions: options, askId }),
  clearAsk: () => set({ askPrompt: '', askOptions: [], askId: '' }),
  setPresets: (p) => set({ presets: p }),
  clearHistory: () => {
    localStorage.removeItem(HISTORY_KEY)
    localStorage.removeItem('ai_recommend_state')
    set({ messages: [], recommendCards: [], crsState: {}, askPrompt: '', askOptions: [], askId: '' })
  },
}))
