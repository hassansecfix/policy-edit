'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Timeline, TimelineStep } from '@/components/ui/Timeline';
import { CheckCircle, Clock, FileText, Play, Settings, Upload } from 'lucide-react';

interface ProcessFlowProps {
  currentStep: number;
  automationRunning?: boolean;
  filesReady?: boolean;
  className?: string;
}

export function ProcessFlow({
  currentStep,
  automationRunning = false,
  filesReady = false,
  className,
}: ProcessFlowProps) {
  const steps: TimelineStep[] = [
    {
      id: 1,
      title: 'Setup',
      description: 'Answer questionnaire about your organization',
      status: 'pending',
      icon: <Settings className='w-5 h-5' />,
    },
    {
      id: 2,
      title: 'Review',
      description: 'Preview document changes and customizations',
      status: 'pending',
      icon: <FileText className='w-5 h-5' />,
    },
    {
      id: 3,
      title: 'Generate',
      description: 'AI processes your policy document',
      status: 'pending',
      icon: automationRunning ? <Play className='w-5 h-5' /> : <Play className='w-5 h-5' />,
    },
    {
      id: 4,
      title: 'Complete',
      description: 'Download your customized policy',
      status: 'pending',
      icon: filesReady ? <CheckCircle className='w-5 h-5' /> : <Upload className='w-5 h-5' />,
    },
  ];

  return (
    <Card className={className}>
      <CardHeader className='text-center pb-4'>
        <CardTitle className='flex items-center justify-center gap-2 text-lg'>
          <Clock className='w-5 h-5 text-blue-600' />
          Process Flow
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Timeline steps={steps} currentStep={currentStep} orientation='vertical' />
      </CardContent>
    </Card>
  );
}
