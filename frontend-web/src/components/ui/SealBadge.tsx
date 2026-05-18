interface Props {
  variant?: 'cinnabar' | 'gold' | 'jade';
  children: React.ReactNode;
}

const variantStyles: Record<string, { bg: string; color: string; border: string }> = {
  cinnabar: { bg: 'rgba(192,57,43,0.10)', color: '#c0392b', border: 'rgba(192,57,43,0.30)' },
  gold: { bg: 'rgba(192,138,62,0.10)', color: '#a07230', border: 'rgba(192,138,62,0.30)' },
  jade: { bg: 'rgba(91,140,90,0.10)', color: '#4a7a49', border: 'rgba(91,140,90,0.30)' },
};

export function SealBadge({ variant = 'cinnabar', children }: Props) {
  const v = variantStyles[variant];
  return (
    <span
      className="inline-flex items-center px-[10px] py-[2px] text-[11px] font-bold tracking-[1px] relative font-serif"
      style={{
        color: v.color,
        background: v.bg,
        border: `1px solid ${v.border}`,
        clipPath: 'polygon(2% 0%, 98% 0%, 100% 4%, 96% 6%, 100% 10%, 98% 12%, 100% 50%, 98% 88%, 100% 94%, 96% 96%, 100% 100%, 50% 97%, 0% 100%, 4% 96%, 0% 94%, 4% 88%, 0% 50%, 4% 12%, 0% 10%, 3% 6%, 0% 4%)',
      }}>
      {children}
    </span>
  );
}
