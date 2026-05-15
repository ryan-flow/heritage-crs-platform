import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';

export default function ActivityRegisterPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const [contact, setContact] = useState('');
  const [notes, setNotes] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await apiRequest<{ code: number }>(`/events/${id}/register`, {
        method: 'POST',
        data: { user_id: session?.userId, remark: [contact, notes].filter(Boolean).join(' | ') },
      });
      if (res.code === 0) setDone(true);
      else setError('报名失败，请重试');
    } catch {
      setError('网络错误');
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <div className="px-4 py-20 text-center">
        <div className="w-16 h-16 bg-jade-50 rounded-full flex items-center justify-center mx-auto mb-3">
          <CheckCircle size={40} className="text-jade-500" />
        </div>
        <h2 className="text-lg font-serif font-bold text-ink">报名成功</h2>
        <p className="text-sm text-ink-secondary mt-1">我们会通过站内信通知你活动详情</p>
        <InkButton onClick={() => navigate('/activity')} className="mt-6">
          返回活动列表
        </InkButton>
      </div>
    );
  }

  return (
    <div className="px-4 py-5">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary mb-4 hover:text-ink transition-colors">
        <ArrowLeft size={16} /> 返回
      </button>
      <h1 className="text-xl font-serif font-bold text-ink mb-4">活动报名</h1>

      <GlassCard elevated className="p-5">
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="text-sm text-cinnabar-600 bg-cinnabar-50 p-3 rounded-xl">{error}</div>
          )}
          <div>
            <label className="block text-xs font-medium text-ink-secondary mb-1 ml-1">联系方式</label>
            <input
              type="text"
              value={contact}
              onChange={e => setContact(e.target.value)}
              className="w-full px-3.5 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15"
              placeholder="手机号或邮箱"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-ink-secondary mb-1 ml-1">备注</label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3.5 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 resize-none"
              placeholder="选填，有什么需要提前了解的？"
            />
          </div>
          <InkButton type="submit" loading={loading} className="w-full !py-3 !text-sm">
            确认报名
          </InkButton>
        </form>
      </GlassCard>
    </div>
  );
}
