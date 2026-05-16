import { useNavigate } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import { DigitalHumanModel } from '../digital-human/DigitalHumanModel';
import '../digital-human/DigitalHumanModel.css';

interface Props {
  context?: string;
}

export default function FloatingAiButton({ context }: Props) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => {
        const params = context ? `?q=${encodeURIComponent(context)}` : '';
        navigate(`/ai${params}`);
      }}
      className="fixed right-4 bottom-24 z-[100] border-none cursor-pointer flex flex-col items-center gap-0.5 bg-transparent"
      aria-label="AI 导览"
    >
      <span
        className="text-[10px] font-bold text-ink-muted bg-parchment/90 backdrop-blur-sm px-2 py-0.5 rounded-full shadow-sm"
        style={{ border: '1px solid rgba(180,140,100,0.15)' }}
      >
        AI 导览
      </span>
      <div
        className="rounded-full flex items-center justify-center shadow-lg overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #c0392b, #e8734a)',
          boxShadow: '0 8px 24px rgba(192,57,43,0.28)',
        }}
      >
        <DigitalHumanModel variant="fab" mood="curious" size={64} />
      </div>
    </button>
  );
}
