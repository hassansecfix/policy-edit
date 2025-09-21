'use client';

import { MultiStepLoader } from '@/components/ui/multi-step-loader';
import type { ProgressUpdate } from '@/types';

interface PolicyGenerationOverlayProps {
  isVisible: boolean;
  progress?: ProgressUpdate | null;
  filesReady?: boolean;
}

const loadingStates = [
  { text: 'Processing your answers...' },
  { text: 'AI understanding your organization details...' },
  { text: 'Analyzing your security requirements...' },
  { text: 'Reviewing policy document structure...' },
  { text: 'AI generating personalized policy content...' },
  { text: 'Finalizing document formatting...' },
  { text: 'Almost ready! AI completing final checks...' },
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
        duration={100000}
        loop={false}
      />
    </div>
  );
};
