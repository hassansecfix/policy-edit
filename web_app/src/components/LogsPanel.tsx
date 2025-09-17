'use client';

import { Badge } from '@/components/ui/Badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import type { LogEntry } from '@/types';
import { Terminal } from 'lucide-react';
import { useEffect, useRef } from 'react';

interface LogsPanelProps {
  logs: LogEntry[];
  logCount: number;
}

export function LogsPanel({ logs, logCount }: LogsPanelProps) {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new logs are added
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <Card className='border-0 overflow-hidden'>
      <CardHeader className='bg-gradient-to-r from-gray-800 to-gray-900 text-white border-b-0'>
        <div className='flex items-center justify-between'>
          <div>
            <CardTitle className='text-lg font-semibold text-white flex items-center gap-2'>
              <Terminal className='h-5 w-5' />
              Automation Logs
            </CardTitle>
            <CardDescription className='text-gray-300 mt-1'>
              Real-time automation progress and system messages
            </CardDescription>
          </div>
          <Badge variant='outline' className='bg-blue-600 border-blue-500 text-white'>
            {logCount} {logCount === 1 ? 'log' : 'logs'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className='p-0'>
        <div
          ref={logsContainerRef}
          className='h-[400px] overflow-y-auto bg-gray-900 text-gray-100 font-mono text-sm scrollbar-thin'
        >
          <div className='p-4 space-y-2'>
            {logs.length === 0 && (
              <div className='flex items-center gap-3 p-4 bg-blue-900/20 border border-blue-700/30 rounded-lg'>
                <div className='w-2 h-2 bg-blue-400 rounded-full animate-pulse'></div>
                <div className='flex-1'>
                  <div className='flex items-center gap-2 text-blue-300 text-xs mb-1'>
                    <span>System</span>
                    <span>•</span>
                    <span>--:--:--</span>
                  </div>
                  <div className='text-blue-100'>
                    🤖 Policy Automation Dashboard ready. Click "Start Policy Automation" to begin.
                  </div>
                </div>
              </div>
            )}

            {logs.map((log, index) => (
              <LogEntryComponent key={index} entry={log} />
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </CardContent>

      {logs.length > 0 && (
        <div className='px-4 py-3 bg-gray-800 border-t border-gray-700'>
          <p className='text-xs text-gray-400 text-center'>
            💡 Logs update in real-time during automation
          </p>
        </div>
      )}
    </Card>
  );
}

interface LogEntryComponentProps {
  entry: LogEntry;
  isWelcome?: boolean;
}

function LogEntryComponent({ entry, isWelcome = false }: LogEntryComponentProps) {
  const getLevelIndicator = () => {
    switch (entry.level) {
      case 'success':
        return <div className='w-2 h-2 bg-green-400 rounded-full'></div>;
      case 'error':
        return <div className='w-2 h-2 bg-red-400 rounded-full'></div>;
      case 'warning':
        return <div className='w-2 h-2 bg-yellow-400 rounded-full'></div>;
      case 'info':
      default:
        return <div className='w-2 h-2 bg-blue-400 rounded-full'></div>;
    }
  };

  const getLevelStyles = () => {
    switch (entry.level) {
      case 'success':
        return 'bg-green-900/20 border border-green-700/30 text-green-100';
      case 'error':
        return 'bg-red-900/20 border border-red-700/30 text-red-100';
      case 'warning':
        return 'bg-yellow-900/20 border border-yellow-700/30 text-yellow-100';
      case 'info':
      default:
        return isWelcome
          ? 'bg-green-900/20 border border-green-700/30 text-green-100'
          : 'bg-blue-900/20 border border-blue-700/30 text-blue-100';
    }
  };

  const getTextColor = () => {
    switch (entry.level) {
      case 'success':
        return 'text-green-300';
      case 'error':
        return 'text-red-300';
      case 'warning':
        return 'text-yellow-300';
      case 'info':
      default:
        return 'text-blue-300';
    }
  };

  return (
    <div className={cn('flex items-center gap-3 p-3 rounded-lg animate-fadeIn', getLevelStyles())}>
      {getLevelIndicator()}
      <div className='flex-1'>
        <div className={cn('flex items-center gap-2 text-xs mb-1', getTextColor())}>
          <span className='capitalize'>{entry.level}</span>
          <span>•</span>
          <span>{entry.timestamp}</span>
        </div>
        <div className='text-gray-100 text-sm break-words'>{entry.message}</div>
      </div>
    </div>
  );
}
