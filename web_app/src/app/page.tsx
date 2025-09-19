'use client';

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
  // const [questionnaireProgress, setQuestionnaireProgress] = useState({ current: 0, total: 0 });

  // Development state for testing loader
  const [testLoaderRunning, setTestLoaderRunning] = useState(false);
  const isDev = process.env.NODE_ENV === 'development';
  // const [showDebugAnswers, setShowDebugAnswers] = useState(false); // Removed - replaced with DocumentChangesPreview
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
        const savedAnswers = localStorage.getItem(QUESTIONNAIRE_STORAGE_KEY);
        console.log('🔍 DEBUG: Raw localStorage data:', savedAnswers);

        const questionnaireAnswers = savedAnswers ? JSON.parse(savedAnswers) : {};
        console.log('🔍 DEBUG: Parsed questionnaire answers:', questionnaireAnswers);
        console.log('🔍 DEBUG: Answer count:', Object.keys(questionnaireAnswers).length);
        console.log('🔍 DEBUG: Answer keys:', Object.keys(questionnaireAnswers));

        // Keep base64 logo data for internal automation (filtering only needed for external APIs)
        // The logo data will be processed internally by the automation scripts
        console.log('🔍 DEBUG: Keeping base64 logo data for automation processing');

        console.log('🔍 DEBUG: Answers for automation:', Object.keys(questionnaireAnswers).length);
        console.log(
          '🚀 Starting automation with answers:',
          Object.keys(questionnaireAnswers).length,
          'fields',
        );

        // Get the stored userId for this session
        const userId = localStorage.getItem('questionnaire_user_id');
        console.log('🔍 Using stored user ID for automation:', userId);

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
          setAutomationRunning(true);
          setTestLoaderRunning(false); // Stop test loader when real automation starts
          addLog({
            timestamp: formatTime(new Date()),
            message: `🚀 Automation started successfully with ${
              Object.keys(questionnaireAnswers).length
            } questionnaire answers`,
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

  // Update automation running state based on progress
  if (progress?.step === 5 && progress?.status === 'completed' && automationRunning) {
    setAutomationRunning(false);
  }

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

        <div className='flex flex-1 overflow-hidden items-center justify-center'>
          <div className='w-full max-w-3xl bg-gray-50 overflow-y-auto overflow-x-hidden p-6 flex flex-col min-w-0'>
            <div className='flex-1'>
              <PolicyHeader />
              <Questionnaire
                onComplete={handleQuestionnaireComplete}
                onStartAutomation={() => handleStartAutomation(false)}
                automationRunning={automationRunning}
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
        <div className='w-full max-w-3xl px-6 py-12 overflow-hidden min-w-0'>
          <PolicyHeader />

          {/* Always Show Questionnaire Editor - First Section */}
          {questionnaireCompleted && (
            <ExpandableQuestionnaire
              isExpanded={true}
              onToggle={() => {}}
              onComplete={handleQuestionnaireComplete}
              onStartAutomation={() => handleStartAutomation(false)}
              automationRunning={automationRunning}
            />
          )}

          {/* Centered Control Panel */}
          {/* <div className='mb-8'>
              <div id='automation-panel' className='automation-panel'>
                <ControlPanel
                  onStopAutomation={handleStopAutomation}
                  onClearLogs={handleClearLogs}
                  automationRunning={automationRunning}
                />

                {isDev && !automationRunning && (
                  <div className='mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg'>
                    <div className='text-center'>
                      <button
                        onClick={() => setTestLoaderRunning(!testLoaderRunning)}
                        className='bg-purple-500 hover:bg-purple-600 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors duration-200 border border-purple-400 shadow-sm'
                      >
                        🧪 {testLoaderRunning ? 'Stop' : 'Test'} Loader UI
                      </button>
                    </div>
                    <p className='text-xs text-purple-600 text-center mt-2 font-medium'>
                      Development Mode: Test the automation loader UI without running actual
                      automation
                    </p>
                  </div>
                )}
              </div>
            </div> */}

          <div className='flex flex-col gap-6'>
            <div className='w-full'>
              <DownloadSection files={files} visible={files.length > 0} />
            </div>

            {/* <div className='w-full'>
                <LogsPanel logs={logs} logCount={logs.length} />
              </div>

              {(automationRunning || testLoaderRunning) && (
                <div className='w-full'>
                  <PolicyAutomationLoader loading={automationRunning || testLoaderRunning} />
                </div>
              )} */}
          </div>

          {/* Footer - Added at the bottom of the main content */}
          <Footer />
        </div>
      </div>

      <ConnectionStatus isConnected={isConnected} />
    </div>
  );
}
