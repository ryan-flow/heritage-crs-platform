import { useQuery } from '@tanstack/react-query'
import { Users, FileText, Calendar, MessageSquare, BookOpen, TrendingUp } from 'lucide-react'
import { apiRequest } from '../../lib/api'
import { DashboardStats } from '../../types'

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: () => apiRequest<{ code: number; data: DashboardStats }>('/stats/dashboard'),
  })

  const stats = data?.data

  const cards = stats ? [
    { label: '总用户', value: stats.total_users, icon: Users, color: 'bg-blue-500' },
    { label: '内容总数', value: stats.total_contents, icon: FileText, color: 'bg-heritage-500' },
    { label: '活动总数', value: stats.total_activities, icon: Calendar, color: 'bg-green-500' },
    { label: '帖子总数', value: stats.total_discussions, icon: MessageSquare, color: 'bg-amber-500' },
    { label: '知识条目', value: stats.total_knowledge_base, icon: BookOpen, color: 'bg-purple-500' },
    { label: '今日新增', value: stats.users_today, icon: TrendingUp, color: 'bg-red-500' },
  ] : []

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">数据概览</h2>
      {isLoading ? (
        <div className="grid grid-cols-3 gap-3">
          {[1,2,3,4,5,6].map(i => <div key={i} className="h-24 bg-white rounded-xl animate-pulse border border-gray-100" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {cards.map((card, i) => {
            const Icon = card.icon
            return (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 ${card.color} rounded-lg flex items-center justify-center`}>
                    <Icon size={20} className="text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-800">{card.value}</p>
                    <p className="text-xs text-gray-500">{card.label}</p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">快速操作</h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: '管理内容', path: '/admin/contents' },
            { label: '管理活动', path: '/admin/activities' },
            { label: '管理帖子', path: '/admin/topics' },
            { label: '管理用户', path: '/admin/users' },
          ].map((link, i) => (
            <a key={i} href={link.path}
              className="text-center py-2.5 bg-gray-50 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors">
              {link.label}
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
