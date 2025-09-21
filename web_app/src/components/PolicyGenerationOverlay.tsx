'use client';

import { MultiStepLoader } from '@/components/ui/multi-step-loader';
import type { ProgressUpdate } from '@/types';

interface PolicyGenerationOverlayProps {
  isVisible: boolean;
  progress?: ProgressUpdate | null;
  filesReady?: boolean;
}

const loadingStates = [
  { text: 'Gathering your answers...' },
  { text: 'Understanding your organization details...' },
  { text: 'Reviewing your security requirements...' },
  { text: 'Analyzing policy document...' },
  { text: 'Applying your answers to the policy document...' },
  { text: 'Finalizing document structure...' },
  { text: 'Almost ready! Adding finishing touches...' },
];

export const PolicyGenerationOverlay = ({
  isVisible,
  progress,
  filesReady,
}: PolicyGenerationOverlayProps) => {
  if (!isVisible) {
    return null;
  }

  // Get current loading states - show ALL states to cycle through once
  const getCurrentLoadingStates = () => {
    if (filesReady) {
      return [{ text: '✅ Policy document generated successfully!' }];
    }

    // Show all loading states - MultiStepLoader will cycle through them once and stop at last
    return loadingStates;
  };

  const currentStates = getCurrentLoadingStates();

  return (
    <div className='absolute inset-0 bg-white/90 backdrop-blur-sm rounded-[6px] flex items-center justify-center z-50'>
      <MultiStepLoader
        loadingStates={currentStates}
        loading={isVisible}
        duration={2000}
        loop={false}
      />
    </div>
  );
};
