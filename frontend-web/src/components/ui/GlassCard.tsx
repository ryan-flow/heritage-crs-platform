import { type HTMLAttributes, type ElementType } from 'react';

interface Props extends HTMLAttributes<HTMLDivElement> {
  as?: ElementType;
  elevated?: boolean;
  hover?: boolean;
  className?: string;
  children: React.ReactNode;
}

export function GlassCard({ as: Tag = 'div', elevated, hover, className = '', children, ...rest }: Props) {
  const base = elevated ? 'glass-card-elevated' : 'glass-card';
  const lift = hover ? 'card-lift' : '';
  return (
    <Tag className={`${base} ${lift} ${className}`} {...rest}>
      {children}
    </Tag>
  );
}
