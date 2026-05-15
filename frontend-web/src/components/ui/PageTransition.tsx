import { useEffect, useRef, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  className?: string;
}

export function PageTransition({ children, className = '' }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.classList.add('page-enter');
    }
  }, []);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
