'use client';

import { cn } from '@/lib/utils';
import { CheckCircle, Circle } from 'lucide-react';

interface ProgressIndicatorProps {
  currentStep: number;
  totalSteps: number;
  title?: string;
  subtitle?: string;
  className?: string;
}

export function ProgressIndicator({
  currentStep,
  totalSteps,
  title,
  subtitle,
  className,
}: ProgressIndicatorProps) {
  const progress = (currentStep / totalSteps) * 100;
  const completedSteps = currentStep - 1; // Previous steps are completed

  return (
    <div className={cn('w-full', className)}>
      {/* Header with title and progress info */}
      <div className='flex items-center justify-between mb-3'>
        <div>
          {title && <h3 className='font-medium text-gray-900'>{title}</h3>}
          {subtitle && <p className='text-sm text-gray-600'>{subtitle}</p>}
        </div>
        <div className='text-sm text-gray-600 font-medium'>
          {currentStep} / {totalSteps}
        </div>
      </div>

      {/* Enhanced Progress Bar */}
      <div className='relative'>
        {/* Background track */}
        <div className='w-full bg-gray-200 rounded-full h-3 overflow-hidden'>
          {/* Progress fill with gradient */}
          <div
            className='h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out relative overflow-hidden'
            style={{ width: `${progress}%` }}
          >
            {/* Animated shine effect */}
            <div className='absolute inset-0 -skew-x-12 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shine' />
          </div>
        </div>

        {/* Step indicators */}
        <div className='flex justify-between mt-4'>
          {Array.from({ length: totalSteps }, (_, index) => {
            const stepNumber = index + 1;
            const isCompleted = stepNumber <= completedSteps;
            const isCurrent = stepNumber === currentStep;
            const isFuture = stepNumber > currentStep;

            return (
              <div key={stepNumber} className='flex flex-col items-center'>
                {/* Step circle */}
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-all duration-300',
                    isCompleted && 'text-violet-600 text-white shadow-lg transform scale-110',
                    isCurrent &&
                      'text-violet-600 text-white shadow-lg ring-4 ring-blue-200 animate-pulse',
                    isFuture && 'bg-gray-200 text-gray-400',
                  )}
                >
                  {isCompleted ? (
                    <CheckCircle className='w-4 h-4' />
                  ) : isCurrent ? (
                    <Circle className='w-4 h-4 animate-pulse' />
                  ) : (
                    stepNumber
                  )}
                </div>

                {/* Step label */}
                <div
                  className={cn(
                    'mt-2 text-xs font-medium transition-colors',
                    isCompleted && 'text-green-600',
                    isCurrent && 'text-blue-600',
                    isFuture && 'text-gray-400',
                  )}
                >
                  Step {stepNumber}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Progress percentage */}
      <div className='mt-3 text-center'>
        <span className='text-lg font-semibold text-gray-900'>{Math.round(progress)}%</span>
        <span className='text-sm text-gray-500 ml-1'>Complete</span>
      </div>
    </div>
  );
}

// Re-export enhanced components
export { EnhancedProgress, SimpleTimelineProgress } from './ui/EnhancedProgress';
export { Timeline } from './ui/Timeline';

/* Enhanced Progress Bar for simple use cases */
interface SimpleProgressBarProps {
  current: number;
  total: number;
  className?: string;
  showSteps?: boolean;
}

export function SimpleProgressBar({
  current,
  total,
  className,
  showSteps = true,
}: SimpleProgressBarProps) {
  const progress = (current / total) * 100;

  return (
    <div className={cn('w-full', className)}>
      {showSteps && (
        <div className='flex justify-between text-sm text-gray-600 mb-2'>
          <span className='font-medium'>
            Question {current} of {total}
          </span>
          <span className='font-medium'>{Math.round(progress)}% Complete</span>
        </div>
      )}

      <div className='relative'>
        <div className='w-full bg-gray-200 rounded-full h-3 overflow-hidden'>
          <div
            className='h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500 ease-out relative'
            style={{ width: `${progress}%` }}
          >
            {/* Animated shimmer effect */}
            <div className='absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12 animate-shimmer' />
          </div>
        </div>
      </div>
    </div>
  );
}
