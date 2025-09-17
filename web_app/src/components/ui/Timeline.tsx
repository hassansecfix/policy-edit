'use client';

import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { Check, Circle, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

export interface TimelineStep {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  icon?: React.ReactNode;
}

interface TimelineProps {
  steps: TimelineStep[];
  currentStep: number;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
}

export function Timeline({
  steps,
  currentStep,
  className,
  orientation = 'horizontal',
}: TimelineProps) {
  const [animatedSteps, setAnimatedSteps] = useState<TimelineStep[]>(steps);

  useEffect(() => {
    setAnimatedSteps(
      steps.map((step, index) => ({
        ...step,
        status:
          index < currentStep - 1 ? 'completed' : index === currentStep - 1 ? 'active' : 'pending',
      })),
    );
  }, [steps, currentStep]);

  if (orientation === 'vertical') {
    return (
      <div className={cn('relative', className)}>
        {animatedSteps.map((step, index) => (
          <VerticalTimelineItem
            key={step.id}
            step={step}
            index={index}
            isLast={index === animatedSteps.length - 1}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      <HorizontalTimeline steps={animatedSteps} currentStep={currentStep} />
    </div>
  );
}

function HorizontalTimeline({
  steps,
  currentStep,
}: {
  steps: TimelineStep[];
  currentStep: number;
}) {
  return (
    <div className='relative'>
      {/* Background Progress Line */}
      <div className='absolute top-6 left-6 right-6 h-0.5 bg-gray-200 rounded-full'></div>

      {/* Active Progress Line */}
      <div
        className='absolute top-6 left-6 h-0.5 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-1000 ease-out'
        style={{
          width: `calc(${Math.max(0, (currentStep - 1) / (steps.length - 1)) * 100}% - 1.5rem)`,
        }}
      >
        {/* Animated Glow Effect */}
        <div className='absolute inset-0 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full animate-pulse opacity-50'></div>
      </div>

      {/* Steps */}
      <div className='relative flex justify-between'>
        {steps.map((step, index) => (
          <HorizontalTimelineStep
            key={step.id}
            step={step}
            index={index}
            currentStep={currentStep}
          />
        ))}
      </div>
    </div>
  );
}

function HorizontalTimelineStep({
  step,
  index,
  currentStep,
}: {
  step: TimelineStep;
  index: number;
  currentStep: number;
}) {
  const isCompleted = index < currentStep - 1;
  const isActive = index === currentStep - 1;
  const isPending = index >= currentStep;

  return (
    <div className='flex flex-col items-center relative group'>
      {/* Step Circle */}
      <div
        className={cn(
          'relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 transform',
          'ring-4 ring-white shadow-lg',
          isCompleted && 'bg-gradient-to-br from-green-500 to-emerald-600 scale-110',
          isActive &&
            'bg-gradient-to-br from-blue-500 to-indigo-600 scale-125 shadow-xl shadow-blue-500/25',
          isPending && 'bg-gray-200 scale-100',
        )}
      >
        {/* Animated Border for Active Step */}
        {isActive && (
          <div className='absolute inset-0 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 animate-spin-slow opacity-20'></div>
        )}

        {/* Step Icon */}
        <div
          className={cn(
            'relative z-10 transition-all duration-300',
            isCompleted && 'text-white',
            isActive && 'text-white',
            isPending && 'text-gray-400',
          )}
        >
          {isCompleted ? (
            <Check className='w-5 h-5' />
          ) : isActive ? (
            <Loader2 className='w-5 h-5 animate-spin' />
          ) : (
            <Circle className='w-5 h-5' />
          )}
        </div>

        {/* Pulse Animation for Active Step */}
        {isActive && (
          <div className='absolute inset-0 rounded-full bg-violet-600 animate-ping opacity-20'></div>
        )}
      </div>

      {/* Step Content */}
      <div className='mt-4 text-center max-w-32'>
        <h3
          className={cn(
            'text-sm font-medium transition-colors duration-300',
            isCompleted && 'bg-violet-600',
            isActive && 'text-blue-700',
            isPending && 'text-gray-500',
          )}
        >
          {step.title}
        </h3>
        <p
          className={cn(
            'text-xs mt-1 transition-colors duration-300',
            isCompleted && 'text-green-600',
            isActive && 'text-blue-600',
            isPending && 'text-gray-400',
          )}
        >
          {step.description}
        </p>

        {/* Status Badge */}
        <div className='mt-2'>
          {isCompleted && (
            <Badge variant='success' className='text-xs animate-fadeIn'>
              Complete
            </Badge>
          )}
          {isActive && (
            <Badge variant='default' className='text-xs animate-pulse'>
              In Progress
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}

function VerticalTimelineItem({
  step,
  index,
  isLast,
}: {
  step: TimelineStep;
  index: number;
  isLast: boolean;
}) {
  const isCompleted = step.status === 'completed';
  const isActive = step.status === 'active';
  const isPending = step.status === 'pending';

  return (
    <div className='relative flex items-start group'>
      {/* Connector Line */}
      {!isLast && (
        <div className='absolute left-6 top-12 w-0.5 h-16 bg-gray-200'>
          <div
            className={cn(
              'w-full transition-all duration-1000 ease-out',
              'bg-gradient-to-b from-blue-500 to-indigo-600',
              isCompleted ? 'h-full' : 'h-0',
            )}
          ></div>
        </div>
      )}

      {/* Step Circle */}
      <div
        className={cn(
          'relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500',
          'ring-4 ring-white shadow-lg z-10',
          isCompleted && 'bg-gradient-to-br from-green-500 to-emerald-600',
          isActive && 'bg-gradient-to-br from-blue-500 to-indigo-600 shadow-xl shadow-blue-500/25',
          isPending && 'bg-gray-200',
        )}
      >
        <div
          className={cn(
            'transition-colors duration-300',
            isCompleted && 'text-white',
            isActive && 'text-white',
            isPending && 'text-gray-400',
          )}
        >
          {step.icon ||
            (isCompleted ? (
              <Check className='w-5 h-5' />
            ) : isActive ? (
              <Loader2 className='w-5 h-5 animate-spin' />
            ) : (
              <Circle className='w-5 h-5' />
            ))}
        </div>

        {isActive && (
          <div className='absolute inset-0 rounded-full bg-violet-600 animate-ping opacity-20'></div>
        )}
      </div>

      {/* Content */}
      <div className='ml-6 pb-8'>
        <h3
          className={cn(
            'font-medium transition-colors duration-300',
            isCompleted && 'bg-violet-600',
            isActive && 'text-blue-700',
            isPending && 'text-gray-500',
          )}
        >
          {step.title}
        </h3>
        <p
          className={cn(
            'text-sm mt-1 transition-colors duration-300',
            isCompleted && 'text-green-600',
            isActive && 'text-blue-600',
            isPending && 'text-gray-400',
          )}
        >
          {step.description}
        </p>

        <div className='mt-2'>
          {isCompleted && (
            <Badge variant='success' className='text-xs'>
              Completed
            </Badge>
          )}
          {isActive && (
            <Badge variant='default' className='text-xs'>
              Active
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}
