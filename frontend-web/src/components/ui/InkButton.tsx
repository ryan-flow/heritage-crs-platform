import { type ButtonHTMLAttributes } from 'react';

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

const variantStyles: Record<string, string> = {
  primary: [
    'bg-gradient-to-br from-[#9f2d22] to-[#c04833] text-white',
    'shadow-[0_7px_16px_rgba(159,45,34,0.22)]',
    'hover:shadow-[0_9px_22px_rgba(159,45,34,0.30)]',
    'active:translate-y-[1px] active:scale-[0.985]',
  ].join(' '),
  secondary: [
    'bg-gradient-to-br from-[#c08a3e] to-[#d5a24d] text-white',
    'shadow-[0_7px_16px_rgba(192,138,62,0.22)]',
    'hover:shadow-[0_9px_22px_rgba(192,138,62,0.30)]',
    'active:translate-y-[1px] active:scale-[0.985]',
  ].join(' '),
  outline: [
    'bg-[#f9f0e2] text-[#8a5a20]',
    'border border-[rgba(197,160,120,0.3)]',
    'hover:bg-[#f5e6d2] hover:border-[rgba(197,160,120,0.5)]',
    'active:translate-y-[1px] active:scale-[0.985]',
  ].join(' '),
  ghost: [
    'bg-transparent text-ink-secondary',
    'hover:bg-[rgba(44,36,22,0.04)]',
    'active:translate-y-[1px] active:scale-[0.985]',
  ].join(' '),
};

const sizeStyles: Record<string, string> = {
  sm: '!py-1.5 !px-3 !text-xs',
  md: '',
  lg: '!py-3.5 !px-8 !text-base',
};

export function InkButton({ variant = 'primary', size = 'md', loading, className = '', children, disabled, ...rest }: Props) {
  return (
    <button
      className={[
        'inline-flex items-center justify-center gap-2 font-semibold text-sm rounded-[999px]',
        'transition-all duration-200 cursor-pointer border-none outline-none',
        variantStyles[variant],
        sizeStyles[size],
        className,
      ].join(' ')}
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
