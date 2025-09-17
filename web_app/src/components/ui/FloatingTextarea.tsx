'use client';

import { cn } from '@/lib/utils';
import { AlertCircle, Check } from 'lucide-react';
import React, { forwardRef, useState } from 'react';

export interface FloatingTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  success?: boolean;
  helperText?: string;
  variant?: 'default' | 'modern' | 'minimal';
  showCharCount?: boolean;
  maxLength?: number;
}

const FloatingTextarea = forwardRef<HTMLTextAreaElement, FloatingTextareaProps>(
  (
    {
      className,
      label,
      error,
      success,
      helperText,
      variant = 'default',
      showCharCount = false,
      maxLength,
      value,
      rows = 4,
      ...props
    },
    ref,
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const hasValue = value !== undefined && value !== null && value !== '';
    const isFloating = isFocused || hasValue;
    const charCount = typeof value === 'string' ? value.length : 0;

    const getVariantClasses = () => {
      switch (variant) {
        case 'modern':
          return {
            container: 'bg-gradient-to-br from-white to-gray-50 border-2',
            textarea: 'bg-transparent',
            label: 'bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent',
          };
        case 'minimal':
          return {
            container: 'bg-transparent border-b-2 border-l-0 border-r-0 border-t-0 rounded-none',
            textarea: 'bg-transparent',
            label: 'text-gray-600',
          };
        default:
          return {
            container: 'bg-white border',
            textarea: 'bg-transparent',
            label: 'text-gray-600',
          };
      }
    };

    const variantClasses = getVariantClasses();

    const containerClasses = cn(
      'relative transition-all duration-300 ease-out',
      variant === 'minimal' ? 'rounded-none' : 'rounded-xl',
      // Base styles
      variantClasses.container,
      // Focus states
      isFocused && !error && 'border-blue-500 shadow-lg shadow-blue-500/10',
      isFocused && !error && variant === 'modern' && 'shadow-xl shadow-blue-500/20',
      // Error states
      error && 'border-red-500 shadow-lg shadow-red-500/10',
      // Success states
      success && !error && 'border-green-500 shadow-lg shadow-green-500/10',
      // Hover states
      'hover:border-gray-200',
      !isFocused && !error && !success && 'border-gray-200',
      className,
    );

    const textareaClasses = cn(
      'peer w-full transition-all duration-200 ease-out resize-none',
      'focus:outline-none',
      variantClasses.textarea,
      // Padding based on variant
      variant === 'minimal' ? 'px-0 py-3 pt-6' : 'px-4 py-4 pt-6',
      // Text styling
      'text-gray-900 placeholder-transparent',
      'text-base font-medium leading-relaxed',
    );

    const labelClasses = cn(
      'absolute transition-all duration-300 ease-out pointer-events-none',
      variant === 'minimal' ? 'left-0' : 'left-4',
      variantClasses.label,
      // Floating state
      isFloating ? 'top-2 text-xs font-semibold' : 'top-4 text-base font-medium',
      // Focus states
      isFocused && !error && 'text-blue-600',
      error && 'text-red-600',
      success && !error && 'text-green-600',
      // Default state
      !isFocused && !error && !success && 'text-gray-500',
    );

    return (
      <div className='space-y-2'>
        <div className={containerClasses}>
          {/* Textarea */}
          <textarea
            ref={ref}
            value={value}
            rows={rows}
            maxLength={maxLength}
            className={textareaClasses}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            {...props}
          />

          {/* Floating Label */}
          <label className={labelClasses}>{label}</label>

          {/* Status Icons */}
          <div className='absolute right-4 top-4 flex items-center gap-2'>
            {/* Success Icon */}
            {success && !error && (
              <div className='text-green-500 animate-fadeIn'>
                <Check className='h-5 w-5' />
              </div>
            )}

            {/* Error Icon */}
            {error && (
              <div className='text-red-500 animate-fadeIn'>
                <AlertCircle className='h-5 w-5' />
              </div>
            )}
          </div>

          {/* Focus Ring Effect */}
          {isFocused && (
            <div className='absolute inset-0 rounded-xl bg-violet-500/5 animate-fadeIn' />
          )}
        </div>

        {/* Footer with Helper Text and Character Count */}
        <div className='flex items-center justify-between px-4'>
          <div className='flex-1'>
            {error && (
              <p className='text-sm text-red-600 font-medium flex items-center gap-2 animate-slideDown'>
                <AlertCircle className='h-4 w-4' />
                {error}
              </p>
            )}
            {helperText && !error && (
              <p className='text-sm text-gray-500 animate-slideDown'>{helperText}</p>
            )}
          </div>

          {/* Character Count */}
          {showCharCount && (
            <div className='flex-shrink-0 ml-4'>
              <span
                className={cn(
                  'text-xs transition-colors duration-200',
                  maxLength && charCount > maxLength * 0.9
                    ? 'text-red-500 font-medium'
                    : maxLength && charCount > maxLength * 0.8
                    ? 'text-yellow-600 font-medium'
                    : 'text-gray-400',
                )}
              >
                {charCount}
                {maxLength && `/${maxLength}`}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  },
);

FloatingTextarea.displayName = 'FloatingTextarea';

export { FloatingTextarea };
