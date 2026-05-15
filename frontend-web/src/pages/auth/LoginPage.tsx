import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { ApiResponse, Session } from '../../types';
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
      .then((res) => { if (res.code === 0 && res.data) setTestAccount(res.data); })
      .catch(() => {});
  }, []);

  const handleGuestLogin = async () => {
    setError(''); setLoading(true);
    try {
      const res = await apiRequest<ApiResponse<Session>>('/auth/guest', { method: 'POST' });
      if (res.code === 0 && res.data) { setSession(res.data); navigate('/', { replace: true }); }
    } catch (err: unknown) { setError(err instanceof Error ? err.message : '网络错误'); }
    finally { setLoading(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      if (isRegister) {
        const res = await apiRequest<ApiResponse<{ userId: number }>>('/auth/register', {
          method: 'POST', data: { username, password, nickname: nickname || username },
        });
        if (res.code === 0) { setIsRegister(false); setError('注册成功，请登录'); }
        else setError(res.message || '注册失败');
      } else {
        const res = await apiRequest<ApiResponse<Session>>('/auth/login', { method: 'POST', data: { username, password } });
        if (res.code === 0 && res.data) { setSession(res.data); navigate('/', { replace: true }); }
        else setError(res.message || '登录失败');
      }
    } catch (err: unknown) { setError(err instanceof Error ? err.message : '网络错误'); }
    finally { setLoading(false); }
  };

  const fillTest = () => {
    if (testAccount) { setUsername(testAccount.username); setPassword(testAccount.password); setError(''); }
  };

  const inputCls = "w-full h-12 rounded-full px-5 text-[15px] text-white/85 placeholder:text-white/40 bg-white/[0.07] border border-white/[0.12] outline-none focus:border-amber-400/40 transition-colors box-border";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12 relative overflow-hidden text-white"
      style={{ background: 'linear-gradient(175deg, #1a0f07 0%, #2d1810 15%, #4a2816 30%, #5c3018 48%, #6b3a14 65%, #7a4012 82%, #8b4513 95%, #9c4e15 100%)' }}>

      {/* Glow orbs — pointer-events-none so they don't block clicks */}
      <div className="absolute w-72 h-72 -left-10 -top-10 rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(200,80,40,0.22), transparent 70%)', filter: 'blur(90px)' }} />
      <div className="absolute w-60 h-60 -right-5 bottom-10 rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(218,165,32,0.16), transparent 70%)', filter: 'blur(90px)' }} />

      {/* Huiwen borders */}
      <div className="absolute top-0 left-0 right-0 h-1 pointer-events-none"
        style={{ background: 'repeating-linear-gradient(90deg, rgba(212,175,86,0.25) 0 12px, transparent 12px 24px)' }} />
      <div className="absolute bottom-0 left-0 right-0 h-1 pointer-events-none"
        style={{ background: 'repeating-linear-gradient(90deg, rgba(212,175,86,0.25) 0 12px, transparent 12px 24px)' }} />

      <div className="relative z-10 w-full max-w-sm flex flex-col items-center">
        {/* Rings + Digital Human */}
        <div className="relative mb-6 flex items-center justify-center">
          <div className="absolute w-[200px] h-[200px] rounded-full border border-amber-300/25 animate-[spin_18s_linear_infinite]"
            style={{ boxShadow: '0 0 40px rgba(212,175,86,0.08), inset 0 0 40px rgba(212,175,86,0.04)' }} />
          <div className="absolute w-[240px] h-[240px] rounded-full border border-amber-300/15 animate-[spin_24s_linear_infinite_reverse]" />
          <DigitalHumanModel variant="hero" mood="curious" size={160} />
        </div>

        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex mx-auto mb-4 px-5 py-1.5 rounded text-base font-bold tracking-[4px]"
            style={{ background: 'linear-gradient(135deg, #b22222, #cd3333)' }}>
            非遗
          </div>
          <h1 className="text-[42px] font-extrabold tracking-[5px] mt-0 mb-2 font-[var(--font-serif)]"
            style={{ textShadow: '0 2px 4px rgba(0,0,0,0.3), 0 0 30px rgba(212,175,86,0.15)' }}>
            〖 中国非物质文化遗产 〗
          </h1>
          <p className="text-base text-amber-200/70 tracking-[3px]">黑塔伴你 · 探寻千年文化瑰宝</p>
        </div>

        {/* Feature Cards */}
        <div className="flex gap-3 mb-8 w-full">
          {[
            { num: '壹', title: '智能推荐', desc: 'CRS精准匹配', color: '#8b5cf6' },
            { num: '贰', title: 'AI数字人', desc: '黑塔导览互动', color: '#ef4444' },
            { num: '叁', title: '非遗社区', desc: '分享传承之美', color: '#f59e0b' },
          ].map((f, i) => (
            <div key={i} className="flex-1 rounded-xl p-3.5 bg-black/20 border-l-[4px]" style={{ borderLeftColor: f.color }}>
              <div className="text-lg font-[var(--font-serif)] mb-1" style={{ color: f.color }}>{f.num}</div>
              <div className="text-[13px] font-bold text-amber-100/90">{f.title}</div>
              <div className="text-[11px] text-amber-100/40 mt-0.5">{f.desc}</div>
            </div>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="w-full space-y-3">
          {error && (
            <div className={`p-3.5 rounded-2xl text-center text-sm ${error.includes('成功') ? 'bg-green-500/15 text-green-300 border border-green-500/30' : 'bg-red-500/15 text-red-300 border border-red-500/30'}`}>
              {error}
            </div>
          )}

          <input type="text" value={username} onChange={e => setUsername(e.target.value)}
            placeholder="用户名" className={inputCls} required />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="密码" className={inputCls} required />
          {isRegister && (
            <input type="text" value={nickname} onChange={e => setNickname(e.target.value)}
              placeholder="昵称（选填）" className={inputCls} />
          )}

          <button type="submit" disabled={loading}
            className="w-full h-[50px] rounded-full font-bold text-[17px] tracking-[4px] text-white border-none cursor-pointer mt-2"
            style={{
              background: 'linear-gradient(135deg, #a52a2a 0%, #b22222 30%, #c93c3c 60%, #d4af37 100%)',
              boxShadow: '0 4px 20px rgba(180,60,30,0.3), 0 0 30px rgba(212,175,86,0.12)',
            }}>
            {loading ? '处理中...' : isRegister ? '注 册' : '登 录'}
          </button>
        </form>

        {/* Guest & Test */}
        <div className="w-full mt-4 space-y-2.5">
          <button onClick={handleGuestLogin} disabled={loading}
            className="w-full h-12 rounded-full text-amber-300/80 font-semibold bg-white/[0.07] border border-amber-300/20 cursor-pointer hover:bg-white/[0.12] transition-colors">
            游客体验
          </button>
          {testAccount && (
            <button onClick={fillTest}
              className="w-full text-xs text-amber-200/40 bg-transparent border-none cursor-pointer tracking-[1px]">
              填入测试账号：{testAccount.username} / {testAccount.password}
            </button>
          )}
          <button onClick={() => { setIsRegister(!isRegister); setError(''); }}
            className="w-full text-sm text-amber-200/60 bg-transparent border-none cursor-pointer mt-2">
            {isRegister ? '已有账号？去登录' : '没有账号？去注册'}
          </button>
        </div>

        {/* Footer */}
        <p className="mt-10 text-base text-amber-200/30 font-[var(--font-serif)] tracking-[2px]">
          「一问即达 · 懂非遗也懂你」
        </p>
      </div>
    </div>
  );
}
