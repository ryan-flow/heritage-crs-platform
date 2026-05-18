import { type HTMLAttributes, type ElementType } from 'react';

interface Props extends HTMLAttributes<HTMLDivElement> {
  as?: ElementType;
  elevated?: boolean;
  hover?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function GlassCard({ as: Tag = 'div', elevated, hover, className = '', children, ...rest }: Props) {
  const baseStyle = elevated
    ? 'rounded-[18px] border border-[rgba(219,191,155,0.25)] transition-all duration-200'
    : 'rounded-[18px] border border-[rgba(219,191,155,0.18)] transition-all duration-200';

  const bgStyle: React.CSSProperties = {
    background: 'linear-gradient(180deg, rgba(255,252,247,0.98), rgba(249,239,225,0.98))',
    boxShadow: elevated
      ? '0 18px 40px rgba(121,58,31,0.10)'
      : '0 14px 34px rgba(121,58,31,0.08)',
  };

  const hoverStyle = hover ? 'hover:-translate-y-[3px] hover:shadow-[0_18px_36px_rgba(121,58,31,0.12)]' : '';

  return (
    <Tag className={`${baseStyle} ${hoverStyle} ${className}`} style={bgStyle} {...rest}>
      {children}
    </Tag>
  );
}
