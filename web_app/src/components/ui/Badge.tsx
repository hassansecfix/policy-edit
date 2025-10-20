'use client';

import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'success' | 'warning' | 'outline';

const getBadgeVariantClasses = (variant: BadgeVariant): string => {
  switch (variant) {
    case 'default':
      return 'border-transparent bg-violet-100 text-violet-600';
    case 'secondary':
      return 'border-transparent bg-gray-100 text-gray-600';
    case 'destructive':
      return 'border-transparent bg-red-100 text-red-600';
    case 'success':
      return 'border-transparent bg-green-100 text-green-600';
    case 'warning':
      return 'border-transparent bg-yellow-100 text-yellow-600';
    case 'outline':
      return 'border border-gray-200 text-gray-700';
    default:
      return 'border-transparent bg-violet-100 text-violet-600';
  }
};

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant;
}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const baseClasses =
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-normal transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2';
    const variantClasses = getBadgeVariantClasses(variant);

    return <div ref={ref} className={cn(baseClasses, variantClasses, className)} {...props} />;
  },
);
Badge.displayName = 'Badge';

export { Badge };
