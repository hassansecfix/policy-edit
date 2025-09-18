'use client';

import { Questionnaire } from '@/components/Questionnaire';
import type { QuestionnaireAnswer } from '@/types';
import { useCallback } from 'react';

interface ExpandableQuestionnaireProps {
  isExpanded: boolean;
  onToggle: () => void;
  onComplete: (answers: Record<string, QuestionnaireAnswer>) => void;
  onProgressUpdate?: (progress: { current: number; total: number }) => void;
  onStartAutomation?: () => Promise<void>;
  automationRunning?: boolean;
}

export function ExpandableQuestionnaire({
  onComplete,
  onProgressUpdate,
  onStartAutomation,
  automationRunning,
}: ExpandableQuestionnaireProps) {
  const handleComplete = useCallback(
    async (answers: Record<string, QuestionnaireAnswer>) => {
      await onComplete(answers);
    },
    [onComplete],
  );

  return (
    <div className='mb-6'>
      <Questionnaire 
        onComplete={handleComplete} 
        onProgressUpdate={onProgressUpdate || (() => {})} 
        onStartAutomation={onStartAutomation}
        automationRunning={automationRunning}
      />
    </div>
  );
}
