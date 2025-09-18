'use client';

import { MultiStepLoader } from '@/components/ui/multi-step-loader';

interface PolicyGenerationOverlayProps {
  isVisible: boolean;
}

const loadingStates = [
  { text: 'Analyzing your organization details...' },
  { text: 'Understanding your security requirements...' },
  { text: 'Reviewing industry best practices...' },
  { text: 'Generating custom policy content...' },
  { text: 'Tailoring policies to your needs...' },
  { text: 'Applying security frameworks...' },
  { text: 'Finalizing document structure...' },
  { text: 'Almost ready! Adding finishing touches...' },
];

export const PolicyGenerationOverlay = ({ isVisible }: PolicyGenerationOverlayProps) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div className='absolute inset-0 bg-white/90 backdrop-blur-sm rounded-[6px] flex items-center justify-center z-50'>
      <MultiStepLoader loadingStates={loadingStates} loading={true} duration={2500} loop={true} />
    </div>
  );
};
