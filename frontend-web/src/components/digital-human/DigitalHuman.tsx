import { useState, useEffect, useCallback } from 'react'
import { Volume2, VolumeX } from 'lucide-react'

interface Props {
  mood?: string
  size?: 'sm' | 'md' | 'lg'
  speaking?: boolean
  bubble?: string
  onSpeak?: () => void
  onToggle?: () => void
}

const MOOD_EXPRESSIONS: Record<string, string> = {
  curious: '😊',
  thinking: '🤔',
  confident: '😌',
  speaking: '🗣️',
  listening: '👂',
}

export default function DigitalHuman({ mood = 'curious', size = 'md', speaking = false, bubble = '', onSpeak, onToggle }: Props) {
  const [glow, setGlow] = useState(false)

  useEffect(() => {
    if (speaking) {
      const interval = setInterval(() => setGlow(g => !g), 600)
      return () => clearInterval(interval)
    }
    setGlow(false)
  }, [speaking])

  const sizeClasses = {
    sm: 'w-10 h-10 text-lg',
    md: 'w-16 h-16 text-2xl',
    lg: 'w-24 h-24 text-4xl',
  }

  return (
    <div className="relative inline-flex flex-col items-center">
      {bubble && (
        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-white text-xs text-ink-light px-3 py-1 rounded-full shadow-sm border border-amber-100 whitespace-nowrap">
          {bubble}
        </div>
      )}
      <button
        onClick={onToggle || onSpeak}
        className={`${sizeClasses[size]} rounded-full flex items-center justify-center transition-all duration-500 cursor-pointer
          ${glow ? 'shadow-lg shadow-amber-200 scale-105' : 'shadow-md'}
          bg-gradient-to-br from-amber-100 via-amber-50 to-orange-50 border-2 border-amber-200 hover:border-amber-300`}
      >
        <span className={speaking ? 'animate-bounce' : ''}>
          {MOOD_EXPRESSIONS[mood] || MOOD_EXPRESSIONS.curious}
        </span>
      </button>
      {onSpeak && (
        <button onClick={onSpeak} className="mt-1 p-1 hover:bg-amber-50 rounded-full transition-colors">
          {speaking ? <VolumeX size={14} className="text-ink-lighter" /> : <Volume2 size={14} className="text-ink-lighter" />}
        </button>
      )}
    </div>
  )
}
