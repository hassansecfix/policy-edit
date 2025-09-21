'use client';

import { MultiStepLoader } from '@/components/ui/multi-step-loader';
import type { ProgressUpdate } from '@/types';

interface PolicyGenerationOverlayProps {
  isVisible: boolean;
  progress?: ProgressUpdate | null;
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

export const PolicyGenerationOverlay = ({ isVisible, progress }: PolicyGenerationOverlayProps) => {
  if (!isVisible) {
    return null;
  }

  // If overlay is visible, automation is running, so always show loading states

  return (
    <div className='absolute inset-0 bg-white/90 backdrop-blur-sm rounded-[6px] flex items-center justify-center z-50'>
      <MultiStepLoader
        loadingStates={loadingStates}
        loading={isVisible}
        duration={25000}
        loop={false}
      />
    </div>
  );
};
