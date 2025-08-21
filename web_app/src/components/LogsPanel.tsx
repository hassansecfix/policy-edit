'use client';

import { cn } from '@/lib/utils';
import type { LogEntry } from '@/types';
import { Terminal } from 'lucide-react';
import { useRef } from 'react';

interface LogsPanelProps {
  logs: LogEntry[];
  logCount: number;
}

export function LogsPanel({ logs, logCount }: LogsPanelProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // useEffect(() => {
  //   // Auto-scroll to bottom when new logs are added
  //   if (logsEndRef.current) {
  //     logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
  //   }
  // }, [logs]);

  return (
    <div className='bg-white rounded-lg shadow-sm border'>
      <div className='bg-gradient-to-r from-gray-800 to-gray-900 text-white p-4 rounded-t-lg flex justify-between items-center'>
        <h3 className='font-semibold flex items-center gap-2'>
          <Terminal className='h-5 w-5' />
          Automation Logs
        </h3>
        <span className='bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium'>
          {logCount} logs
        </span>
      </div>

      <div
        ref={logsContainerRef}
        className='h-[500px] overflow-y-auto bg-gray-900 text-gray-100 font-mono text-sm'
      >
        <div className='p-4 space-y-2'>
          {logs.length === 0 && (
            <LogEntryComponent
              entry={{
                timestamp: '--:--:--',
                message:
                  '🤖 Policy Automation Dashboard ready. Click "Start Policy Automation" to begin.',
                level: 'info',
              }}
              isWelcome
            />
          )}

          {logs.map((log, index) => (
            <LogEntryComponent key={index} entry={log} />
          ))}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}

interface LogEntryComponentProps {
  entry: LogEntry;
  isWelcome?: boolean;
}

function LogEntryComponent({ entry, isWelcome = false }: LogEntryComponentProps) {
  const getLevelStyles = () => {
    switch (entry.level) {
      case 'success':
        return 'bg-green-900/30 border-l-4 border-green-400 text-green-100';
      case 'error':
        return 'bg-red-900/30 border-l-4 border-red-400 text-red-100';
      case 'warning':
        return 'bg-yellow-900/30 border-l-4 border-yellow-400 text-yellow-100';
      case 'info':
      default:
        return isWelcome
          ? 'bg-green-900/30 border-l-4 border-green-400 text-green-100'
          : 'bg-blue-900/30 border-l-4 border-blue-400 text-blue-100';
    }
  };

  return (
    <div className={cn('flex gap-3 p-3 rounded-lg animate-fadeIn', getLevelStyles())}>
      <span className='text-gray-400 text-xs min-w-[80px] flex-shrink-0 mt-0.5'>
        {entry.timestamp}
      </span>
      <span className='flex-1 break-words'>{entry.message}</span>
    </div>
  );
}
