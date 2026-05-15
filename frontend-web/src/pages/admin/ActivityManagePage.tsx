import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, MapPin, Calendar } from 'lucide-react'
import { apiRequest, buildImageUrl } from '../../lib/api'
import { Activity } from '../../types'

const statusLabels: Record<string, string> = { open: '报名中', closed: '已结束', full: '已满' }

export default function ActivityManagePage() {
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-activities', search],
    queryFn: () => apiRequest<{ code: number; data: Activity[] }>(`/admin/activities?search=${search}`),
  })

  const activities = (data?.data || []) as Activity[]

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">活动管理</h2>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/20" placeholder="搜索活动..." />
      </div>

      {isLoading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-white rounded-xl animate-pulse border border-gray-100" />)}</div>
      ) : (
        <div className="space-y-2">
          {activities.map(item => (
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
                    <span className={`text-xs px-1.5 py-0.5 rounded ${item.status === 'open' ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'}`}>
                      {statusLabels[item.status] || item.status}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                    <span className="flex items-center gap-1"><MapPin size={12} /> {item.location}</span>
                    <span className="flex items-center gap-1"><Calendar size={12} /> {item.start_time?.slice(0, 10)}</span>
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
