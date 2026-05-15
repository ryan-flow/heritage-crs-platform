import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/auth-store'
import AppLayout from './components/layout/AppLayout'
import AdminLayout from './components/layout/AdminLayout'
import LoginPage from './pages/auth/LoginPage'
import HomePage from './pages/home/HomePage'
import AiChatPage from './pages/ai/AiChatPage'
import ContentListPage from './pages/content/ContentListPage'
import ContentDetailPage from './pages/content/ContentDetailPage'
import ActivityListPage from './pages/activity/ActivityListPage'
import ActivityDetailPage from './pages/activity/ActivityDetailPage'
import ActivityRegisterPage from './pages/activity/ActivityRegisterPage'
import DiscussionListPage from './pages/discussion/DiscussionListPage'
import DiscussionDetailPage from './pages/discussion/DiscussionDetailPage'
import ProfilePage from './pages/profile/ProfilePage'
import PreferencesPage from './pages/preferences/PreferencesPage'
import PlacesPage from './pages/places/PlacesPage'
import HistoryPage from './pages/history/HistoryPage'
import CulturePage from './pages/culture/CulturePage'
import HeritageDetailPage from './pages/culture/HeritageDetailPage'
import AdminDashboard from './pages/admin/DashboardPage'
import AdminContent from './pages/admin/ContentManagePage'
import AdminActivity from './pages/admin/ActivityManagePage'
import AdminTopic from './pages/admin/TopicManagePage'
import AdminUser from './pages/admin/UserManagePage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuthStore()
  if (!isLoggedIn()) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { session } = useAuthStore()
  if (!session || session.role !== 'admin') return <Navigate to="/" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
        <Route index element={<AdminDashboard />} />
        <Route path="contents" element={<AdminContent />} />
        <Route path="activities" element={<AdminActivity />} />
        <Route path="topics" element={<AdminTopic />} />
        <Route path="users" element={<AdminUser />} />
      </Route>
      <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<HomePage />} />
        <Route path="ai" element={<AiChatPage />} />
        <Route path="content" element={<ContentListPage />} />
        <Route path="content/:id" element={<ContentDetailPage />} />
        <Route path="activity" element={<ActivityListPage />} />
        <Route path="activity/:id" element={<ActivityDetailPage />} />
        <Route path="activity/:id/register" element={<ActivityRegisterPage />} />
        <Route path="discussion" element={<DiscussionListPage />} />
        <Route path="discussion/:id" element={<DiscussionDetailPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="preferences" element={<PreferencesPage />} />
        <Route path="places" element={<PlacesPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="culture" element={<CulturePage />} />
        <Route path="culture/:id" element={<HeritageDetailPage />} />
      </Route>
    </Routes>
  )
}
