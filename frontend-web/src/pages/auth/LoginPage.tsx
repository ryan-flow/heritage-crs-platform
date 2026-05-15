import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { ApiResponse, Session } from '../../types';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';
import { DigitalHumanModel } from '../../components/digital-human/DigitalHumanModel';
import '../../components/digital-human/DigitalHumanModel.css';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [testAccount, setTestAccount] = useState<{ username: string; password: string } | null>(null);
  const navigate = useNavigate();
  const { setSession } = useAuthStore();

  useEffect(() => {
    apiRequest<ApiResponse<{ username: string; password: string }>>('/auth/test-account')
      .then((res) => {
        if (res.code === 0 && res.data) setTestAccount(res.data);
      })
      .catch(() => {});
  }, []);

  const handleGuestLogin = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await apiRequest<ApiResponse<Session>>('/auth/guest', { method: 'POST' });
      if (res.code === 0 && res.data) {
        setSession(res.data);
        navigate('/', { replace: true });
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        const res = await apiRequest<ApiResponse<{ userId: number }>>('/auth/register', {
          method: 'POST',
          data: { username, password, nickname: nickname || username },
        });
        if (res.code === 0) {
          setIsRegister(false);
          setError('注册成功，请登录');
        } else {
          setError(res.message || '注册失败');
        }
      } else {
        const res = await apiRequest<ApiResponse<Session>>('/auth/login', {
          method: 'POST',
          data: { username, password },
        });
        if (res.code === 0 && res.data) {
          setSession(res.data);
          navigate('/', { replace: true });
        } else {
          setError(res.message || '登录失败');
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally {
      setLoading(false);
    }
  };

  const fillTest = () => {
    if (testAccount) {
      setUsername(testAccount.username);
      setPassword(testAccount.password);
      setError('');
    }
  };

  return (
    <div className="min-h-screen ink-gradient flex items-center justify-center p-4 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-gold-100/30 rounded-full blur-3xl" />
      <div className="absolute bottom-20 right-10 w-80 h-80 bg-cinnabar-50/20 rounded-full blur-3xl" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-jade-50/20 rounded-full blur-3xl" />

      <div className="w-full max-w-sm relative z-10">
        {/* Logo & Brand */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center mb-4 scale-75">
            <DigitalHumanModel variant="hero" mood="curious" size={280} />
          </div>
          <h1 className="text-2xl font-serif text-ink tracking-wider">黑塔</h1>
          <p className="text-sm text-ink-muted mt-1.5 font-sans">中国非遗文化数字平台</p>
        </div>

        {/* Form Card */}
        <GlassCard elevated className="p-6">
          <h2 className="text-lg font-serif text-ink text-center mb-5">
            {isRegister ? '创建账号' : '欢迎回来'}
          </h2>

          {error && (
            <div className={`text-sm p-3 rounded-lg mb-4 ${
              error.includes('成功') ? 'bg-jade-50 text-jade-500 border border-jade-100' : 'bg-cinnabar-50 text-cinnabar-700 border border-cinnabar-100'
            }`}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div>
              <label className="block text-xs font-medium text-ink-secondary mb-1 ml-1">用户名</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-parchment border border-ink-border rounded-xl text-sm text-ink placeholder-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 focus:border-cinnabar-300 transition-all font-sans"
                placeholder="请输入用户名"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-secondary mb-1 ml-1">密码</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-parchment border border-ink-border rounded-xl text-sm text-ink placeholder-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 focus:border-cinnabar-300 transition-all font-sans"
                placeholder="请输入密码"
                required
              />
            </div>

            {isRegister && (
              <div>
                <label className="block text-xs font-medium text-ink-secondary mb-1 ml-1">昵称</label>
                <input
                  type="text"
                  value={nickname}
                  onChange={e => setNickname(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-parchment border border-ink-border rounded-xl text-sm text-ink placeholder-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-cinnabar-800/15 focus:border-cinnabar-300 transition-all font-sans"
                  placeholder="选填"
                />
              </div>
            )}

            <InkButton type="submit" loading={loading} className="w-full !py-3 !text-sm">
              {isRegister ? '注 册' : '登 录'}
            </InkButton>
          </form>

          {/* Guest login */}
          <div className="mt-4 pt-4 border-t border-ink-border/50 space-y-2.5">
            <InkButton variant="outline" onClick={handleGuestLogin} loading={loading} className="w-full !py-2.5 !text-sm">
              游客体验
            </InkButton>

            {testAccount && (
              <button
                type="button"
                onClick={fillTest}
                className="w-full text-xs text-ink-muted hover:text-ink-secondary transition-colors py-1.5"
              >
                快速填入测试账号：{testAccount.username} / {testAccount.password}
              </button>
            )}
          </div>

          <p className="text-center text-xs text-ink-muted mt-4">
            {isRegister ? '已有账号？' : '没有账号？'}
            <button
              type="button"
              onClick={() => { setIsRegister(!isRegister); setError(''); }}
              className="text-cinnabar-700 hover:text-cinnabar-800 ml-1 font-medium transition-colors"
            >
              {isRegister ? '去登录' : '去注册'}
            </button>
          </p>
        </GlassCard>

        <p className="text-center text-xs text-ink-muted/60 mt-4 font-sans">
          {isRegister ? '注册即表示同意服务条款和隐私政策' : '基于CRS推荐与AI数字人的非遗文化传播系统'}
        </p>
      </div>
    </div>
  );
}
