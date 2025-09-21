'use client';

import { Questionnaire } from '@/components/Questionnaire';
import type { ProgressUpdate, QuestionnaireAnswer } from '@/types';
import { useCallback } from 'react';

interface ExpandableQuestionnaireProps {
  isExpanded: boolean;
  onToggle: () => void;
  onComplete: (answers: Record<string, QuestionnaireAnswer>) => void;
  onProgressUpdate?: (progress: { current: number; total: number }) => void;
  onStartAutomation?: () => Promise<void>;
  onSetAutomationRunning?: (running: boolean) => void;
  automationRunning?: boolean;
  progress?: ProgressUpdate | null;
  filesReady?: boolean;
}

export function ExpandableQuestionnaire({
  onComplete,
  onProgressUpdate,
  onStartAutomation,
  onSetAutomationRunning,
  automationRunning,
  progress,
  filesReady = false,
}: ExpandableQuestionnaireProps) {
  const handleComplete = useCallback(
    async (answers: Record<string, QuestionnaireAnswer>) => {
      await onComplete(answers);
    },
    [onComplete],
  );

  return (
    <div className='mb-6 w-full max-w-full overflow-hidden min-w-0'>
      <Questionnaire
        onComplete={handleComplete}
        onProgressUpdate={onProgressUpdate || (() => {})}
        onStartAutomation={onStartAutomation}
        onSetAutomationRunning={onSetAutomationRunning}
        automationRunning={automationRunning}
        progress={progress}
        filesReady={filesReady}
      />
    </div>
  );
}
