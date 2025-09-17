'use client';

import { Button } from '@/components/ui/Button';
import { API_CONFIG, getApiUrl } from '@/config/api';
import type { SystemStatus } from '@/types';
import { Play, Square, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ControlPanelProps {
  onStartAutomation: (skipApi: boolean) => void;
  onStopAutomation: () => void;
  onClearLogs: () => void;
  automationRunning: boolean;
}

export function ControlPanel({
  onStartAutomation,
  onStopAutomation,
  onClearLogs,
  automationRunning,
}: ControlPanelProps) {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.status));
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to check status:', error);
    }
  };

  const handleStart = () => {
    onStartAutomation(false); // Always use API (not skip)
  };

  if (!status) {
    return (
      <div className='flex justify-center'>
        <div className='animate-pulse'>
          <div className='h-12 bg-gray-200 rounded-xl w-64'></div>
        </div>
      </div>
    );
  }

  const canStart =
    status.policy_exists &&
    status.questionnaire_exists &&
    status.api_key_configured &&
    !automationRunning;

  return (
    <div className='flex flex-col items-center gap-4'>
      {/* Main Action Button */}
      <Button
        onClick={handleStart}
        disabled={!canStart}
        loading={automationRunning}
        variant={canStart ? 'success' : 'secondary'}
        size='xl'
        className='min-w-[280px]'
      >
        {automationRunning ? (
          'Processing Automation...'
        ) : (
          <>
            <Play className='h-5 w-5' />
            Start Policy Automation
          </>
        )}
      </Button>

      {/* Control Buttons when running */}
      {automationRunning && (
        <div className='flex gap-3 justify-center mt-2'>
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
