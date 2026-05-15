import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, Trash2, Heart, MessageCircle } from 'lucide-react'
import { apiRequest } from '../../lib/api'
import { DiscussionTopic } from '../../types'

export default function TopicManagePage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-topics', search],
    queryFn: () => apiRequest<{ code: number; data: DiscussionTopic[] }>(`/admin/topics?search=${search}`),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiRequest(`/admin/topics/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-topics'] }),
  })

  const topics = (data?.data || []) as DiscussionTopic[]

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">帖子管理</h2>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/20" placeholder="搜索帖子..." />
      </div>

      {isLoading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-white rounded-xl animate-pulse border border-gray-100" />)}</div>
      ) : (
        <div className="space-y-2">
          {topics.map(item => (
            <div key={item.id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-800">{item.title}</h3>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{item.content?.slice(0, 200)}</p>
                  <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400">
                    <span>{item.nickname || '匿名'}</span>
                    <span className="flex items-center gap-1"><Heart size={12} /> {item.like_count || 0}</span>
                    <span className="flex items-center gap-1"><MessageCircle size={12} /> {item.comment_count || 0}</span>
                    <span>{item.created_at?.slice(0, 10)}</span>
                  </div>
                </div>
                <button onClick={() => { if (confirm('确认删除？')) deleteMutation.mutate(item.id) }}
                  className="p-2 hover:bg-red-50 rounded-lg text-gray-400 hover:text-red-500 transition-colors">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
