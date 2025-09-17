'use client';

import { cn } from '@/lib/utils';
import { AlertCircle, Check, ChevronDown } from 'lucide-react';
import React, { forwardRef, useState } from 'react';

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface FloatingSelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  label: string;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  success?: boolean;
  helperText?: string;
  variant?: 'default' | 'modern' | 'minimal';
  leftIcon?: React.ReactNode;
}

const FloatingSelect = forwardRef<HTMLSelectElement, FloatingSelectProps>(
  (
    {
      className,
      label,
      options,
      placeholder = 'Select an option...',
      error,
      success,
      helperText,
      variant = 'default',
      leftIcon,
      value,
      ...props
    },
    ref,
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const hasValue = value !== undefined && value !== null && value !== '';
    const isFloating = isFocused || hasValue;

    const getVariantClasses = () => {
      switch (variant) {
        case 'modern':
          return {
            container: 'bg-gradient-to-br from-white to-gray-50 border-2',
            select: 'bg-transparent',
            label: 'bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent',
          };
        case 'minimal':
          return {
            container: 'bg-transparent border-b-2 border-l-0 border-r-0 border-t-0 rounded-none',
            select: 'bg-transparent',
            label: 'text-gray-600',
          };
        default:
          return {
            container: 'bg-white border',
            select: 'bg-transparent',
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

    const selectClasses = cn(
      'peer w-full transition-all duration-200 ease-out appearance-none cursor-pointer',
      'focus:outline-none',
      variantClasses.select,
      // Padding based on variant and icons
      variant === 'minimal' ? 'px-0 py-3' : 'px-4 py-4',
      leftIcon && variant !== 'minimal' && 'pl-12',
      'pr-12', // Always leave space for chevron
      // Text styling
      'text-gray-900',
      'text-base font-medium',
      // Placeholder styling
      !hasValue && 'text-gray-400',
    );

    const labelClasses = cn(
      'absolute transition-all duration-300 ease-out pointer-events-none',
      variant === 'minimal' ? 'left-0' : 'left-4',
      variantClasses.label,
      // Floating state
      isFloating ? 'top-2 text-xs font-semibold' : 'top-1/2 -translate-y-1/2 text-base font-medium',
      // Variant specific positioning
      variant === 'minimal' && isFloating && 'top-0',
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
          {/* Left Icon */}
          {leftIcon && (
            <div className='absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 transition-colors duration-200 pointer-events-none z-10'>
              {leftIcon}
            </div>
          )}

          {/* Select */}
          <select
            ref={ref}
            value={value}
            className={selectClasses}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            {...props}
          >
            {/* Placeholder Option */}
            <option value='' disabled hidden>
              {placeholder}
            </option>

            {/* Options */}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
                className='text-gray-900'
              >
                {option.label}
              </option>
            ))}
          </select>

          {/* Floating Label */}
          <label className={labelClasses}>{label}</label>

          {/* Right Icons */}
          <div className='absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2 pointer-events-none'>
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

            {/* Chevron Down */}
            <div
              className={cn(
                'transition-all duration-200',
                isFocused ? 'text-blue-500 rotate-180' : 'text-gray-400',
                error && 'text-red-500',
                success && !error && 'text-green-500',
              )}
            >
              <ChevronDown className='h-5 w-5' />
            </div>
          </div>

          {/* Focus Ring Effect */}
          {isFocused && (
            <div className='absolute inset-0 rounded-xl bg-violet-600/5 animate-fadeIn pointer-events-none' />
          )}
        </div>

        {/* Helper Text / Error Message */}
        {(error || helperText) && (
          <div className='px-4 animate-slideDown'>
            {error && (
              <p className='text-sm text-red-600 font-medium flex items-center gap-2'>
                <AlertCircle className='h-4 w-4' />
                {error}
              </p>
            )}
            {helperText && !error && <p className='text-sm text-gray-500'>{helperText}</p>}
          </div>
        )}
      </div>
    );
  },
);

FloatingSelect.displayName = 'FloatingSelect';

export { FloatingSelect };
