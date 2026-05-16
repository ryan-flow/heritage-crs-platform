import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin, Building2 } from 'lucide-react';
import { GlassCard } from '../../components/ui/GlassCard';
import { SealBadge } from '../../components/ui/SealBadge';

const PLACES = [
  { name: '中国非物质文化遗产馆', address: '北京市朝阳区湖景东路16号', desc: '国家级非遗专题博物馆', category: '博物馆' },
  { name: '中国工艺美术馆', address: '北京市朝阳区湖景东路16号', desc: '展示传统工艺美术珍品', category: '美术馆' },
  { name: '北京故宫博物院', address: '北京市东城区景山前街4号', desc: '明清宫廷建筑与非遗文化', category: '博物馆' },
  { name: '上海博物馆', address: '上海市黄浦区人民大道201号', desc: '馆藏丰富非遗相关文物', category: '博物馆' },
  { name: '苏州博物馆', address: '苏州市姑苏区东北街204号', desc: '苏式园林建筑与传统工艺', category: '博物馆' },
  { name: '广州粤剧艺术博物馆', address: '广州市荔湾区恩宁路127号', desc: '粤剧非遗专题展示与演出', category: '专题馆' },
  { name: '成都国际非遗博览园', address: '成都市青羊区光华大道二段', desc: '大型非遗主题园区', category: '主题园区' },
  { name: '西安非物质文化遗产博物馆', address: '西安市碑林区', desc: '陕西非遗文化集中展示', category: '博物馆' },
];

export default function PlacesPage() {
  const navigate = useNavigate();

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
          非遗场馆
        </h1>
        <p className="text-sm text-white/65 mt-1 font-sans">
          探访线下场馆，近距离感受非遗之美
        </p>
      </div>

      {/* Places List */}
      <div className="px-4">
        <div className="space-y-2.5 rise-in-stagger">
          {PLACES.map((place, i) => (
            <GlassCard key={i} className="!p-4 card-lift">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 shrink-0 rounded-xl bg-cinnabar-50 flex items-center justify-center">
                  <MapPin size={20} className="text-cinnabar-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-sm font-medium text-ink font-sans">{place.name}</h3>
                    <SealBadge variant={i % 3 === 0 ? 'jade' : i % 3 === 1 ? 'gold' : 'cinnabar'}>
                      {place.category}
                    </SealBadge>
                  </div>
                  <p className="text-xs text-ink-secondary mt-1.5 font-sans leading-relaxed">{place.desc}</p>
                  <p className="text-xs text-ink-muted mt-1 font-sans">{place.address}</p>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-ink-muted/60 mt-5 font-sans">
          更多场馆持续收录中
        </p>
      </div>
    </div>
  );
}
