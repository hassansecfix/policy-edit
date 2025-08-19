'use client';

import { API_CONFIG, getApiUrl } from '@/config/api';
import { cn } from '@/lib/utils';
import type { SystemStatus } from '@/types';
import { Play, Settings, Square, Trash2 } from 'lucide-react';
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
  const [skipApi, setSkipApi] = useState(false);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.status));
      const data = await response.json();
      setStatus(data);
      setSkipApi(data.skip_api);
    } catch (error) {
      console.error('Failed to check status:', error);
    }
  };

  const handleStart = () => {
    onStartAutomation(skipApi);
  };

  if (!status) {
    return (
      <div className='bg-white rounded-lg shadow-sm border p-6'>
        <div className='animate-pulse'>
          <div className='h-4 bg-gray-200 rounded w-1/4 mb-4'></div>
          <div className='space-y-3'>
            <div className='h-4 bg-gray-200 rounded'></div>
            <div className='h-4 bg-gray-200 rounded'></div>
            <div className='h-4 bg-gray-200 rounded'></div>
          </div>
        </div>
      </div>
    );
  }

  const canStart =
    status.policy_exists &&
    status.questionnaire_exists &&
    (status.api_key_configured || status.skip_api) &&
    !automationRunning;

  return (
    <div className='space-y-6'>
      {/* Configuration Status */}
      <div className='bg-white rounded-lg shadow-sm border'>
        <div className='bg-gradient-to-r from-pink-500 to-rose-500 text-white p-4 rounded-t-lg'>
          <h3 className='font-semibold flex items-center gap-2'>
            <Settings className='h-5 w-5' />
            Control Panel
          </h3>
        </div>
        <div className='p-6'>
          <div className='mb-6'>
            <h4 className='font-medium text-gray-900 mb-4'>Configuration Status</h4>
            <div className='space-y-3'>
              <StatusItem
                label='Policy File'
                status={status.policy_exists}
                value={status.policy_exists ? 'Found' : 'Missing'}
              />
              <StatusItem
                label='Questionnaire'
                status={status.questionnaire_exists}
                value={status.questionnaire_exists ? 'Found' : 'Missing'}
              />
              <StatusItem
                label='API Key'
                status={status.api_key_configured}
                value={
                  status.api_key_configured
                    ? status.skip_api
                      ? 'Not Required'
                      : 'Configured'
                    : 'Missing'
                }
              />
              <StatusItem
                label='Skip API'
                status={true}
                value={status.skip_api ? 'Yes' : 'No'}
                variant={status.skip_api ? 'warning' : 'info'}
              />
            </div>
          </div>

          <div className='mb-6'>
            <label className='flex items-center space-x-3'>
              <input
                type='checkbox'
                checked={skipApi}
                onChange={(e) => setSkipApi(e.target.checked)}
                className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
              />
              <span className='text-sm font-medium text-gray-700'>
                Skip API Call (use existing JSON)
              </span>
            </label>
            <p className='text-xs text-gray-500 mt-1 ml-7'>
              Enable this to save costs during testing
            </p>
          </div>

          <button
            onClick={handleStart}
            disabled={!canStart}
            className={cn(
              'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-all',
              canStart && !automationRunning
                ? 'bg-green-600 hover:bg-green-700 text-white shadow-sm'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed',
            )}
          >
            {automationRunning ? (
              <>
                <div className='animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent' />
                Running...
              </>
            ) : (
              <>
                <Play className='h-4 w-4' />
                Start Policy Automation
              </>
            )}
          </button>

          {automationRunning && (
            <div className='flex gap-2 mt-3'>
              <button
                onClick={onStopAutomation}
                className='flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors'
              >
                <Square className='h-4 w-4' />
                Stop
              </button>
              <button
                onClick={onClearLogs}
                className='flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg font-medium transition-colors'
              >
                <Trash2 className='h-4 w-4' />
                Clear Logs
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface StatusItemProps {
  label: string;
  status: boolean;
  value: string;
  variant?: 'success' | 'error' | 'warning' | 'info';
}

function StatusItem({ label, status, value, variant }: StatusItemProps) {
  const getVariantClasses = () => {
    if (variant === 'warning') return 'bg-yellow-100 text-yellow-800';
    if (variant === 'info') return 'bg-blue-100 text-blue-800';
    return status ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
  };

  return (
    <div className='flex justify-between items-center'>
      <span className='text-sm text-gray-600'>{label}:</span>
      <span className={cn('px-2 py-1 rounded-full text-xs font-medium', getVariantClasses())}>
        {value}
      </span>
    </div>
  );
}
