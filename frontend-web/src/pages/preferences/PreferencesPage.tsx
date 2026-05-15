import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';

const HERITAGE_TYPES = ['传统工艺', '戏曲音乐', '民俗节俗', '饮食医药', '民间文学', '传统美术', '传统体育'];
const SCENE_TYPES = ['阅读学习', '实地体验', '亲子互动', '学术研究', '休闲娱乐'];
const REGIONS = ['北京', '上海', '广东', '江苏', '浙江', '四川', '陕西', '云南', '福建', '湖南', '湖北', '河南', '山东', '安徽'];

export default function PreferencesPage() {
  const navigate = useNavigate();
  const { session } = useAuthStore();
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [selectedScenes, setSelectedScenes] = useState<string[]>([]);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (session?.userId) {
      apiRequest<{ code: number; data: { preferred_heritage_types?: string[]; preferred_scene_types?: string[]; preferred_regions?: string[] } }>(`/users/${session.userId}`)
        .then(res => {
          if (res.data) {
            const h = res.data.preferred_heritage_types;
            const s = res.data.preferred_scene_types;
            const r = res.data.preferred_regions;
            if (h) setSelectedTypes(Array.isArray(h) ? h : String(h).split(',').filter(Boolean));
            if (s) setSelectedScenes(Array.isArray(s) ? s : String(s).split(',').filter(Boolean));
            if (r) setSelectedRegions(Array.isArray(r) ? r : String(r).split(',').filter(Boolean));
          }
        }).catch(() => {});
    }
  }, [session]);

  const toggle = (list: string[], item: string, setter: (l: string[]) => void) => {
    setter(list.includes(item) ? list.filter(x => x !== item) : [...list, item]);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiRequest(`/users/me/${session?.userId}/preferences`, {
        method: 'PUT',
        data: {
          heritage_types: selectedTypes,
          scene_types: selectedScenes,
          regions: selectedRegions,
        },
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {} finally {
      setSaving(false);
    }
  };

  const chipClass = (selected: boolean) =>
    selected
      ? 'px-3 py-1.5 rounded-full text-xs font-medium transition-all cinnabar-gradient text-white shadow-sm'
      : 'px-3 py-1.5 rounded-full text-xs transition-all glass-card text-ink-secondary hover:text-ink hover:border-gold-200';

  return (
    <div className="px-4 py-5 space-y-5">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary hover:text-ink transition-colors">
        <ArrowLeft size={16} /> 返回
      </button>

      <div>
        <h1 className="text-xl font-serif font-bold text-ink">偏好设置</h1>
        <p className="text-xs text-ink-muted mt-1">设置偏好后，推荐系统和 AI 数字人会为你推荐更匹配的内容</p>
      </div>

      <GlassCard className="p-4">
        <h3 className="text-sm font-serif font-bold text-ink mb-2.5">感兴趣的非遗类型</h3>
        <div className="flex flex-wrap gap-2">
          {HERITAGE_TYPES.map(t => (
            <button key={t} onClick={() => toggle(selectedTypes, t, setSelectedTypes)} className={chipClass(selectedTypes.includes(t))}>
              {t}
            </button>
          ))}
        </div>
      </GlassCard>

      <GlassCard className="p-4">
        <h3 className="text-sm font-serif font-bold text-ink mb-2.5">感兴趣的场景</h3>
        <div className="flex flex-wrap gap-2">
          {SCENE_TYPES.map(s => (
            <button key={s} onClick={() => toggle(selectedScenes, s, setSelectedScenes)} className={chipClass(selectedScenes.includes(s))}>
              {s}
            </button>
          ))}
        </div>
      </GlassCard>

      <GlassCard className="p-4">
        <h3 className="text-sm font-serif font-bold text-ink mb-2.5">感兴趣的地区</h3>
        <div className="flex flex-wrap gap-2">
          {REGIONS.map(r => (
            <button key={r} onClick={() => toggle(selectedRegions, r, setSelectedRegions)} className={chipClass(selectedRegions.includes(r))}>
              {r}
            </button>
          ))}
        </div>
      </GlassCard>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 ink-btn ink-btn-primary !text-sm"
      >
        <Save size={15} /> {saving ? '保存中...' : saved ? '已保存' : '保存偏好'}
      </button>
    </div>
  );
}
