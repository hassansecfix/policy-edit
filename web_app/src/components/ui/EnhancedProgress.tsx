'use client';

import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Timeline, TimelineStep } from '@/components/ui/Timeline';
import { cn } from '@/lib/utils';
import { Clock, FileText, Play, Settings } from 'lucide-react';

interface EnhancedProgressProps {
  currentStep: number;
  totalSteps: number;
  title?: string;
  subtitle?: string;
  className?: string;
  variant?: 'default' | 'compact';
}

export function EnhancedProgress({
  currentStep,
  totalSteps,
  title = 'Progress',
  subtitle,
  className,
  variant = 'default',
}: EnhancedProgressProps) {
  const steps: TimelineStep[] = [
    {
      id: 1,
      title: 'Questions',
      description: 'Answer about your organization',
      status: 'pending',
      icon: <Settings className='w-5 h-5' />,
    },
    {
      id: 2,
      title: 'Review',
      description: 'Check document changes',
      status: 'pending',
      icon: <FileText className='w-5 h-5' />,
    },
    {
      id: 3,
      title: 'Generate',
      description: 'Create policy document',
      status: 'pending',
      icon: <Play className='w-5 h-5' />,
    },
    {
      id: 4,
      title: 'Download',
      description: 'Get your custom policy',
      status: 'pending',
      icon: <FileText className='w-5 h-5' />,
    },
  ];

  const progressPercentage = Math.round((currentStep / totalSteps) * 100);

  if (variant === 'compact') {
    return (
      <div className={cn('w-full', className)}>
        <div className='flex items-center justify-between mb-3'>
          <div className='flex items-center gap-2'>
            <h3 className='font-medium text-gray-900'>{title}</h3>
            {subtitle && <span className='text-sm text-gray-500'>• {subtitle}</span>}
          </div>
          <Badge variant='outline' className='text-xs'>
            Step {currentStep} of {totalSteps}
          </Badge>
        </div>

        <Timeline steps={steps} currentStep={currentStep} orientation='horizontal' />

        <div className='mt-4 text-center'>
          <div className='flex items-center justify-center gap-2'>
            <Clock className='w-4 h-4 text-gray-400' />
            <span className='text-sm text-gray-600'>{progressPercentage}% Complete</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Card className={cn('border-0 overflow-hidden', className)}>
      <CardHeader className='bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100'>
        <div className='flex items-center justify-between'>
          <div>
            <CardTitle className='text-xl font-semibold text-gray-900 flex items-center gap-2'>
              📋 {title}
            </CardTitle>
            {subtitle && (
              <CardDescription className='mt-1 text-gray-600'>{subtitle}</CardDescription>
            )}
          </div>
          <div className='text-right'>
            <Badge variant='outline' className='mb-2'>
              Step {currentStep} of {totalSteps}
            </Badge>
            <div className='text-2xl font-bold text-blue-600'>{progressPercentage}%</div>
            <div className='text-xs text-gray-500'>Complete</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className='p-8'>
        <Timeline steps={steps} currentStep={currentStep} orientation='horizontal' />

        {/* Progress Bar */}
        <div className='mt-8'>
          <div className='w-full bg-gray-200 rounded-full h-2 overflow-hidden'>
            <div
              className='h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-1000 ease-out relative overflow-hidden'
              style={{ width: `${progressPercentage}%` }}
            >
              {/* Animated shine effect */}
              <div className='absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12 animate-shimmer' />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Simplified Progress Bar for inline use
interface SimpleTimelineProgressProps {
  current: number;
  total: number;
  className?: string;
  showPercentage?: boolean;
}

export function SimpleTimelineProgress({
  current,
  total,
  className,
  showPercentage = true,
}: SimpleTimelineProgressProps) {
  const progress = (current / total) * 100;

  return (
    <div className={cn('w-full', className)}>
      <div className='flex justify-between items-center mb-3'>
        <span className='text-sm font-medium text-gray-700'>
          Question {current} of {total}
        </span>
        {showPercentage && (
          <span className='text-sm font-medium text-blue-600'>{Math.round(progress)}%</span>
        )}
      </div>

      <div className='relative'>
        <div className='w-full bg-gray-200 rounded-full h-3 overflow-hidden'>
          <div
            className='h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500 ease-out relative'
            style={{ width: `${progress}%` }}
          >
            {/* Animated shimmer effect */}
            <div className='absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent -skew-x-12 animate-shimmer' />

            {/* Pulse effect for active progress */}
            <div className='absolute right-0 top-0 w-3 h-full bg-blue-400 rounded-full animate-pulse opacity-75' />
          </div>
        </div>
      </div>
    </div>
  );
}
