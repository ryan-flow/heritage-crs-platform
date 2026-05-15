import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, User, Shield, Ban } from 'lucide-react'
import { apiRequest } from '../../lib/api'
import { User as UserType } from '../../types'

export default function UserManagePage() {
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', search],
    queryFn: () => apiRequest<{ code: number; data: UserType[] }>(`/admin/users?search=${search}`),
  })

  const users = (data?.data || []) as UserType[]

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">用户管理</h2>

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input type="text" value={search} onChange={e => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/20" placeholder="搜索用户..." />
      </div>

      {isLoading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-white rounded-xl animate-pulse border border-gray-100" />)}</div>
      ) : (
        <div className="space-y-2">
          {users.map(item => (
            <div key={item.id} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-medium">
                  {(item.nickname || item.username || '?')[0]}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium text-gray-800">{item.nickname || item.username}</h3>
                    {item.role === 'admin' && (
                      <span className="text-xs bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded flex items-center gap-1">
                        <Shield size={10} /> 管理员
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">@{item.username} · 置信度 {Math.round(item.confidence_score || 0)}%</p>
                  {item.preferred_heritage_types && (
                    <p className="text-xs text-gray-400 mt-0.5">偏好：{item.preferred_heritage_types.replace(/,/g, '、')}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
