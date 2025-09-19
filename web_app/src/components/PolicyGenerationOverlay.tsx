'use client';

import { MultiStepLoader } from '@/components/ui/multi-step-loader';

interface PolicyGenerationOverlayProps {
  isVisible: boolean;
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

export const PolicyGenerationOverlay = ({ isVisible }: PolicyGenerationOverlayProps) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div className='absolute inset-0 bg-white/90 backdrop-blur-sm rounded-[6px] flex items-center justify-center z-50'>
      <MultiStepLoader loadingStates={loadingStates} loading={true} duration={10000} loop={false} />
    </div>
  );
};
