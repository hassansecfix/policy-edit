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
      className={cn('w-6 h-6 ', className)}
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
      className={cn('w-6 h-6 ', className)}
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
    <div className='flex flex-col w-full max-w-4xl mx-auto p-6'>
      {loadingStates.map((loadingState, index) => {
        const distance = Math.abs(index - value);
        const opacity = Math.max(1 - distance * 0.2, 0);

        return (
          <div
            key={index}
            className={cn(
              'text-left flex gap-3 mb-3 p-3 rounded-lg transition-all duration-500 ease-out',
              index < value
                ? 'bg-green-50 border-l-4 border-green-400 text-green-800'
                : index === value
                ? 'bg-blue-50 border-l-4 border-blue-400 text-blue-800 animate-fadeIn'
                : 'bg-gray-50 text-gray-600',
            )}
            style={{
              opacity: opacity,
            }}
          >
            <div className='flex-shrink-0 mt-0.5'>
              {index > value && <CheckIcon className='text-gray-400' />}
              {index === value && (
                <div className='w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full animate-spin' />
              )}
              {index < value && <CheckFilled className='text-green-500' />}
            </div>
            <span className='font-medium text-sm flex-1'>{loadingState.text}</span>
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
    <div className='w-full bg-white rounded-lg border shadow-sm'>
      <div className='bg-gradient-to-r from-blue-500 to-indigo-500 text-white p-4 rounded-t-lg'>
        <h3 className='font-semibold text-lg'>🤖 Automation Progress</h3>
        <p className='text-blue-100 text-sm mt-1'>Real-time progress of your policy automation</p>
      </div>
      <LoaderCore value={currentState} loadingStates={loadingStates} />
    </div>
  );
};
