import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, LayoutDashboard, FileText, Calendar, MessageSquare, Users } from 'lucide-react';
import { PageTransition } from '../ui/PageTransition';

const adminTabs = [
  { path: '/admin', label: '看板', icon: LayoutDashboard },
  { path: '/admin/contents', label: '内容', icon: FileText },
  { path: '/admin/activities', label: '活动', icon: Calendar },
  { path: '/admin/topics', label: '帖子', icon: MessageSquare },
  { path: '/admin/users', label: '用户', icon: Users },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-parchment">
      <header className="sticky top-0 z-40 glass-card-elevated border-b border-ink-border/30 rounded-none">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-4 h-14">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="p-1.5 hover:bg-parchment-dark/50 rounded-lg transition-colors">
              <ArrowLeft size={20} className="text-ink-secondary" />
            </button>
            <h1 className="text-base font-serif font-bold text-ink">管理后台</h1>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex gap-1 -mb-px overflow-x-auto scrollbar-hide">
            {adminTabs.map(tab => {
              const Icon = tab.icon;
              const isActive = location.pathname === tab.path || (tab.path !== '/admin' && location.pathname.startsWith(tab.path));
              return (
                <button
                  key={tab.path}
                  onClick={() => navigate(tab.path)}
                  className={`flex items-center gap-1.5 px-3 py-2.5 text-sm border-b-2 transition-all shrink-0 ${
                    isActive
                      ? 'border-cinnabar-700 text-cinnabar-700 font-medium'
                      : 'border-transparent text-ink-muted hover:text-ink-secondary'
                  }`}
                >
                  <Icon size={15} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto p-4">
        <PageTransition key={location.pathname}>
          <Outlet />
        </PageTransition>
      </main>
    </div>
  );
}
