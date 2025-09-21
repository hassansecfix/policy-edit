'use client';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

const SpinnerIcon = ({ className }: { className?: string }) => {
  return (
    <div
      className={cn(
        'w-4 h-4 border-2 border-violet-300 border-t-violet-600 rounded-full animate-spin',
        className,
      )}
    />
  );
};

type LoadingState = {
  text: string;
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

  // Reset to first state when loading starts
  useEffect(() => {
    if (loading && loadingStates.length > 0) {
      setCurrentState(0);
    }
  }, [loading, loadingStates.length]);

  useEffect(() => {
    if (!loading) {
      setCurrentState(0);
      return;
    }

    // If we only have one state, don't set up a timeout (stay on that state)
    if (loadingStates.length === 1) {
      setCurrentState(0); // Make sure we show the single state
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

  const currentLoadingState = loadingStates[currentState];

  return (
    <div className='flex items-center gap-3 px-6 py-4'>
      <SpinnerIcon />
      <span className='text-sm font-medium text-violet-600'>
        {currentLoadingState?.text || 'Processing...'}
      </span>
    </div>
  );
};
