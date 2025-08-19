'use client';

import { ConnectionStatus } from '@/components/ConnectionStatus';
import { ControlPanel } from '@/components/ControlPanel';
import { DownloadSection } from '@/components/DownloadSection';
import { Header } from '@/components/Header';
import { LogsPanel } from '@/components/LogsPanel';
import { ProgressTracker } from '@/components/ProgressTracker';
import { API_CONFIG, getApiUrl } from '@/config/api';
import { useSocket } from '@/hooks/useSocket';
import { formatTime } from '@/lib/utils';
import { useCallback, useState } from 'react';

export default function Dashboard() {
  const [automationRunning, setAutomationRunning] = useState(false);
  const { socket, isConnected, logs, progress, files, clearLogs, addLog } = useSocket();

  const handleStartAutomation = useCallback(
    async (skipApi: boolean) => {
      try {
        const response = await fetch(getApiUrl(API_CONFIG.endpoints.start), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ skip_api: skipApi }),
        });

        if (response.ok) {
          setAutomationRunning(true);
          addLog({
            timestamp: formatTime(new Date()),
            message: '🚀 Automation started successfully',
            level: 'success',
          });
        } else {
          const error = await response.json();
          addLog({
            timestamp: formatTime(new Date()),
            message: `❌ Failed to start automation: ${error.error}`,
            level: 'error',
          });
        }
      } catch (error) {
        console.error('Failed to start automation:', error);
        addLog({
          timestamp: formatTime(new Date()),
          message: '❌ Failed to start automation: Network error',
          level: 'error',
        });
      }
    },
    [addLog],
  );

  const handleStopAutomation = useCallback(async () => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.endpoints.stop), {
        method: 'POST',
      });

      if (response.ok) {
        setAutomationRunning(false);
        addLog({
          timestamp: formatTime(new Date()),
          message: '⏹️ Automation stopped by user',
          level: 'warning',
        });
      }
    } catch (error) {
      console.error('Failed to stop automation:', error);
      addLog({
        timestamp: formatTime(new Date()),
        message: '❌ Failed to stop automation',
        level: 'error',
      });
    }
  }, [addLog]);

  const handleClearLogs = useCallback(() => {
    clearLogs();
  }, [clearLogs]);

  // Update automation running state based on progress
  if (progress?.step === 5 && progress?.status === 'completed' && automationRunning) {
    setAutomationRunning(false);
  }

  return (
    <div className='min-h-screen bg-gray-50'>
      <div className='container mx-auto px-4 py-6 max-w-7xl'>
        <Header />

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
          {/* Left Column - Control Panel & Progress */}
          <div className='lg:col-span-1 space-y-6'>
            <ControlPanel
              onStartAutomation={handleStartAutomation}
              onStopAutomation={handleStopAutomation}
              onClearLogs={handleClearLogs}
              automationRunning={automationRunning}
            />

            <ProgressTracker progress={progress} />

            <DownloadSection files={files} visible={files.length > 0} />
          </div>

          {/* Right Column - Logs */}
          <div className='lg:col-span-2'>
            <LogsPanel logs={logs} logCount={logs.length} />
          </div>
        </div>
      </div>

      <ConnectionStatus isConnected={isConnected} />
    </div>
  );
}
