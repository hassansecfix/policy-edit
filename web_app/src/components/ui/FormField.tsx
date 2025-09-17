'use client';

import { cn } from '@/lib/utils';
import React from 'react';

interface FormFieldProps {
  children: React.ReactNode;
  className?: string;
  label?: string;
  description?: string;
  required?: boolean;
  error?: string;
  success?: boolean;
}

export function FormField({
  children,
  className,
  label,
  description,
  required = false,
  error,
  success,
}: FormFieldProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {/* Label */}
      {label && (
        <label className='block text-sm font-medium text-gray-700 mb-2'>
          {label}
          {required && <span className='text-red-500 ml-1'>*</span>}
        </label>
      )}

      {/* Description */}
      {description && <p className='text-sm text-gray-600 mb-3 leading-relaxed'>{description}</p>}

      {/* Form Element */}
      <div className='relative'>{children}</div>

      {/* Success Message */}
      {success && !error && (
        <p className='text-sm text-green-600 font-medium animate-slideDown flex items-center gap-2'>
          ✅ Field completed successfully
        </p>
      )}
    </div>
  );
}

interface FormGroupProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
}

export function FormGroup({ children, className, title, description }: FormGroupProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {(title || description) && (
        <div className='space-y-2'>
          {title && <h3 className='text-lg font-semibold text-gray-900'>{title}</h3>}
          {description && <p className='text-sm text-gray-600 leading-relaxed'>{description}</p>}
        </div>
      )}
      <div className='space-y-4'>{children}</div>
    </div>
  );
}

interface FormSectionProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  icon?: React.ReactNode;
}

export function FormSection({ children, className, title, subtitle, icon }: FormSectionProps) {
  return (
    <div className={cn('bg-white rounded-xl border border-gray-200', className)}>
      {(title || subtitle || icon) && (
        <div className='px-6 py-4 border-b border-gray-200'>
          <div className='flex items-center gap-3'>
            {icon && (
              <div className='w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600'>
                {icon}
              </div>
            )}
            <div>
              {title && <h4 className='text-lg font-semibold text-gray-900'>{title}</h4>}
              {subtitle && <p className='text-sm text-gray-600 mt-1'>{subtitle}</p>}
            </div>
          </div>
        </div>
      )}
      <div className='p-6'>{children}</div>
    </div>
  );
}
