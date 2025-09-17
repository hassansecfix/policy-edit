'use client';

import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';

interface ValidationMessageProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  className?: string;
  showIcon?: boolean;
}

export function ValidationMessage({
  type,
  message,
  className,
  showIcon = true,
}: ValidationMessageProps) {
  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className='h-4 w-4' />;
      case 'error':
        return <XCircle className='h-4 w-4' />;
      case 'warning':
        return <AlertCircle className='h-4 w-4' />;
      case 'info':
        return <Info className='h-4 w-4' />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case 'success':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'info':
        return 'text-blue-700 bg-blue-50 border-blue-200';
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border animate-slideDown',
        getStyles(),
        className,
      )}
    >
      {showIcon && getIcon()}
      <span>{message}</span>
    </div>
  );
}
