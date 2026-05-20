import { type HTMLAttributes, type ElementType } from 'react';

interface Props extends HTMLAttributes<HTMLDivElement> {
  as?: ElementType;
  elevated?: boolean;
  hover?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function GlassCard({ as: Tag = 'div', elevated, hover, className = '', children, ...rest }: Props) {
  const bgStyle: React.CSSProperties = {
    background: 'rgba(255, 251, 245, 0.96)',
    borderRadius: '14px',
    border: elevated
      ? '1px solid rgba(219, 191, 155, 0.30)'
      : '1px solid rgba(219, 191, 155, 0.18)',
    boxShadow: elevated
      ? '0 9px 20px rgba(121, 58, 31, 0.14)'
      : '0 7px 17px rgba(121, 58, 31, 0.10)',
  };

  const hoverStyle = hover
    ? 'hover:-translate-y-[3px] hover:shadow-[0_9px_22px_rgba(121,58,31,0.16)] transition-all duration-200'
    : 'transition-all duration-200';

  return (
    <Tag className={`${hoverStyle} ${className}`} style={bgStyle} {...rest}>
      {children}
    </Tag>
  );
}
