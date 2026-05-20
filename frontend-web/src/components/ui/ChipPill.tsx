interface Props {
  variant?: 'brand' | 'accent' | 'jade';
  className?: string;
  children: React.ReactNode;
}

const variantStyles: Record<string, { bg: string; color: string }> = {
  brand: { bg: 'var(--color-brand-soft)', color: 'var(--color-brand)' },
  accent: { bg: 'var(--color-accent-soft)', color: 'var(--color-accent)' },
  jade: { bg: 'var(--color-jade-50)', color: 'var(--color-jade-600)' },
};

export function ChipPill({ variant = 'brand', className = '', children }: Props) {
  const v = variantStyles[variant];
  return (
    <span
      className={`inline-flex items-center px-[12px] py-[4px] text-[11px] font-semibold rounded-full whitespace-nowrap transition-all duration-200 active:scale-[0.97] ${className}`}
      style={{
        color: v.color,
        background: v.bg,
      }}
    >
      {children}
    </span>
  );
}
