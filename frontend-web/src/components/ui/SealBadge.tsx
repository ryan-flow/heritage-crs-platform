interface Props {
  variant?: 'cinnabar' | 'gold' | 'jade';
  children: React.ReactNode;
}

export function SealBadge({ variant = 'cinnabar', children }: Props) {
  const colorClass = {
    cinnabar: 'seal-badge-cinnabar',
    gold: 'seal-badge-gold',
    jade: 'seal-badge-jade',
  }[variant];
  return <span className={`seal-badge ${colorClass}`}>{children}</span>;
}
