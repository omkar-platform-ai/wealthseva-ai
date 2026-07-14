'use client';
import { forwardRef } from 'react';
import { cn, FOCUS_RING } from '@/lib/utils';
import { Spinner } from './Spinner';

export type ButtonVariant = 'primary' | 'secondary' | 'warm' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-idbi-green text-white hover:bg-idbi-dark shadow-glow',
  secondary: 'bg-white text-idbi-green border border-idbi-green hover:bg-idbi-light',
  warm: 'bg-idbi-orange text-white hover:bg-idbi-orangeDark shadow-glowOrange',
  ghost: 'bg-transparent text-idbi-slate hover:bg-idbi-light',
  danger: 'bg-red-500 text-white hover:bg-red-600',
};

const SIZES: Record<ButtonSize, string> = {
  sm: 'h-9 px-3.5 text-sm',
  md: 'h-11 px-5 text-base',
  lg: 'h-12 px-6 text-lg',
};

const BASE =
  'inline-flex items-center justify-center gap-2 font-semibold rounded-field transition-all select-none ' +
  'disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none';

/** Class string only — use on <Link> or <a> to get button styling without a <button>. */
export const buttonVariants = (
  { variant = 'primary', size = 'md' }: { variant?: ButtonVariant; size?: ButtonSize } = {},
) => cn(BASE, VARIANTS[variant], SIZES[size], FOCUS_RING);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading = false, className, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  ),
);
Button.displayName = 'Button';
