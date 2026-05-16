import { useState } from 'react';
import { buildImageUrl } from '../../lib/api';

interface CoverImageProps {
  coverUrl: string | null | undefined;
  alt?: string;
  className?: string;
  style?: React.CSSProperties;
  loading?: 'lazy' | 'eager';
  fallback?: React.ReactNode;
}

export default function CoverImage({
  coverUrl,
  alt = '',
  className = '',
  style,
  loading = 'lazy',
  fallback,
}: CoverImageProps) {
  const [error, setError] = useState(false);

  if (!coverUrl || error) {
    if (fallback) return <>{fallback}</>;
    return (
      <span
        className={`flex items-center justify-center text-3xl opacity-30 ${className}`}
        style={style}
      >
        📖
      </span>
    );
  }

  return (
    <img
      src={buildImageUrl(coverUrl)}
      alt={alt}
      className={className}
      style={style}
      loading={loading}
      onError={() => setError(true)}
    />
  );
}
