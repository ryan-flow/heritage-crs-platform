interface Props {
  variant?: 'text' | 'card' | 'avatar' | 'image';
  className?: string;
}

export function SkeletonLoader({ variant = 'text', className = '' }: Props) {
  const variantClass = {
    text: 'h-4 w-full',
    card: 'h-40 w-full rounded-xl',
    avatar: 'h-12 w-12 rounded-full',
    image: 'h-48 w-full rounded-lg',
  }[variant];

  return <div className={`skeleton ${variantClass} ${className}`} />;
}
