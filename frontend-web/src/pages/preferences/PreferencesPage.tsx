import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, Check } from 'lucide-react';
import { apiRequest } from '../../lib/api';
import { useAuthStore } from '../../stores/auth-store';
import { GlassCard } from '../../components/ui/GlassCard';
import { InkButton } from '../../components/ui/InkButton';

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
      ? 'chip chip-active text-white shadow-sm'
      : 'chip bg-parchment-dark/80 text-ink-secondary hover:bg-parchment-dark';

  return (
    <div className="pb-8 space-y-5">

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-[36px] bg-gradient-to-br from-cinnabar-700 via-brand to-gold-400 mx-4 mt-4 p-6 animate-fade-in-up">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-1 text-sm text-white/80 hover:text-white transition-colors mb-2 font-sans"
        >
          <ArrowLeft size={16} /> 返回
        </button>
        <h1 className="text-2xl font-serif font-bold text-white leading-snug">
          偏好设置
        </h1>
        <p className="text-sm text-white/65 mt-1 font-sans">
          设置偏好后，推荐系统和 AI 数字人会为你推荐更匹配的内容
        </p>
      </div>

      {/* Preferences Sections */}
      <div className="px-4 space-y-4 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>

        {/* Heritage Types */}
        <GlassCard className="!p-4">
          <h3 className="text-sm font-serif font-bold text-ink mb-3">
            感兴趣的非遗类型
          </h3>
          <div className="flex flex-wrap gap-2">
            {HERITAGE_TYPES.map(t => (
              <button
                key={t}
                onClick={() => toggle(selectedTypes, t, setSelectedTypes)}
                className={chipClass(selectedTypes.includes(t))}
              >
                {selectedTypes.includes(t) && <Check size={12} className="mr-0.5" />}
                {t}
              </button>
            ))}
          </div>
          {selectedTypes.length > 0 && (
            <p className="text-xs text-ink-muted mt-2 font-sans">
              已选 {selectedTypes.length} 项
            </p>
          )}
        </GlassCard>

        {/* Scene Types */}
        <GlassCard className="!p-4">
          <h3 className="text-sm font-serif font-bold text-ink mb-3">
            感兴趣的场景
          </h3>
          <div className="flex flex-wrap gap-2">
            {SCENE_TYPES.map(s => (
              <button
                key={s}
                onClick={() => toggle(selectedScenes, s, setSelectedScenes)}
                className={chipClass(selectedScenes.includes(s))}
              >
                {selectedScenes.includes(s) && <Check size={12} className="mr-0.5" />}
                {s}
              </button>
            ))}
          </div>
          {selectedScenes.length > 0 && (
            <p className="text-xs text-ink-muted mt-2 font-sans">
              已选 {selectedScenes.length} 项
            </p>
          )}
        </GlassCard>

        {/* Regions */}
        <GlassCard className="!p-4">
          <h3 className="text-sm font-serif font-bold text-ink mb-3">
            感兴趣的地区
          </h3>
          <div className="flex flex-wrap gap-2">
            {REGIONS.map(r => (
              <button
                key={r}
                onClick={() => toggle(selectedRegions, r, setSelectedRegions)}
                className={chipClass(selectedRegions.includes(r))}
              >
                {selectedRegions.includes(r) && <Check size={12} className="mr-0.5" />}
                {r}
              </button>
            ))}
          </div>
          {selectedRegions.length > 0 && (
            <p className="text-xs text-ink-muted mt-2 font-sans">
              已选 {selectedRegions.length} 项
            </p>
          )}
        </GlassCard>

        {/* Save Button */}
        <InkButton
          variant="primary"
          size="lg"
          onClick={handleSave}
          loading={saving}
          disabled={saving}
          className="!w-full"
        >
          {!saving && !saved && <Save size={15} />}
          {saved && <Check size={15} />}
          {saving ? '保存中...' : saved ? '已保存' : '保存偏好'}
        </InkButton>
      </div>
    </div>
  );
}
