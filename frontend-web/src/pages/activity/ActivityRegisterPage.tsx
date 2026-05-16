import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, ClipboardCheck } from 'lucide-react';
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
      setError('网络错误，请检查连接后重试');
    } finally {
      setLoading(false);
    }
  };

  /* ── Success State ── */
  if (done) {
    return (
      <div className="px-4 py-16 text-center">
        <div className="w-[72px] h-[72px] rounded-full bg-jade-50 border-2 border-jade-200/40 flex items-center justify-center mx-auto mb-4">
          <CheckCircle size={36} className="text-jade-500" />
        </div>
        <h2 className="text-xl font-serif font-bold text-ink mb-1">报名成功</h2>
        <p className="text-sm text-ink-secondary leading-relaxed">
          我们会通过站内信通知你活动详情
        </p>
        <InkButton variant="outline" onClick={() => navigate('/activity')} className="mt-6">
          返回活动列表
        </InkButton>
      </div>
    );
  }

  /* ── Form State ── */
  return (
    <div className="px-4 py-5">
      {/* Back Navigation */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-ink-secondary mb-5 hover:text-ink transition-colors"
      >
        <ArrowLeft size={16} /> 返回
      </button>

      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 rounded-full bg-cinnabar-50 flex items-center justify-center shrink-0">
          <ClipboardCheck size={18} className="text-cinnabar-500" />
        </div>
        <h1 className="text-xl font-serif font-bold text-ink">活动报名</h1>
      </div>

      {/* Form Card */}
      <GlassCard elevated className="p-5">
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Error Banner */}
          {error && (
            <div className="text-sm text-cinnabar-600 bg-cinnabar-50 border border-cinnabar-200/40 p-3.5 rounded-xl leading-relaxed">
              {error}
            </div>
          )}

          {/* Contact Input */}
          <div>
            <label className="block text-xs font-medium text-ink-secondary mb-1.5 ml-1">
              联系方式 <span className="text-cinnabar-500">*</span>
            </label>
            <input
              type="text"
              value={contact}
              onChange={e => setContact(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl text-sm text-ink bg-parchment border border-gold-200/30 outline-none transition-colors focus:border-cinnabar-200/60 focus:ring-2 focus:ring-cinnabar-800/10 placeholder:text-ink-muted/50"
              placeholder="手机号或邮箱"
              required
            />
          </div>

          {/* Notes Textarea */}
          <div>
            <label className="block text-xs font-medium text-ink-secondary mb-1.5 ml-1">
              备注 <span className="text-ink-muted font-normal">（选填）</span>
            </label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={3}
              className="w-full px-3.5 py-2.5 rounded-xl text-sm text-ink bg-parchment border border-gold-200/30 outline-none transition-colors focus:border-cinnabar-200/60 focus:ring-2 focus:ring-cinnabar-800/10 placeholder:text-ink-muted/50 resize-none"
              placeholder="有什么需要提前了解的？"
            />
          </div>

          {/* Submit Button */}
          <InkButton
            type="submit"
            variant="primary"
            loading={loading}
            className="w-full !py-3 !text-sm"
          >
            确认报名
          </InkButton>
        </form>
      </GlassCard>
    </div>
  );
}
