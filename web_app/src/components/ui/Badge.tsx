'use client';

import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'success' | 'warning' | 'outline';

const getBadgeVariantClasses = (variant: BadgeVariant): string => {
  switch (variant) {
    case 'default':
      return 'border-transparent bg-blue-100 text-blue-800 hover:bg-blue-200';
    case 'secondary':
      return 'border-transparent bg-gray-100 text-gray-800 hover:bg-gray-200';
    case 'destructive':
      return 'border-transparent bg-red-100 text-red-800 hover:bg-red-200';
    case 'success':
      return 'border-transparent bg-green-100 text-green-800 hover:bg-green-200';
    case 'warning':
      return 'border-transparent bg-yellow-100 text-yellow-800 hover:bg-yellow-200';
    case 'outline':
      return 'border border-gray-200 text-gray-700 hover:bg-gray-50';
    default:
      return 'border-transparent bg-blue-100 text-blue-800 hover:bg-blue-200';
  }
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const baseClasses =
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2';
    const variantClasses = getBadgeVariantClasses(variant);

    return <div ref={ref} className={cn(baseClasses, variantClasses, className)} {...props} />;
  },
);
Badge.displayName = 'Badge';

export { Badge };
