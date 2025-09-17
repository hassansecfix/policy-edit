'use client';

import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

type ButtonVariant =
  | 'default'
  | 'destructive'
  | 'outline'
  | 'secondary'
  | 'ghost'
  | 'link'
  | 'success';
type ButtonSize = 'default' | 'sm' | 'lg' | 'xl' | 'icon';

const getButtonVariantClasses = (variant: ButtonVariant): string => {
  switch (variant) {
    case 'default':
      return 'bg-violet-600 text-white hover:bg-violet-700';
    case 'destructive':
      return 'bg-red-500 text-white hover:bg-red-600';
    case 'outline':
      return 'border-1 border-gray-200 bg-white text-gray-900 hover:bg-gray-50 hover:border-gray-200';
    case 'secondary':
      return 'bg-gray-100 text-gray-900 hover:bg-gray-200';
    case 'ghost':
      return 'text-gray-900 hover:bg-gray-100';
    case 'link':
      return 'text-blue-600 underline-offset-4 hover:underline';
    case 'success':
      return 'bg-violet-600 text-white hover:bg-violet-700';
    default:
      return 'bg-violet-600 text-white hover:bg-violet-700';
  }
};

const getButtonSizeClasses = (size: ButtonSize): string => {
  switch (size) {
    case 'default':
      return 'h-11 px-6 py-2';
    case 'sm':
      return 'h-9 px-4 py-1.5 text-xs';
    case 'lg':
      return 'h-12 px-8 py-3 text-base font-semibold';
    case 'xl':
      return 'h-14 px-10 py-4 text-lg font-semibold';
    case 'icon':
      return 'h-10 w-10';
    default:
      return 'h-11 px-6 py-2';
  }
};

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'default',
      size = 'default',
      loading = false,
      children,
      disabled,
      ...props
    },
    ref,
  ) => {
    const baseClasses =
      'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-600 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 transform active:scale-95 cursor-pointer transition-all duration-200 ease-in-out shadow-sm';
    const variantClasses = getButtonVariantClasses(variant);
    const sizeClasses = getButtonSizeClasses(size);

    return (
      <button
        className={cn(baseClasses, variantClasses, sizeClasses, className)}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <div className='mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent' />
        )}
        {children}
      </button>
    );
  },
);
Button.displayName = 'Button';

export { Button };
