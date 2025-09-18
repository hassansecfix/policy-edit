'use client';

import { cn } from '@/lib/utils';

interface SidebarStep {
  id: number;
  title: string;
  status: 'completed' | 'active' | 'pending';
}

interface SidebarProps {
  currentStep: number;
  className?: string;
}

export function Sidebar({ currentStep, className }: SidebarProps) {
  const steps: SidebarStep[] = [
    {
      id: 1,
      title: 'Questionnaire',
      status: currentStep > 1 ? 'completed' : currentStep === 1 ? 'active' : 'pending',
    },
    {
      id: 2,
      title: 'Automating',
      status: currentStep > 3 ? 'completed' : currentStep === 3 ? 'active' : 'pending',
    },
    {
      id: 3,
      title: 'Document Ready',
      status: currentStep > 4 ? 'completed' : currentStep === 4 ? 'active' : 'pending',
    },
  ];

  return (
    <div className={cn('w-full h-full flex flex-col', className)}>
      <div className='p-6 flex flex-col h-full gap-6'>
        <div className='bg-white border border-gray-200 rounded-lg p-6'>
          <h2 className='text-lg font-semibold text-gray-900'>Policy Configurator</h2>
        </div>

        <div className='flex flex-col flex-1 gap-1 bg-white border border-gray-200 rounded-lg p-6'>
          {steps.map((step) => (
            <div key={step.id} className='flex flex-col flex-1'>
              {/* Step Content and Line Container */}
              <div className='flex items-center h-full gap-2'>
                {/* Step Text */}
                <div className='flex-1 p-3 flex items-center'>
                  <h3
                    className={cn(
                      'font-semibold text-2xl transition-colors duration-200',
                      step.status === 'completed' && 'text-violet-600',
                      step.status === 'active' && 'text-violet-600',
                      step.status === 'pending' && 'text-gray-500',
                    )}
                  >
                    {step.title}
                  </h3>
                </div>

                {/* Vertical Line on Right */}
                <div className='flex flex-col items-center h-full'>
                  <div className='w-0.75 flex-1 bg-gray-200'>
                    <div
                      className={cn(
                        'w-full transition-all duration-500 ease-out bg-violet-600',
                        step.status === 'completed' ? 'h-full' : 'h-0',
                      )}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* AI Information Card */}
        <div className='bg-white border border-gray-200 rounded-lg p-6'>
          <div className='flex items-start gap-3'>
            <div>
              <h4 className='font-medium text-gray-900 text-sm mb-1'>AI-Powered Generation</h4>
              <p className='text-xs text-gray-600 leading-relaxed'>
                Complete the questionnaire to unlock our intelligent document generator. Our AI will
                analyze your responses and create a fully customized access control policy tailored
                to your organization&apos;s specific needs.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
