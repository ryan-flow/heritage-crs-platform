import { useNavigate } from 'react-router-dom';
import { ArrowLeft, MapPin } from 'lucide-react';
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
    <div className="px-4 py-5 space-y-4">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-sm text-ink-secondary hover:text-ink transition-colors">
        <ArrowLeft size={16} /> 返回
      </button>
      <h1 className="text-xl font-serif font-bold text-ink">非遗场馆</h1>

      <div className="space-y-2.5">
        {PLACES.map((place, i) => (
          <GlassCard key={i} className="p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-cinnabar-50 rounded-xl flex items-center justify-center shrink-0">
                <MapPin size={20} className="text-cinnabar-600" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-medium text-ink">{place.name}</h3>
                <SealBadge variant="gold">{place.category}</SealBadge>
                <p className="text-xs text-ink-secondary mt-1.5">{place.desc}</p>
                <p className="text-xs text-ink-muted mt-1">{place.address}</p>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}
