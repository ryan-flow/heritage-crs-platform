import { type ButtonHTMLAttributes } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export function InkButton({ variant = 'primary', size = 'md', loading, className = '', children, disabled, ...rest }: Props) {
  const variantClass = {
    primary: 'ink-btn-primary',
    outline: 'ink-btn-outline',
    ghost: 'ink-btn-ghost',
  }[variant];

  const sizeClass = {
    sm: '!py-1.5 !px-3 !text-xs',
    md: '',
    lg: '!py-3.5 !px-8 !text-base',
  }[size];

  return (
    <button
      className={`ink-btn ${variantClass} ${sizeClass} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
