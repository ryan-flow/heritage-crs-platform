import { useEffect, useRef, useCallback, useState } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

interface Props {
  variant?: 'hero' | 'ai' | 'fab';
  mood?: 'curious' | 'thinking' | 'confident';
  speaking?: boolean;
  size?: number;
  onSpeak?: () => void;
}

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

export function DigitalHumanModel({
  variant = 'ai',
  mood = 'curious',
  speaking = false,
  size = 280,
  onSpeak,
}: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [clicked, setClicked] = useState(false);

  const handleClick = useCallback(() => {
    setClicked(true);
    setTimeout(() => setClicked(false), 600);
    onSpeak?.();
  }, [onSpeak]);

  const toggleSpeak = useCallback(() => {
    if (speaking && audioRef.current) { audioRef.current.pause(); }
    onSpeak?.();
  }, [speaking, onSpeak]);

  const scale = variant === 'hero' ? 1.04 : variant === 'fab' ? 0.72 : 1;
  const stateClass = speaking ? 'state-speaking' : 'state-open';
  const moodClass = `mood-${mood}`;

  return (
    <div
      className={`dhm-stage variant-${variant} ${stateClass} ${moodClass} ${clicked ? 'clicked' : ''} guofeng-press`}
      style={{ width: size, height: size }}
      onClick={handleClick}
    >
      {/* TTS button (top-right corner) */}
      {onSpeak && (
        <button onClick={toggleSpeak} className="dhm-tts-btn">
          {speaking ? <VolumeX size={14} /> : <Volume2 size={14} />}
        </button>
      )}

      {/* Avatar container */}
      <div className="dhm-avatar" style={{ transform: `scale(${scale})` }}>
        <div className="dhm-shadow" />

        {/* Hat */}
        <div className="dhm-hat">
          <div className="dhm-hat-cone" />
          <div className="dhm-hat-tip-glow" />
          <div className="dhm-hat-brim" />
          <div className="dhm-hat-band" />
          <div className="dhm-hat-mark" />
          <div className="dhm-flower flower-main" />
          <div className="dhm-flower flower-mini" />
          <div className="dhm-star-pin" />
        </div>

        {/* Hair */}
        <div className="dhm-hair back left" />
        <div className="dhm-hair back right" />

        {/* Face */}
        <div className="dhm-face">
          <div className="dhm-bangs bang-left" />
          <div className="dhm-bangs bang-center" />
          <div className="dhm-bangs bang-right" />
          <div className="dhm-brow brow-left" />
          <div className="dhm-brow brow-right" />
          <div className="dhm-eye left" />
          <div className="dhm-eye right" />
          <div className="dhm-blush blush-left" />
          <div className="dhm-blush blush-right" />
          <div className="dhm-mouth" />
        </div>

        {/* Body */}
        <div className="dhm-body">
          <div className="dhm-collar" />
          <div className="dhm-vest" />
          <div className="dhm-tie" />
          <div className="dhm-brooch" />
          <div className="dhm-arm-group arm-group-left">
            <div className="dhm-arm arm-left" />
          </div>
          <div className="dhm-arm-group arm-group-right">
            <div className="dhm-arm arm-right" />
          </div>
          <div className="dhm-skirt" />
          <div className="dhm-hem-line" />
        </div>
      </div>

      <audio ref={audioRef} onEnded={() => onSpeak?.()} />
    </div>
  );
}

export type { Props as DigitalHumanModelProps };
