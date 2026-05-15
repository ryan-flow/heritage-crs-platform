import { create } from 'zustand'
import { Session } from '../types'

interface AuthState {
  session: Session | null
  setSession: (s: Session | null) => void
  isLoggedIn: () => boolean
  logout: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  session: (() => {
    try {
      const raw = localStorage.getItem('session')
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })(),
  setSession: (s) => {
    if (s) {
      localStorage.setItem('session', JSON.stringify(s))
    } else {
      localStorage.removeItem('session')
    }
    set({ session: s })
  },
  isLoggedIn: () => {
    const s = get().session
    return !!(s && s.userId)
  },
  logout: () => {
    localStorage.removeItem('session')
    localStorage.removeItem('ai_chat_history')
    localStorage.removeItem('ai_recommend_state')
    set({ session: null })
  },
}))
