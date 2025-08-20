'use client';

import { QuestionnaireAnswer } from '@/types';
import { useEffect, useState } from 'react';

interface ServerAnswersResponse {
  exists?: boolean;
  content?: string;
  message?: string;
  filePath?: string;
  lineCount?: number;
  searchedPaths?: string[];
  error?: any;
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
        setAnswers(JSON.parse(savedAnswers));
      }

      // Check server-side answers
      const response = await fetch('/api/answers');
      if (response.ok) {
        const data = await response.json();
        setServerAnswers(data);
      } else {
        const errorData = await response.json();
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

  if (!visible) {
    return null;
  }

  return (
    <div className='bg-white border border-gray-200 rounded-lg p-6 mb-6'>
      <div className='flex items-center justify-between mb-4'>
        <h3 className='text-lg font-semibold text-gray-900'>
          🔍 Debug: Your Questionnaire Answers
        </h3>
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
                    </p>
                    <p className='text-xs text-gray-600'>📁 Path: {serverAnswers.filePath}</p>
                    <div className='text-xs bg-white p-2 rounded border'>
                      <strong>Preview:</strong>
                      <pre className='mt-1 whitespace-pre-wrap'>
                        {serverAnswers.content?.split('\n').slice(0, 5).join('\n')}
                        {serverAnswers.content &&
                          serverAnswers.content.split('\n').length > 5 &&
                          '\n...'}
                      </pre>
                    </div>
                  </>
                ) : (
                  <>
                    <p className='text-sm text-red-600'>❌ No file found on server</p>
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
        <p className='text-sm text-yellow-800'>
          <strong>💡 Debug Info:</strong> This panel helps diagnose questionnaire saving issues. If
          your answers appear in &quot;Local Storage&quot; but not &quot;Server&quot;, there&apos;s
          a file path or permission issue in production.
        </p>
      </div>
    </div>
  );
}
