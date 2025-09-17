'use client';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

const CheckIcon = ({ className }: { className?: string }) => {
  return (
    <svg
      xmlns='http://www.w3.org/2000/svg'
      fill='none'
      viewBox='0 0 24 24'
      strokeWidth={1.5}
      stroke='currentColor'
      className={cn('w-5 h-5', className)}
    >
      <path d='M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z' />
    </svg>
  );
};

const CheckFilled = ({ className }: { className?: string }) => {
  return (
    <svg
      xmlns='http://www.w3.org/2000/svg'
      viewBox='0 0 24 24'
      fill='currentColor'
      className={cn('w-5 h-5', className)}
    >
      <path
        fillRule='evenodd'
        d='M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z'
        clipRule='evenodd'
      />
    </svg>
  );
};

type LoadingState = {
  text: string;
};

const LoaderCore = ({
  loadingStates,
  value = 0,
}: {
  loadingStates: LoadingState[];
  value?: number;
}) => {
  return (
    <div className='p-6'>
      {loadingStates.map((loadingState, index) => {
        return (
          <div
            key={index}
            className={cn(
              'flex items-center gap-3 p-3 mb-3 rounded-lg transition-all duration-300 ease-out',
              index < value
                ? 'bg-violet-50 text-violet-800'
                : index === value
                ? 'bg-gray-100 text-gray-800'
                : 'bg-gray-50 text-gray-500',
            )}
          >
            <div className='flex-shrink-0 w-5'>
              {index > value && <CheckIcon className='text-gray-400 w-5 h-5' />}
              {index === value && (
                <div className='w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin m-auto' />
              )}
              {index < value && <CheckFilled className='text-violet-600 w-5 h-5' />}
            </div>
            <span className='text-sm font-medium flex-1'>{loadingState.text}</span>
          </div>
        );
      })}
    </div>
  );
};

export const MultiStepLoader = ({
  loadingStates,
  loading,
  duration = 2000,
  loop = true,
}: {
  loadingStates: LoadingState[];
  loading?: boolean;
  duration?: number;
  loop?: boolean;
}) => {
  const [currentState, setCurrentState] = useState(0);

  useEffect(() => {
    if (!loading) {
      setCurrentState(0);
      return;
    }
    const timeout = setTimeout(() => {
      setCurrentState((prevState) =>
        loop
          ? prevState === loadingStates.length - 1
            ? 0
            : prevState + 1
          : Math.min(prevState + 1, loadingStates.length - 1),
      );
    }, duration);

    return () => clearTimeout(timeout);
  }, [currentState, loading, loop, loadingStates.length, duration]);
  if (!loading) {
    return null;
  }

  return (
    <div className='w-full rounded-xl border border-gray-200 bg-white overflow-hidden'>
      <div className='text-gray-900 px-6 py-4 border-b border-gray-200'>
        <h3 className='font-semibold text-lg'>🤖 Automation Progress</h3>
        <p className='text-gray-500 text-sm mt-1'>Real-time progress of your policy automation</p>
      </div>
      <LoaderCore value={currentState} loadingStates={loadingStates} />
    </div>
  );
};
