'use client';

import { cn } from '@/lib/utils';
import type { AutomationStep, ProgressUpdate } from '@/types';
import { CheckCircle, Loader2, TrendingUp, XCircle } from 'lucide-react';

interface ProgressTrackerProps {
  progress: ProgressUpdate | null;
}

export function ProgressTracker({ progress }: ProgressTrackerProps) {
  const steps: AutomationStep[] = [
    { id: 1, title: 'Preparing environment', icon: 'loader', status: 'pending' },
    { id: 2, title: 'Processing questionnaire', icon: 'loader', status: 'pending' },
    { id: 3, title: 'Generating AI edits', icon: 'loader', status: 'pending' },
    { id: 4, title: 'Triggering GitHub Actions', icon: 'loader', status: 'pending' },
    { id: 5, title: 'Complete', icon: 'loader', status: 'pending' },
  ];

  // Update step statuses based on progress
  const updatedSteps = steps.map((step) => {
    if (!progress) return step;

    if (step.id < progress.step) {
      return { ...step, status: 'completed' as const };
    } else if (step.id === progress.step) {
      return { ...step, status: progress.status };
    }
    return step;
  });

  const progressPercentage = progress?.progress || 0;

  return (
    <div className='bg-white rounded-lg border'>
      <div className='bg-gradient-to-r from-blue-500 to-indigo-500 text-white p-4 rounded-t-lg'>
        <h3 className='font-semibold flex items-center gap-2'>
          <TrendingUp className='h-5 w-5' />
          Progress
        </h3>
      </div>
      <div className='p-6'>
        {/* Progress Bar */}
        <div className='mb-6'>
          <div className='w-full bg-gray-200 rounded-full h-2'>
            <div
              className='bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-500 ease-out'
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className='text-sm text-gray-600 mt-2 text-center'>
            {Math.round(progressPercentage)}% complete
          </div>
        </div>

        {/* Steps */}
        <div className='space-y-3'>
          {updatedSteps.map((step) => (
            <StepItem key={step.id} step={step} />
          ))}
        </div>
      </div>
    </div>
  );
}

interface StepItemProps {
  step: AutomationStep;
}

function StepItem({ step }: StepItemProps) {
  const getIcon = () => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className='h-4 w-4 text-green-500' />;
      case 'error':
        return <XCircle className='h-4 w-4 text-red-500' />;
      case 'active':
        return <Loader2 className='h-4 w-4 text-blue-500 animate-spin' />;
      default:
        return <div className='h-4 w-4 rounded-full border-2 border-gray-300' />;
    }
  };

  const getBackgroundClass = () => {
    switch (step.status) {
      case 'completed':
        return 'bg-green-50 border-l-4 border-green-400';
      case 'error':
        return 'bg-red-50 border-l-4 border-red-400';
      case 'active':
        return 'bg-blue-50 border-l-4 border-blue-400';
      default:
        return 'bg-gray-50';
    }
  };

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg transition-all duration-300',
        getBackgroundClass(),
      )}
    >
      {getIcon()}
      <span
        className={cn(
          'font-medium text-sm',
          step.status === 'completed'
            ? 'text-violet-600'
            : step.status === 'error'
            ? 'text-red-700'
            : step.status === 'active'
            ? 'text-blue-700'
            : 'text-gray-600',
        )}
      >
        {step.title}
      </span>
    </div>
  );
}
