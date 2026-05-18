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

  return (
    <div
      className={`rounded-[14px] ${variantClass} ${className}`}
      style={{
        background: 'linear-gradient(90deg, #f2e8da 25%, #eadcc8 50%, #f2e8da 75%)',
        backgroundSize: '240% 100%',
        animation: 'skeletonShimmer 1.4s ease infinite',
      }}
    />
  );
}
