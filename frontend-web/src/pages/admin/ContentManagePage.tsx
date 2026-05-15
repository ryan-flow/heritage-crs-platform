import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { apiRequest, buildImageUrl } from '../../lib/api'
import { ContentItem } from '../../types'

export default function ContentManagePage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-contents', filter, search],
    queryFn: () => apiRequest<{ code: number; data: ContentItem[] }>(`/admin/contents?status=${filter}&search=${search}`),
  })

  const reviewMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: string }) =>
      apiRequest(`/admin/contents/${id}/review`, { method: 'POST', data: { action } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-contents'] }),
  })

  const contents = (data?.data || []) as ContentItem[]

  const statusColors: Record<string, string> = {
    published: 'text-green-600 bg-green-50', draft: 'text-gray-500 bg-gray-50', pending: 'text-amber-600 bg-amber-50', rejected: 'text-red-600 bg-red-50',
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">内容管理</h2>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/20" placeholder="搜索..." />
        </div>
        {['', 'published', 'draft', 'pending', 'rejected'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === s ? 'bg-cinnabar-800 text-white' : 'bg-white border border-gray-200 text-gray-600'}`}>
            {s || '全部'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-white rounded-xl animate-pulse border border-gray-100" />)}</div>
      ) : (
        <div className="space-y-2">
          {contents.map(item => (
            <div key={item.id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="flex items-start gap-3">
                {item.cover_url && (
                  <div className="w-12 h-12 shrink-0 rounded-lg overflow-hidden bg-gray-100">
                    <img src={buildImageUrl(item.cover_url)} alt="" className="w-full h-full object-cover" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-gray-800">{item.title}</h3>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${statusColors[item.status || ''] || 'bg-gray-50 text-gray-500'}`}>
                      {item.status || 'unknown'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {item.category} · {item.region} · 质量 {item.quality_score?.toFixed(2)}
                  </p>
                  <div className="flex gap-1 mt-2">
                    {item.status === 'pending' && (
                      <>
                        <button onClick={() => reviewMutation.mutate({ id: item.id, action: 'approve' })}
                          className="flex items-center gap-1 text-xs px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100">
                          <CheckCircle size={12} /> 通过
                        </button>
                        <button onClick={() => reviewMutation.mutate({ id: item.id, action: 'reject' })}
                          className="flex items-center gap-1 text-xs px-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100">
                          <XCircle size={12} /> 拒绝
                        </button>
                      </>
                    )}
                    {item.status === 'published' && (
                      <button onClick={() => reviewMutation.mutate({ id: item.id, action: 'draft' })}
                        className="flex items-center gap-1 text-xs px-2 py-1 bg-gray-50 text-gray-600 rounded hover:bg-gray-100">
                        <AlertCircle size={12} /> 下架
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
