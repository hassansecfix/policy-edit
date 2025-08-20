'use client';

import { QuestionnaireAnswer } from '@/types';
import { useEffect, useState } from 'react';

interface ServerAnswersResponse {
  exists?: boolean;
  content?: string;
  message?: string;
  filePath?: string;
  lineCount?: number;
  isUserSpecific?: boolean;
  dataDir?: string;
  originalDataDir?: string;
  isRender?: boolean;
  isServerless?: boolean;
  directoryFallbackUsed?: boolean;
  availableUserFiles?: string[];
  searchedPaths?: string[];
  searchedDirectories?: string[];
  cwd?: string;
  error?: string | object;
}

interface UserAnswersDisplayProps {
  visible?: boolean;
}

export function UserAnswersDisplay({ visible = false }: UserAnswersDisplayProps) {
  const [answers, setAnswers] = useState<Record<string, QuestionnaireAnswer> | null>(null);
  const [serverAnswers, setServerAnswers] = useState<ServerAnswersResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnswers = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load from localStorage
      const savedAnswers = localStorage.getItem('questionnaire_answers');
      if (savedAnswers) {
        const parsedAnswers = JSON.parse(savedAnswers);
        setAnswers(parsedAnswers);
        console.log(
          '📱 Local storage answers loaded:',
          Object.keys(parsedAnswers).length,
          'answers',
        );
      } else {
        console.log('📱 No answers found in local storage');
      }

      // Check server-side answers
      console.log('🗄️ Fetching server answers...');
      const response = await fetch('/api/answers', {
        cache: 'no-store', // Always get fresh data
        headers: {
          'Cache-Control': 'no-cache',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('🗄️ Server response:', data);
        setServerAnswers(data);
      } else {
        const errorData = await response.json();
        console.error('🗄️ Server error response:', errorData);
        setServerAnswers({ error: errorData });
      }
    } catch (err) {
      setError('Failed to load answers');
      console.error('Error loading answers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      loadAnswers();
    }
  }, [visible]);

  // Parse CSV content to extract answers
  const parseServerAnswers = (csvContent: string) => {
    try {
      const lines = csvContent.trim().split('\n');
      if (lines.length <= 1) return {};

      const parsedAnswers: Record<
        string,
        {
          field: string;
          questionNumber: number;
          questionText: string;
          responseType: string;
          value: string;
        }
      > = {};

      // Skip header line
      for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        if (!line.trim()) continue;

        const parts = line.split(';');
        if (parts.length >= 5) {
          const [questionNumber, questionText, field, responseType, userResponse] = parts;

          // Skip special entries like logo base64 data
          if (field === '_logo_base64_data') continue;

          parsedAnswers[field] = {
            field,
            questionNumber: parseInt(questionNumber),
            questionText,
            responseType,
            value: userResponse,
          };
        }
      }

      return parsedAnswers;
    } catch (error) {
      console.error('Error parsing CSV:', error);
      return {};
    }
  };

  if (!visible) {
    return null;
  }

  return (
    <div className='bg-white border border-gray-200 rounded-lg p-6 mb-6'>
      <div className='flex items-center justify-between mb-4'>
        <h3 className='text-lg font-semibold text-gray-900'>
          🔍 Debug: Your Questionnaire Answers
        </h3>
        <div className='flex gap-2'>
          <button
            onClick={loadAnswers}
            disabled={loading}
            className={`px-3 py-1 text-sm rounded ${
              loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button
            onClick={async () => {
              if (!answers) {
                alert('No local answers to test save with');
                return;
              }

              try {
                console.log('🧪 Testing save with current local answers...');
                const response = await fetch('/api/answers', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ answers }),
                });

                const result = await response.json();
                console.log('🧪 Test save result:', result);

                if (response.ok) {
                  alert(
                    `Test save successful! Saved ${result.answerCount} answers to ${result.filePath}`,
                  );
                  loadAnswers(); // Refresh to see the updated server data
                } else {
                  alert(`Test save failed: ${result.error}`);
                }
              } catch (error) {
                console.error('🧪 Test save error:', error);
                alert(`Test save error: ${error}`);
              }
            }}
            disabled={!answers || loading}
            className={`px-3 py-1 text-sm rounded ${
              !answers || loading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            🧪 Test Save
          </button>
        </div>
      </div>

      {error && (
        <div className='bg-red-50 border border-red-200 rounded-lg p-3 mb-4'>
          <p className='text-red-700 text-sm'>❌ Error: {error}</p>
        </div>
      )}

      <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
        {/* Local Storage Answers */}
        <div>
          <h4 className='font-medium text-gray-800 mb-3'>📱 Local Storage (Your Browser)</h4>
          <div className='bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto'>
            {answers ? (
              <div className='space-y-2'>
                <p className='text-sm text-green-600'>
                  ✅ Found {Object.keys(answers).length} answers
                </p>
                {Object.entries(answers).map(([field, answer]) => (
                  <div key={field} className='text-xs'>
                    <span className='font-mono text-blue-600'>{field}:</span>{' '}
                    <span className='text-gray-700'>
                      {typeof answer.value === 'object'
                        ? JSON.stringify(answer.value).substring(0, 50) + '...'
                        : String(answer.value).substring(0, 100)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className='text-sm text-gray-500'>No answers found in local storage</p>
            )}
          </div>
        </div>

        {/* Server-side Answers */}
        <div>
          <h4 className='font-medium text-gray-800 mb-3'>🗄️ Server (Production File)</h4>
          <div className='bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto'>
            {loading ? (
              <div className='flex items-center'>
                <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2'></div>
                <span className='text-sm text-gray-600'>Checking server...</span>
              </div>
            ) : serverAnswers ? (
              <div className='space-y-2'>
                {serverAnswers.exists ? (
                  <>
                    <p className='text-sm text-green-600'>
                      ✅ File exists: {serverAnswers.lineCount} lines
                      {serverAnswers.isUserSpecific && ' (User-specific timestamped file)'}
                    </p>
                    <p className='text-xs text-gray-600'>📁 Path: {serverAnswers.filePath}</p>
                    {serverAnswers.isServerless && (
                      <p className='text-xs text-yellow-600 font-medium'>
                        🌐 Serverless environment detected
                      </p>
                    )}
                    {serverAnswers.dataDir && (
                      <p className='text-xs text-gray-600'>
                        📂 Data directory: {serverAnswers.dataDir}
                      </p>
                    )}
                    {serverAnswers.originalDataDir &&
                      serverAnswers.originalDataDir !== serverAnswers.dataDir && (
                        <p className='text-xs text-gray-600'>
                          📂 Original data directory: {serverAnswers.originalDataDir}
                        </p>
                      )}
                    {serverAnswers.cwd && (
                      <p className='text-xs text-gray-500'>
                        🏠 Working directory: {serverAnswers.cwd}
                      </p>
                    )}
                    {serverAnswers.directoryFallbackUsed && (
                      <p className='text-xs text-orange-600 font-medium'>
                        ⚠️ Directory fallback used - original location was not writable
                      </p>
                    )}
                    {serverAnswers.availableUserFiles &&
                      serverAnswers.availableUserFiles.length > 0 && (
                        <details className='text-xs mt-1'>
                          <summary className='cursor-pointer text-blue-600 hover:text-blue-800'>
                            📋 Available user files ({serverAnswers.availableUserFiles.length})
                          </summary>
                          <ul className='mt-1 ml-4 space-y-1'>
                            {serverAnswers.availableUserFiles.map((file, index) => (
                              <li key={index} className='text-gray-600'>
                                • {file}
                              </li>
                            ))}
                          </ul>
                        </details>
                      )}

                    {/* Parsed Server Answers */}
                    {serverAnswers.content &&
                      (() => {
                        const parsedServerAnswers = parseServerAnswers(serverAnswers.content);
                        const serverAnswerCount = Object.keys(parsedServerAnswers).length;

                        return (
                          <div className='space-y-2'>
                            <p className='text-sm text-blue-600'>
                              📊 Parsed {serverAnswerCount} answers from server
                            </p>
                            {serverAnswerCount > 0 ? (
                              <div className='space-y-1 max-h-32 overflow-y-auto'>
                                {Object.entries(parsedServerAnswers).map(([field, answer]) => (
                                  <div key={field} className='text-xs bg-white p-2 rounded border'>
                                    <div className='font-semibold text-gray-700 mb-1'>
                                      Q{answer.questionNumber}: {answer.questionText}
                                    </div>
                                    <div className='text-blue-600'>
                                      <span className='font-mono'>{field}:</span> {answer.value}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <p className='text-sm text-orange-600'>
                                ⚠️ No answers found in server file
                              </p>
                            )}

                            {/* Raw CSV Preview */}
                            <details className='text-xs'>
                              <summary className='cursor-pointer text-gray-600 hover:text-gray-800'>
                                📄 Raw CSV Content (click to expand)
                              </summary>
                              <div className='mt-2 bg-white p-2 rounded border'>
                                <pre className='whitespace-pre-wrap text-xs'>
                                  {serverAnswers.content.split('\n').slice(0, 10).join('\n')}
                                  {serverAnswers.content.split('\n').length > 10 &&
                                    '\n... (truncated)'}
                                </pre>
                              </div>
                            </details>
                          </div>
                        );
                      })()}
                  </>
                ) : (
                  <>
                    <p className='text-sm text-red-600'>❌ No file found on server</p>
                    {serverAnswers.isServerless && (
                      <p className='text-xs text-yellow-600 font-medium'>
                        🌐 Serverless environment detected
                      </p>
                    )}
                    {serverAnswers.cwd && (
                      <p className='text-xs text-gray-500'>
                        🏠 Working directory: {serverAnswers.cwd}
                      </p>
                    )}
                    {serverAnswers.searchedDirectories && (
                      <div className='text-xs text-gray-600'>
                        <strong>Searched directories:</strong>
                        {serverAnswers.searchedDirectories.map((path: string, index: number) => (
                          <div key={index} className='font-mono ml-2'>
                            • {path}
                          </div>
                        ))}
                      </div>
                    )}
                    {serverAnswers.searchedPaths && (
                      <div className='text-xs text-gray-600'>
                        <strong>Searched paths:</strong>
                        {serverAnswers.searchedPaths.map((path: string, index: number) => (
                          <div key={index} className='font-mono ml-2'>
                            • {path}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}

                {serverAnswers.error && (
                  <div className='text-xs text-red-600 bg-red-50 p-2 rounded border'>
                    <strong>Server Error:</strong> {JSON.stringify(serverAnswers.error, null, 2)}
                  </div>
                )}
              </div>
            ) : (
              <p className='text-sm text-gray-500'>No server data loaded</p>
            )}
          </div>
        </div>
      </div>

      <div className='mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg'>
        <p className='text-sm text-yellow-800 mb-2'>
          <strong>💡 Debug Instructions:</strong>
        </p>
        <ul className='text-sm text-yellow-800 space-y-1 ml-4'>
          <li>
            •{' '}
            <strong>
              If Local Storage shows answers but Server shows &quot;No file found&quot;
            </strong>
            : File path issue in production
          </li>
          <li>
            • <strong>If Server shows file but 0 parsed answers</strong>: CSV format issue
          </li>
          <li>
            • <strong>Use &quot;Test Save&quot; button</strong>: Manually test if saving works right
            now
          </li>
          <li>
            • <strong>Check browser console</strong>: Look for detailed error logs and paths
          </li>
          <li>
            • <strong>Both panels empty</strong>: Questions not submitted yet
          </li>
        </ul>

        {serverAnswers && serverAnswers.exists && (
          <div className='mt-3 p-2 bg-green-50 border border-green-200 rounded'>
            <p className='text-sm font-medium text-green-800'>
              ✨ <strong>Direct API Active:</strong> Your answers are processed directly via API -
              no complex file storage needed! This is faster, more reliable, and works perfectly in
              production environments. Multiple users can work simultaneously without conflicts.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
