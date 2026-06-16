import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, X, ImageIcon } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';

const AVAILABLE_TAGS = [
  '戏曲', '工艺', '节俗', '求科普', '活动反馈',
  '传统音乐', '传统美术', '传统技艺', '民俗',
];

export default function DiscussionCreatePage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [coverUrl, setCoverUrl] = useState('');
  const [coverPreview, setCoverPreview] = useState('');
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const API_BASE = '/api/v1';

  const getSessionHeaders = () => {
    try {
      const raw = localStorage.getItem('session');
      const session = raw ? JSON.parse(raw) : null;
      const headers: Record<string, string> = {};
      if (session?.userId) headers['X-User-Id'] = String(session.userId);
      if (session?.token) headers['X-Admin-Token'] = session.token;
      return headers;
    } catch {
      return {} as Record<string, string>;
    }
  };

  const handleTagToggle = (tag: string) => {
    setSelectedTags((prev) => {
      if (prev.includes(tag)) return prev.filter((t) => t !== tag);
      if (prev.length >= 3) return prev;
      return [...prev, tag];
    });
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const headers = getSessionHeaders();
      const res = await fetch(`${API_BASE}/discussion/upload-cover`, {
        method: 'POST',
        headers,
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(`上传失败: HTTP ${res.status} ${text.slice(0, 100)}`);
      }

      const json = await res.json();
      if (json.code === 0 && json.data?.url) {
        setCoverUrl(json.data.url);
        const fullUrl = json.data.url.startsWith('http')
          ? json.data.url
          : `${API_BASE.replace('/api/v1', '')}${json.data.url}`;
        setCoverPreview(fullUrl);
      } else {
        throw new Error(json.message || '上传返回异常');
      }
    } catch (err: any) {
      setError(err.message || '封面上传失败');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeCover = () => {
    setCoverUrl('');
    setCoverPreview('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async () => {
    setError('');

    if (!title.trim()) {
      setError('请输入标题');
      return;
    }
    if (!content.trim() || content.trim().length < 20) {
      setError('内容至少需要 20 个字');
      return;
    }

    setSubmitting(true);

    try {
      const res = await apiRequest<{ code: number; message?: string; data?: { id: number } }>(
        '/discussion/topics',
        {
          method: 'POST',
          data: {
            title: title.trim(),
            content: content.trim(),
            tags: selectedTags,
            cover_url: coverUrl || undefined,
          },
        },
      );

      if (res.code === 0) {
        navigate('/discussion', { replace: true });
      } else {
        setError(res.message || '发布失败，请重试');
      }
    } catch (err: any) {
      setError(err.message || '网络错误，请稍后再试');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pb-28 px-5">
      {/* ── Back Button ── */}
      <div className="mt-3 mb-3">
        <InkButton variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={15} /> 返回
        </InkButton>
      </div>

      {/* ── Hero Banner ── */}
      <div
        className="rise-in relative overflow-hidden mb-6 p-5 rounded-[36px]"
        style={{
          background: 'linear-gradient(135deg, #6B3A2A 0%, #9B4F3C 50%, #b85d47 100%)',
          boxShadow: '0 22px 46px rgba(60, 20, 10, 0.22)',
        }}
      >
        <div className="absolute -top-10 -right-8 w-36 h-36 rounded-full bg-white/6" />
        <div className="absolute -bottom-6 left-10 w-20 h-20 rounded-full bg-white/4" />

        <span className="relative inline-block px-3.5 py-1 rounded-full text-xs font-semibold tracking-wide bg-white/12 text-[#ffe1bc] mb-2.5">
          发起讨论
        </span>
        <h1 className="relative font-serif text-[26px] font-extrabold text-[#fff8f1] leading-tight mb-1">
          发起讨论
        </h1>
        <p className="relative text-sm text-white/85 font-sans">
          分享你的见解，与同好一起交流非遗文化
        </p>
      </div>

      {/* ── Error Banner ── */}
      {error && (
        <div className="mb-4 p-3.5 rounded-2xl bg-cinnabar-50 border border-cinnabar-200/40">
          <p className="text-sm text-cinnabar-600 font-sans">{error}</p>
        </div>
      )}

      {/* ── Form Card ── */}
      <GlassCard elevated className="p-5 space-y-5">
        {/* Title */}
        <div>
          <label className="block font-serif text-sm font-bold text-ink mb-2">
            标题 <span className="text-cinnabar-500">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="请输入讨论标题..."
            maxLength={100}
            className="w-full h-11 rounded-xl px-4 bg-parchment border border-parchment-dark/60 text-sm text-ink placeholder:text-ink-muted/50 font-sans outline-none focus:border-cinnabar-200/60 focus:ring-2 focus:ring-cinnabar-800/10 transition-colors"
          />
          <p className="text-[11px] text-ink-muted mt-1.5 font-sans">
            {title.length}/100
          </p>
        </div>

        {/* Content */}
        <div>
          <label className="block font-serif text-sm font-bold text-ink mb-2">
            内容 <span className="text-cinnabar-500">*</span>
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="分享你的想法...（至少 20 个字）"
            rows={6}
            className="w-full rounded-xl p-4 bg-parchment border border-parchment-dark/60 text-sm text-ink placeholder:text-ink-muted/50 font-sans outline-none focus:border-cinnabar-200/60 focus:ring-2 focus:ring-cinnabar-800/10 transition-colors resize-none"
          />
          <p className="text-[11px] text-ink-muted mt-1.5 font-sans">
            {content.length}/20 最少字数
          </p>
        </div>

        {/* Tags */}
        <div>
          <label className="block font-serif text-sm font-bold text-ink mb-2">
            标签 <span className="text-[11px] text-ink-muted font-normal font-sans">（最多 3 个）</span>
          </label>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_TAGS.map((tag) => {
              const isActive = selectedTags.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleTagToggle(tag)}
                  disabled={!isActive && selectedTags.length >= 3}
                  className={`chip !min-h-0 !py-1.5 !px-3.5 text-xs transition-all ${
                    isActive ? 'chip-active' : ''
                  } ${!isActive && selectedTags.length >= 3 ? 'opacity-35 pointer-events-none' : ''}`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        {/* Cover Image Upload */}
        <div>
          <label className="block font-serif text-sm font-bold text-ink mb-2">
            封面图片 <span className="text-[11px] text-ink-muted font-normal font-sans">（可选）</span>
          </label>

          {coverPreview ? (
            <div className="relative w-full h-40 rounded-2xl overflow-hidden bg-parchment-dark">
              <img
                src={coverPreview}
                alt="封面预览"
                className="w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={removeCover}
                className="absolute top-2 right-2 w-7 h-7 rounded-full bg-ink/60 text-white flex items-center justify-center hover:bg-ink/80 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full h-32 rounded-2xl border-2 border-dashed border-parchment-dark/60 bg-parchment flex flex-col items-center justify-center gap-2 hover:border-cinnabar-200/60 hover:bg-cinnabar-50/40 transition-colors"
            >
              {uploading ? (
                <>
                  <svg className="animate-spin h-6 w-6 text-ink-muted" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span className="text-xs text-ink-muted font-sans">上传中...</span>
                </>
              ) : (
                <>
                  <div className="w-10 h-10 rounded-full bg-parchment-dark/50 flex items-center justify-center">
                    <ImageIcon size={20} className="text-ink-muted/50" />
                  </div>
                  <span className="text-xs text-ink-muted font-sans">点击上传封面图片</span>
                </>
              )}
            </button>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Submit Button */}
        <InkButton
          variant="primary"
          size="lg"
          loading={submitting}
          disabled={submitting}
          onClick={handleSubmit}
          className="w-full !rounded-2xl"
        >
          发布
        </InkButton>
      </GlassCard>
    </div>
  );
}
