'use client';

import { ConnectionStatus } from '@/components/ConnectionStatus';
import { ControlPanel } from '@/components/ControlPanel';
import { DownloadSection } from '@/components/DownloadSection';
import { Header } from '@/components/Header';
import { LogsPanel } from '@/components/LogsPanel';
import { ProgressTracker } from '@/components/ProgressTracker';
import { Questionnaire } from '@/components/Questionnaire';
import { UserAnswersDisplay } from '@/components/UserAnswersDisplay';
import { API_CONFIG, getApiUrl } from '@/config/api';
import { useSocket } from '@/hooks/useSocket';
import { QUESTIONNAIRE_STORAGE_KEY } from '@/lib/questionnaire-utils';
import { formatTime } from '@/lib/utils';
import { QuestionnaireAnswer } from '@/types';
import { useCallback, useEffect, useState } from 'react';

export default function Dashboard() {
  const [automationRunning, setAutomationRunning] = useState(false);
  const [questionnaireCompleted, setQuestionnaireCompleted] = useState(false);
  const [checkingQuestionnaire, setCheckingQuestionnaire] = useState(true);
  const [editingQuestionnaire, setEditingQuestionnaire] = useState(false);
  const [questionnaireProgress, setQuestionnaireProgress] = useState({ current: 0, total: 0 });
  const [showDebugAnswers, setShowDebugAnswers] = useState(false);
  const { isConnected, logs, progress, files, clearLogs, addLog } = useSocket();

  // Check if questionnaire is already completed (from localStorage)
  useEffect(() => {
    const checkQuestionnaireStatus = () => {
      try {
        const savedAnswers = localStorage.getItem(QUESTIONNAIRE_STORAGE_KEY);
        if (savedAnswers) {
          const answers = JSON.parse(savedAnswers);
          // Consider questionnaire completed if we have at least some answers
          setQuestionnaireCompleted(Object.keys(answers).length > 0);
        }
      } catch (error) {
        console.error('Failed to check questionnaire status:', error);
      } finally {
        setCheckingQuestionnaire(false);
      }
    };

    checkQuestionnaireStatus();
  }, []);

  const handleStartAutomation = useCallback(
    async (skipApi: boolean) => {
      try {
        // Get questionnaire answers from localStorage
        const savedAnswers = localStorage.getItem('questionnaireAnswers');
        const questionnaireAnswers = savedAnswers ? JSON.parse(savedAnswers) : {};
        
        console.log('🚀 Starting automation with answers:', Object.keys(questionnaireAnswers).length, 'fields');
        
        const response = await fetch(getApiUrl(API_CONFIG.endpoints.start), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ 
            skip_api: skipApi,
            questionnaire_answers: questionnaireAnswers,
            timestamp: Date.now()
          }),
        });

        if (response.ok) {
          setAutomationRunning(true);
          addLog({
            timestamp: formatTime(new Date()),
            message: `🚀 Automation started successfully with ${Object.keys(questionnaireAnswers).length} questionnaire answers`,
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

  const handleQuestionnaireComplete = useCallback(
    async (answers: Record<string, QuestionnaireAnswer>) => {
      try {
        const response = await fetch('/api/answers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ answers }),
        });

        if (response.ok) {
          setQuestionnaireCompleted(true);
          setEditingQuestionnaire(false); // Exit editing mode

          // Parse response to get debugging info
          const responseData = await response.json();

          const message = editingQuestionnaire
            ? '✅ Questionnaire updated successfully'
            : `✅ Questionnaire completed successfully! Saved ${
                responseData.answerCount || 'unknown'
              } answers. Ready to start automation.`;
          addLog({
            timestamp: formatTime(new Date()),
            message,
            level: 'success',
          });

          // Add debug information
          if (responseData.filePath) {
            addLog({
              timestamp: formatTime(new Date()),
              message: `📁 Answers saved to: ${responseData.filePath}`,
              level: 'info',
            });
          }

          if (responseData.dataDir) {
            addLog({
              timestamp: formatTime(new Date()),
              message: `📂 Using data directory: ${responseData.dataDir}`,
              level: 'info',
            });
          }

          // Auto-scroll to automation panel after a short delay for better UX
          if (!editingQuestionnaire) {
            // Return a promise that resolves after navigation is complete
            return new Promise<void>((resolve) => {
              setTimeout(() => {
                const automationPanel = document.getElementById('automation-panel');
                if (automationPanel) {
                  automationPanel.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                  });
                  // Add a subtle highlight effect
                  automationPanel.classList.add('highlight-automation');
                  setTimeout(() => {
                    automationPanel.classList.remove('highlight-automation');
                    resolve();
                  }, 3000);
                } else {
                  resolve();
                }
              }, 1000);
            });
          } else {
            // For editing mode, resolve immediately
            return Promise.resolve();
          }
        } else {
          const error = await response.json();
          addLog({
            timestamp: formatTime(new Date()),
            message: `❌ Failed to save questionnaire: ${error.error}`,
            level: 'error',
          });
          throw new Error(error.error || 'Failed to save questionnaire');
        }
      } catch (error) {
        console.error('Failed to save questionnaire:', error);
        addLog({
          timestamp: formatTime(new Date()),
          message: '❌ Failed to save questionnaire: Network error',
          level: 'error',
        });
        throw error;
      }
    },
    [addLog, editingQuestionnaire],
  );

  const handleEditQuestionnaire = useCallback(() => {
    setEditingQuestionnaire(true);
    addLog({
      timestamp: formatTime(new Date()),
      message: '📝 Editing questionnaire responses...',
      level: 'info',
    });
  }, [addLog]);

  // Update automation running state based on progress
  if (progress?.step === 5 && progress?.status === 'completed' && automationRunning) {
    setAutomationRunning(false);
  }

  // Show loading state while checking questionnaire status
  if (checkingQuestionnaire) {
    return (
      <div className='min-h-screen bg-gray-50 flex items-center justify-center'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>Loading...</p>
        </div>
      </div>
    );
  }

  // Show questionnaire if not completed OR if user wants to edit
  if (!questionnaireCompleted || editingQuestionnaire) {
    return (
      <div className='min-h-screen bg-gray-50'>
        <div className='container mx-auto px-4 py-6 max-w-7xl'>
          <Header />

          <div className='mt-8'>
            <div className='text-center mb-8'>
              <h1 className='text-3xl font-bold text-gray-900 mb-4'>
                {editingQuestionnaire
                  ? 'Edit Questionnaire Responses'
                  : 'Policy Configuration Questionnaire'}
              </h1>
              <p className='text-lg text-gray-600 max-w-2xl mx-auto'>
                {editingQuestionnaire
                  ? 'Update your responses below. Your previous answers have been pre-filled for easy editing.'
                  : 'Please answer the following questions to configure your access control policy. This information will be used to generate a customized policy document for your organization.'}
              </p>
              {editingQuestionnaire && (
                <div className='mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg max-w-2xl mx-auto'>
                  <p className='text-blue-800 text-sm'>
                    💡 You are editing your questionnaire responses. Your previous answers are
                    loaded and can be modified.
                  </p>
                </div>
              )}
              {questionnaireProgress.total > 0 && (
                <div className='mt-4 text-sm text-gray-500'>
                  Progress: {questionnaireProgress.current} of {questionnaireProgress.total}{' '}
                  questions
                </div>
              )}
            </div>

            <Questionnaire
              onComplete={handleQuestionnaireComplete}
              onProgressUpdate={setQuestionnaireProgress}
            />
          </div>
        </div>

        <ConnectionStatus isConnected={isConnected} />
      </div>
    );
  }

  // Show main dashboard after questionnaire is completed
  return (
    <div className='min-h-screen bg-gray-50'>
      <div className='container mx-auto px-4 py-6 max-w-7xl'>
        <Header />

        {/* Questionnaire completion banner */}
        <div className='mb-6 bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6 shadow-sm'>
          <div className='flex items-center justify-between'>
            <div className='flex items-center'>
              <div className='text-green-600 mr-4 text-2xl'>✅</div>
              <div>
                <h3 className='text-green-900 font-semibold text-lg'>
                  Questionnaire Completed Successfully!
                </h3>
                <p className='text-green-700 text-sm mt-1'>
                  Your responses have been saved. <strong>Next step:</strong> Click &quot;Start
                  Automation&quot; below to generate your custom policy document.
                </p>
                <div className='flex items-center mt-2 text-blue-700 text-sm'>
                  <span className='mr-2'>👇</span>
                  <span className='font-medium'>
                    Use the automation panel below to start processing
                  </span>
                </div>
              </div>
            </div>
            <div className='flex gap-2'>
              <button
                onClick={handleEditQuestionnaire}
                className='px-4 py-2 bg-white border border-green-300 text-green-700 rounded-lg hover:bg-green-50 transition-colors text-sm font-medium'
              >
                📝 Edit Questionnaire
              </button>
              <button
                onClick={() => setShowDebugAnswers(!showDebugAnswers)}
                className='px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-lg hover:bg-blue-50 transition-colors text-sm font-medium'
              >
                🔍 {showDebugAnswers ? 'Hide' : 'Show'} Answers
              </button>
            </div>
          </div>
        </div>

        {/* Debug Answers Display */}
        <UserAnswersDisplay visible={showDebugAnswers} />

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
          {/* Left Column - Control Panel & Progress */}
          <div className='lg:col-span-1 space-y-6'>
            <div id='automation-panel' className='automation-panel'>
              <ControlPanel
                onStartAutomation={handleStartAutomation}
                onStopAutomation={handleStopAutomation}
                onClearLogs={handleClearLogs}
                automationRunning={automationRunning}
              />
            </div>

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
