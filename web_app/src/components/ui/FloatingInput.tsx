'use client';

import { cn } from '@/lib/utils';
import { AlertCircle, Check, Eye, EyeOff } from 'lucide-react';
import React, { forwardRef, useState } from 'react';

export interface FloatingInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  success?: boolean;
  helperText?: string;
  variant?: 'default' | 'modern' | 'minimal';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  showPasswordToggle?: boolean;
}

const FloatingInput = forwardRef<HTMLInputElement, FloatingInputProps>(
  (
    {
      className,
      type = 'text',
      label,
      error,
      success,
      helperText,
      variant = 'default',
      leftIcon,
      rightIcon,
      showPasswordToggle = false,
      value,
      ...props
    },
    ref,
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const hasValue = value !== undefined && value !== null && value !== '';
    const isFloating = isFocused || hasValue;

    const inputType = showPasswordToggle && showPassword ? 'text' : type;

    const getVariantClasses = () => {
      switch (variant) {
        case 'modern':
          return {
            container: 'bg-gradient-to-br from-white to-gray-50 border-2',
            input: 'bg-transparent',
            label: 'bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent',
          };
        case 'minimal':
          return {
            container: 'bg-transparent border-b-2 border-l-0 border-r-0 border-t-0 rounded-none',
            input: 'bg-transparent',
            label: 'text-gray-600',
          };
        default:
          return {
            container: 'bg-white border',
            input: 'bg-transparent',
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

    const inputClasses = cn(
      'peer w-full transition-all duration-200 ease-out',
      'focus:outline-none',
      variantClasses.input,
      // Padding based on variant and icons
      variant === 'minimal' ? 'px-0 py-3' : 'px-4 py-4',
      leftIcon && variant !== 'minimal' && 'pl-12',
      (rightIcon || showPasswordToggle) && variant !== 'minimal' && 'pr-12',
      // Text styling
      'text-gray-900 placeholder-transparent',
      'text-base font-medium',
    );

    const labelClasses = cn(
      'absolute left-4 transition-all duration-300 ease-out pointer-events-none',
      variantClasses.label,
      // Floating state
      isFloating ? 'top-2 text-xs font-semibold' : 'top-1/2 -translate-y-1/2 text-base font-medium',
      // Variant specific positioning
      variant === 'minimal' && 'left-0',
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
            <div className='absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 transition-colors duration-200'>
              {leftIcon}
            </div>
          )}

          {/* Input */}
          <input
            ref={ref}
            type={inputType}
            value={value}
            className={inputClasses}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            {...props}
          />

          {/* Floating Label */}
          <label className={labelClasses}>{label}</label>

          {/* Right Icons */}
          <div className='absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2'>
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

            {/* Password Toggle */}
            {showPasswordToggle && (
              <button
                type='button'
                onClick={() => setShowPassword(!showPassword)}
                className='text-gray-400 hover:text-gray-600 transition-colors duration-200'
              >
                {showPassword ? <EyeOff className='h-5 w-5' /> : <Eye className='h-5 w-5' />}
              </button>
            )}

            {/* Custom Right Icon */}
            {rightIcon && !success && !error && (
              <div className='text-gray-400 transition-colors duration-200'>{rightIcon}</div>
            )}
          </div>

          {/* Focus Ring Effect */}
          {isFocused && (
            <div className='absolute inset-0 rounded-xl bg-violet-600/5 animate-fadeIn' />
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

FloatingInput.displayName = 'FloatingInput';

export { FloatingInput };
