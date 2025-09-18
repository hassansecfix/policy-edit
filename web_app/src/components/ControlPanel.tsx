'use client';

import { Button } from '@/components/ui/Button';
import { Square, Trash2 } from 'lucide-react';

interface ControlPanelProps {
  onStopAutomation: () => void;
  onClearLogs: () => void;
  automationRunning: boolean;
}

export function ControlPanel({
  onStopAutomation,
  onClearLogs,
  automationRunning,
}: ControlPanelProps) {
  return (
    <div className='flex flex-col items-center gap-4'>
      {/* Control Buttons when automation is running */}
      {automationRunning && (
        <div className='flex gap-3 justify-center'>
          <Button onClick={onStopAutomation} variant='destructive' size='sm'>
            <Square className='h-4 w-4' />
            Stop
          </Button>
          <Button onClick={onClearLogs} variant='secondary' size='sm'>
            <Trash2 className='h-4 w-4' />
            Clear Logs
          </Button>
        </div>
      )}
    </div>
  );
}
