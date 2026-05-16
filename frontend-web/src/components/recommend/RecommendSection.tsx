import { useNavigate } from 'react-router-dom'
import { Sparkles, ExternalLink, ChevronDown, ChevronUp, ThumbsUp, ThumbsDown } from 'lucide-react'
import { RecommendCard } from '../../types'
import CoverImage from '../ui/CoverImage'
import { useState } from 'react'

interface Props {
  cards: RecommendCard[]
  onTrack?: (card: RecommendCard, action: string) => void
}

export default function RecommendSection({ cards, onTrack }: Props) {
  if (!cards.length) return null

  return (
    <div className="mt-4">
      <div className="flex items-center gap-1.5 mb-3">
        <Sparkles size={16} className="text-cinnabar-800" />
        <span className="text-sm font-medium text-ink">为您推荐</span>
      </div>
      <div className="space-y-3">
        {cards.map((card, idx) => (
          <RecommendCardItem key={`${card.type}-${card.id}`} card={card} idx={idx} onTrack={onTrack} />
        ))}
      </div>
    </div>
  )
}

function RecommendCardItem({ card, idx, onTrack }: { card: RecommendCard; idx: number; onTrack?: (card: RecommendCard, action: string) => void }) {
  const navigate = useNavigate()
  const [expanded, setExpanded] = useState(false)

  const typeLabels: Record<string, string> = { content: '内容', event: '活动', topic: '讨论' }
  const typeColors: Record<string, string> = { content: 'bg-blue-100 text-blue-700', event: 'bg-green-100 text-green-700', topic: 'bg-amber-100 text-amber-700' }
  const typePaths: Record<string, string> = { content: '/content/', event: '/activity/', topic: '/discussion/' }

  const handleClick = () => {
    onTrack?.(card, 'click')
    navigate(`${typePaths[card.type]}${card.id}`)
  }

  const explain = card.explain || {}
  const display = explain.display
  const kgTerms = display?.heritageTerms || []

  return (
    <div className="bg-white rounded-xl border border-amber-100 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div className="flex gap-3 p-3 cursor-pointer" onClick={handleClick}>
        {card.cover_url && (
          <div className="w-20 h-20 shrink-0 rounded-lg overflow-hidden bg-amber-50">
            <CoverImage coverUrl={card.cover_url} alt={card.title} className="w-full h-full object-cover" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            <span className={`text-xs px-1.5 py-0.5 rounded ${typeColors[card.type] || 'bg-gray-100 text-gray-600'}`}>
              {typeLabels[card.type] || card.type}
            </span>
            {explain.crs_mode_label && (
              <span className="text-xs text-heritage-600">{explain.crs_mode_label}</span>
            )}
          </div>
          <h4 className="text-sm font-medium text-ink line-clamp-2">{card.title}</h4>
          {card.reason && (
            <p className="text-xs text-ink-lighter mt-1 line-clamp-2">{card.reason}</p>
          )}
        </div>
        <ExternalLink size={16} className="text-ink-lighter shrink-0 mt-1" />
      </div>

      {/* Explain detail */}
      {kgTerms.length > 0 && (
        <div className="px-3 pb-2 flex flex-wrap gap-1">
          {kgTerms.slice(0, 3).map((t: string, i: number) => (
            <span key={i} className="text-xs bg-amber-50 text-heritage-700 px-1.5 py-0.5 rounded">{t}</span>
          ))}
        </div>
      )}

      <div className="border-t border-amber-50 px-3 py-1.5 flex items-center justify-between">
        <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          className="text-xs text-ink-lighter hover:text-ink-light flex items-center gap-1">
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          推荐依据
        </button>
        <div className="flex gap-2">
          <button onClick={(e) => { e.stopPropagation(); onTrack?.(card, 'feedback_like') }}
            className="p-1 hover:bg-green-50 rounded transition-colors">
            <ThumbsUp size={14} className="text-ink-lighter hover:text-green-600" />
          </button>
          <button onClick={(e) => { e.stopPropagation(); onTrack?.(card, 'feedback_dislike') }}
            className="p-1 hover:bg-red-50 rounded transition-colors">
            <ThumbsDown size={14} className="text-ink-lighter hover:text-red-500" />
          </button>
        </div>
      </div>

      {expanded && explain.match_score_text && (
        <div className="px-3 pb-3 text-xs text-ink-lighter space-y-0.5 bg-amber-50/50">
          <p>综合评分：{explain.final_score_text || '-'}</p>
          <p>匹配度：{explain.match_score_text || '-'} {display?.matchDetailText ? `(${display.matchDetailText})` : ''}</p>
          {explain.novelty_score_text && <p>新鲜度：{explain.novelty_score_text}</p>}
          {display?.sources && display.sources.length > 0 && <p>来源：{display.sources.join('、')}</p>}
          {display?.similarEntities && display.similarEntities.length > 0 && (
            <p>相似实体：{display.similarEntities.join('、')}</p>
          )}
          {display?.kgReasonText && <p>关联原因：{display.kgReasonText}</p>}
        </div>
      )}
    </div>
  )
}
