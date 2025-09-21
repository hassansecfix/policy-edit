'use client';

import { LogsPanel } from '@/components';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { DownloadSection } from '@/components/DownloadSection';
import { ExpandableQuestionnaire } from '@/components/ExpandableQuestionnaire';
import { Footer } from '@/components/Footer';
import { Header } from '@/components/Header';
import { PolicyHeader } from '@/components/PolicyHeader';
import { Questionnaire } from '@/components/Questionnaire';
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

  // Development state for testing loader
  const [testLoaderRunning, setTestLoaderRunning] = useState(false);
  const isDev = process.env.NODE_ENV === 'development';
  const { isConnected, logs, progress, files, clearLogs, clearFiles, addLog } = useSocket();

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
      setTestLoaderRunning(false);

      try {
        // Get questionnaire answers from localStorage
        const savedAnswers = localStorage.getItem(QUESTIONNAIRE_STORAGE_KEY);
        const questionnaireAnswers = savedAnswers ? JSON.parse(savedAnswers) : {};

        // Get the stored userId for this session
        const userId = localStorage.getItem('questionnaire_user_id');

        const response = await fetch(getApiUrl(API_CONFIG.endpoints.start), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            skip_api: skipApi,
            questionnaire_answers: questionnaireAnswers,
            user_id: userId, // Include userId for multi-user isolation
            timestamp: Date.now(),
          }),
        });

        if (response.ok) {
          addLog({
            timestamp: formatTime(new Date()),
            message: `🚀 Automation started successfully with ${
              Object.keys(questionnaireAnswers).length
            } questionnaire answers`,
            level: 'success',
          });
        } else {
          const error = await response.json();

          // If backend says automation is already running, keep the frontend state as running
          if (error.error && error.error.includes('already running')) {
            addLog({
              timestamp: formatTime(new Date()),
              message: '🔄 Syncing with existing automation process...',
              level: 'info',
            });
          } else {
            // Reset automation state on other errors
            setAutomationRunning(false);
            addLog({
              timestamp: formatTime(new Date()),
              message: `❌ Failed to start automation: ${error.error}`,
              level: 'error',
            });
          }
        }
      } catch (error) {
        console.error('Failed to start automation:', error);
        setAutomationRunning(false);
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

          // Store the userId for later use in automation
          if (responseData.userId) {
            localStorage.setItem('questionnaire_user_id', responseData.userId);
            console.log('💾 Stored user ID for automation:', responseData.userId);
          }

          const message = editingQuestionnaire
            ? '✅ Questionnaire updated successfully'
            : `✅ Questionnaire completed successfully! Saved ${
                responseData.answerCount || 'unknown'
              } answers${
                responseData.logoProcessed ? ' (logo processed)' : ''
              }. Ready to start automation.`;
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

  // Update automation running state ONLY when files are actually available
  useEffect(() => {
    if (automationRunning) {
      // Stop automation ONLY when files become available (matching DownloadSection logic)
      if (files.length > 0) {
        setAutomationRunning(false);
        addLog({
          timestamp: formatTime(new Date()),
          message: `✅ Policy document generated successfully! ${files.length} file(s) ready for download.`,
          level: 'success',
        });
      }
    }
  }, [files.length, automationRunning, addLog]);

  // Auto-stop test loader when real automation completes
  // useEffect(() => {
  //   if (!automationRunning && testLoaderRunning) {
  //     // Auto-stop test loader after a delay when real automation finishes
  //     const timer = setTimeout(() => {
  //       setTestLoaderRunning(false);
  //     }, 9000);
  //     return () => clearTimeout(timer);
  //   }
  // }, [automationRunning, testLoaderRunning]);

  // Show loading state while checking questionnaire status
  if (checkingQuestionnaire) {
    return (
      <div className='h-screen bg-gray-50 flex items-center justify-center'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>Loading...</p>
        </div>
      </div>
    );
  }

  // Show questionnaire if not completed (but not if just editing)
  if (!questionnaireCompleted && !editingQuestionnaire) {
    return (
      <div className='h-screen bg-gray-50 flex flex-col'>
        {/* Header - Fixed */}
        <div className='bg-gray-50 border-b border-gray-200 px-4 py-3 flex-shrink-0'>
          <div className='container mx-auto max-w-7xl'>
            <Header />
          </div>
        </div>

        <div className='flex flex-1 items-center justify-center'>
          <div className='w-full max-w-3xl bg-gray-50 overflow-y-auto overflow-x-hidden p-6 flex flex-col min-w-0'>
            <div className='flex-1'>
              <PolicyHeader />
              <Questionnaire
                onComplete={handleQuestionnaireComplete}
                onStartAutomation={() => handleStartAutomation(false)}
                onSetAutomationRunning={setAutomationRunning}
                onClearFiles={clearFiles}
                automationRunning={automationRunning}
                progress={progress}
                filesReady={files.length > 0}
              />
            </div>

            {/* Footer - Added at the bottom of questionnaire view */}
            <Footer />
          </div>
        </div>

        <ConnectionStatus isConnected={isConnected} />
      </div>
    );
  }

  return (
    <div className='h-screen flex flex-col bg-gray-50 overflow-hidden'>
      {/* Header - Fixed */}
      <div className='bg-gray-50 border-b border-gray-200 px-6 py-3 flex-shrink-0 sticky top-0 z-10'>
        <div className='container max-w-7xl'>
          <Header />
        </div>
      </div>

      {/* Main Layout: Sidebar + Content */}
      <div className='flex flex-1 bg-gray-50 overflow-auto justify-center'>
        {/* Main Content - 75% Scrollable */}
        <div className='w-full max-w-3xl px-6 py-12 min-w-0'>
          <PolicyHeader />

          {/* Always Show Questionnaire Editor - First Section */}
          {questionnaireCompleted && (
            <ExpandableQuestionnaire
              isExpanded={true}
              onToggle={() => {}}
              onComplete={handleQuestionnaireComplete}
              onStartAutomation={() => handleStartAutomation(false)}
              onSetAutomationRunning={setAutomationRunning}
              onClearFiles={clearFiles}
              automationRunning={automationRunning}
              progress={progress}
              filesReady={files.length > 0}
            />
          )}

          {/* Automation Control Button - Dev Only */}
          {isDev && (
            <div className='mb-8 flex justify-center'>
              <div className='bg-white rounded-lg shadow-md border border-gray-200 p-6 w-full max-w-md'>
                <div className='text-center'>
                  <h3 className='text-lg font-semibold text-gray-900 mb-3'>Policy Automation</h3>
                  <p className='text-sm text-gray-600 mb-6'>
                    Generate your customized policy document based on your questionnaire responses.
                  </p>

                  {!automationRunning ? (
                    <div className='space-y-2'>
                      <button
                        onClick={() => handleStartAutomation(false)}
                        className='w-full bg-violet-600 hover:bg-violet-700 text-white font-medium px-6 py-3 rounded-lg transition-colors duration-200 cursor-pointer shadow-sm hover:shadow-md flex items-center justify-center gap-2'
                      >
                        <svg
                          className='w-5 h-5'
                          fill='none'
                          stroke='currentColor'
                          viewBox='0 0 24 24'
                        >
                          <path
                            strokeLinecap='round'
                            strokeLinejoin='round'
                            strokeWidth='2'
                            d='M12 3v18m9-9l-9-9-9 9'
                          />
                        </svg>
                        Start Automation
                      </button>
                    </div>
                  ) : (
                    <div className='space-y-2'>
                      <div className='w-full bg-amber-100 text-amber-800 font-medium px-6 py-3 rounded-lg border border-amber-200 flex items-center justify-center gap-2'>
                        <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600'></div>
                        Automation Running...
                      </div>
                      <button
                        onClick={handleStopAutomation}
                        className='w-full bg-red-100 hover:bg-red-200 text-red-700 font-medium px-4 py-2 rounded-lg transition-colors duration-200 cursor-pointer text-sm border border-red-200'
                      >
                        Force Stop Automation
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className='flex flex-col gap-6'>
            <div className='w-full'>
              <DownloadSection files={files} visible={files.length > 0} />
            </div>

            {isDev && <LogsPanel logs={logs} logCount={logs.length} />}
          </div>

          {/* Footer - Added at the bottom of the main content */}
          <Footer />
        </div>
      </div>

      <ConnectionStatus isConnected={isConnected} />
    </div>
  );
}
