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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally { setLoading(false); }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      if (isRegister) {
        const res = await apiRequest<ApiResponse<{ userId: number }>>('/auth/register', {
          method: 'POST',
          data: { username, password, nickname: nickname || username },
        });
        if (res.code === 0) { setIsRegister(false); setError('注册成功，请登录'); }
        else setError(res.message || '注册失败');
      } else {
        const res = await apiRequest<ApiResponse<Session>>('/auth/login', {
          method: 'POST', data: { username, password },
        });
        if (res.code === 0 && res.data) { setSession(res.data); navigate('/', { replace: true }); }
        else setError(res.message || '登录失败');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '网络错误');
    } finally { setLoading(false); }
  };

  const fillTest = () => {
    if (testAccount) { setUsername(testAccount.username); setPassword(testAccount.password); setError(''); }
  };

  return (
    <div className="text-white" style={{
      minHeight: '100vh',
      background: `radial-gradient(ellipse 120% 80% at 50% -10%, rgba(139,69,19,0.35) 0%, transparent 60%),
        radial-gradient(ellipse 100% 60% at 20% 90%, rgba(128,0,32,0.25) 0%, transparent 55%),
        radial-gradient(ellipse 80% 70% at 85% 70%, rgba(184,134,11,0.18) 0%, transparent 55%),
        linear-gradient(175deg, #1a0f07 0%, #2d1810 15%, #4a2816 30%, #5c3018 48%, #6b3a14 65%, #7a4012 82%, #8b4513 95%, #9c4e15 100%)`,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: '48rpx 24rpx', position: 'relative', overflow: 'hidden',
    }}>
      {/* Glow orbs */}
      <div style={{ position: 'absolute', width: 280, height: 280, left: '-10%', top: '-8%',
        background: 'radial-gradient(circle, rgba(200,80,40,0.22), transparent 70%)', filter: 'blur(90rpx)', borderRadius: '50%' }} />
      <div style={{ position: 'absolute', width: 240, height: 240, right: '-5%', bottom: '10%',
        background: 'radial-gradient(circle, rgba(218,165,32,0.16), transparent 70%)', filter: 'blur(90rpx)', borderRadius: '50%' }} />

      {/* Floating clouds / xiangyun */}
      {['☁','✦','◈','☁','✦'].map((s, i) => (
        <span key={i} style={{
          position: 'absolute', fontSize: i % 2 ? 28 : 40,
          left: `${10 + i * 22}%`, top: `${5 + i * 18}%`,
          color: i % 3 === 0 ? '#d4a574' : i % 3 === 1 ? '#c9965a' : '#e8c88b',
          opacity: 0.08 + i * 0.025, animation: `floatCloud ${7 + i * 3}s ease-in-out infinite`,
          animationDelay: `${i * 2}s`,
        }}>{s}</span>
      ))}

      {/* Huiwen top border */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4,
        background: 'repeating-linear-gradient(90deg, rgba(212,175,86,0.25) 0 12rpx, transparent 12rpx 24rpx)' }} />

      {/* Rotating rings around digital human */}
      <div style={{ position: 'relative', marginBottom: 24 }}>
        <div style={{
          width: 200, height: 200, borderRadius: '50%',
          border: '1px solid rgba(212,175,86,0.28)',
          animation: 'spin 18s linear infinite',
          boxShadow: '0 0 40rpx rgba(212,175,86,0.08), inset 0 0 40rpx rgba(212,175,86,0.04)',
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        }} />
        <div style={{
          width: 240, height: 240, borderRadius: '50%',
          border: '1px solid rgba(212,175,86,0.15)',
          animation: 'spin 24s linear infinite reverse',
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
        }} />
        {/* Ring sparks */}
        {['◆','✦','◇','✧'].map((s, i) => (
          <span key={i} style={{
            position: 'absolute',
            top: '50%', left: '50%',
            transform: `rotate(${i * 90}deg) translateY(-100px)`,
            color: '#e8c96a', fontSize: 10,
            textShadow: '0 0 12rpx rgba(212,175,86,0.5)',
            animation: `sparkPulse ${3 + i}s ease-in-out infinite`,
          }}>{s}</span>
        ))}

        <DigitalHumanModel variant="hero" mood="curious" size={160} />
      </div>

      {/* Brand */}
      <div className="text-center" style={{ marginBottom: 32 }}>
        <div className="seal-badge seal-badge-cinnabar" style={{
          margin: '0 auto 16rpx', display: 'inline-flex',
          background: 'linear-gradient(135deg, #b22222, #cd3333)',
          borderRadius: '4rpx', fontSize: 20, padding: '6rpx 20rpx',
          letterSpacing: '4rpx',
        }}>
          非遗
        </div>
        <h1 style={{
          fontSize: 42, fontWeight: 800, letterSpacing: '5rpx',
          textShadow: '0 2rpx 4rpx rgba(0,0,0,0.3), 0 0 30rpx rgba(212,175,86,0.15)',
          fontFamily: 'var(--font-serif)',
          margin: 0,
        }}>〖 中国非物质文化遗产 〗</h1>
        <p style={{ fontSize: 20, color: '#d4b896', letterSpacing: '3rpx', marginTop: 8 }}>
          黑塔伴你 · 探寻千年文化瑰宝
        </p>
      </div>

      {/* Feature Cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 32, width: '100%', maxWidth: 400 }}>
        {[
          { num: '壹', title: '智能推荐', desc: 'CRS精准匹配', color: '#8b5cf6' },
          { num: '贰', title: 'AI数字人', desc: '黑塔导览互动', color: '#ef4444' },
          { num: '叁', title: '非遗社区', desc: '分享传承之美', color: '#f59e0b' },
        ].map((f, i) => (
          <div key={i} style={{
            flex: 1, background: 'rgba(0,0,0,0.18)', borderRadius: '14rpx',
            borderLeft: `4rpx solid ${f.color}`, padding: '16rpx 14rpx',
          }}>
            <div style={{ fontSize: 18, color: f.color, fontFamily: 'var(--font-serif)', marginBottom: 4 }}>{f.num}</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#f0e0cc' }}>{f.title}</div>
            <div style={{ fontSize: 11, color: 'rgba(212,175,150,0.6)', marginTop: 2 }}>{f.desc}</div>
          </div>
        ))}
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: 400 }}>
        {error && (
          <div style={{
            padding: '14rpx 20rpx', borderRadius: 14, marginBottom: 16,
            background: error.includes('成功') ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)',
            color: error.includes('成功') ? '#86efac' : '#fca5a5',
            border: `1px solid ${error.includes('成功') ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}`,
            fontSize: 13, textAlign: 'center',
          }}>
            {error}
          </div>
        )}

        <input type="text" value={username} onChange={e => setUsername(e.target.value)}
          placeholder="用户名"
          style={inputStyle} required />

        <input type="password" value={password} onChange={e => setPassword(e.target.value)}
          placeholder="密码"
          style={inputStyle} required />

        {isRegister && (
          <input type="text" value={nickname} onChange={e => setNickname(e.target.value)}
            placeholder="昵称（选填）"
            style={inputStyle} />
        )}

        <button type="submit" disabled={loading}
          style={loginBtnStyle}>
          {loading ? '处理中...' : isRegister ? '注 册' : '登 录'}
        </button>
      </form>

      {/* Guest & Test account */}
      <div style={{ width: '100%', maxWidth: 400, marginTop: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button onClick={handleGuestLogin} disabled={loading}
          style={{
            ...inputStyle, background: 'rgba(255,250,240,0.07)', border: '1px solid rgba(212,175,86,0.22)',
            color: '#d4a574', textAlign: 'center', cursor: 'pointer', fontWeight: 600,
          }}>
          游客体验
        </button>

        {testAccount && (
          <button type="button" onClick={fillTest}
            style={{ fontSize: 12, color: 'rgba(212,167,116,0.6)', background: 'none', border: 'none',
              cursor: 'pointer', textAlign: 'center', letterSpacing: '1rpx' }}>
            快速填入测试账号：{testAccount.username} / {testAccount.password}
          </button>
        )}

        <button type="button"
          onClick={() => { setIsRegister(!isRegister); setError(''); }}
          style={{ fontSize: 13, color: 'rgba(212,167,116,0.7)', background: 'none',
            border: 'none', cursor: 'pointer', marginTop: 8 }}>
          {isRegister ? '已有账号？去登录' : '没有账号？去注册'}
        </button>
      </div>

      {/* Footer */}
      <p style={{
        marginTop: 40, fontSize: 18, color: 'rgba(212,175,116,0.5)',
        fontFamily: 'var(--font-serif)', letterSpacing: '2rpx',
      }}>
        「一问即达 · 懂非遗也懂你」
      </p>

      {/* Bottom huiwen */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
        background: 'repeating-linear-gradient(90deg, rgba(212,175,86,0.25) 0 12rpx, transparent 12rpx 24rpx)',
      }} />

      <style>{`
        @keyframes floatCloud {
          0%, 100% { transform: translateY(0) translateX(0); }
          33% { transform: translateY(-12rpx) translateX(8rpx); }
          66% { transform: translateY(6rpx) translateX(-4rpx); }
        }
        @keyframes sparkPulse {
          0%, 100% { opacity: 0.3; transform: rotate(var(--rot, 0deg)) translateY(-100px) scale(0.8); }
          50% { opacity: 0.8; transform: rotate(var(--rot, 0deg)) translateY(-100px) scale(1.2); }
        }
        @keyframes spin {
          from { transform: translate(-50%, -50%) rotate(0deg); }
          to { transform: translate(-50%, -50%) rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%', height: 48, borderRadius: 24, marginBottom: 12,
  background: 'rgba(255,250,240,0.07)', border: '1px solid rgba(212,175,86,0.22)',
  color: '#f0e0cc', fontSize: 15, padding: '0 20rpx', outline: 'none',
  boxSizing: 'border-box',
};

const loginBtnStyle: React.CSSProperties = {
  width: '100%', height: 50, borderRadius: 25, marginTop: 8,
  background: 'linear-gradient(135deg, #a52a2a 0%, #b22222 30%, #c93c3c 60%, #d4af37 100%)',
  color: '#fff', fontWeight: 700, fontSize: 17, letterSpacing: '4rpx',
  border: 'none', cursor: 'pointer',
  boxShadow: '0 4rpx 20rpx rgba(180,60,30,0.3), 0 0 30rpx rgba(212,175,86,0.12)',
};
