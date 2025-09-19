'use client';

import { PolicyGenerationOverlay } from '@/components/PolicyGenerationOverlay';
import { QuestionInput } from '@/components/QuestionInput';
import { SparkleIcon } from '@/components/ui/SparkleIcon';
import { generateDynamicDescription } from '@/lib/dynamic-descriptions';
import { QUESTIONNAIRE_STORAGE_KEY } from '@/lib/questionnaire-utils';
import { Question, QuestionnaireAnswer, QuestionnaireState } from '@/types';
import { useCallback, useEffect, useRef, useState } from 'react';

interface FileUploadValue {
  name: string;
  size: number;
  type: string;
  data: string;
}

interface DocumentChange {
  type: 'replace' | 'remove' | 'add' | 'logo' | 'info';
  description: string;
  oldText: string;
  newText: string;
  field: string;
}

interface QuestionnaireProps {
  onComplete: (answers: Record<string, QuestionnaireAnswer>) => Promise<void>;
  onProgressUpdate?: (progress: { current: number; total: number }) => void;
  onStartAutomation?: () => Promise<void>;
  automationRunning?: boolean;
}

export function Questionnaire({
  onComplete,
  onProgressUpdate,
  onStartAutomation,
  automationRunning = false,
}: QuestionnaireProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [state, setState] = useState<QuestionnaireState>({
    currentQuestionIndex: 0,
    answers: {},
    isCompleted: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, forceUpdate] = useState({});
  const [testOverlay, setTestOverlay] = useState(false);
  const [isPreviewExpanded, setIsPreviewExpanded] = useState(false);
  const [documentChanges, setDocumentChanges] = useState<DocumentChange[]>([]);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastAnswersRef = useRef<string>('');

  // Load questions from API
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        const response = await fetch('/api/questions');
        if (!response.ok) {
          throw new Error('Failed to load questions');
        }
        const questionsData = await response.json();
        setQuestions(questionsData);
        setLoading(false);
      } catch {
        setError('Failed to load questions. Please try again.');
        setLoading(false);
      }
    };

    loadQuestions();
  }, []);

  // Load existing answers from localStorage
  useEffect(() => {
    const loadExistingAnswers = () => {
      if (questions.length === 0) return; // Wait for questions to load first

      try {
        const savedAnswers = localStorage.getItem(QUESTIONNAIRE_STORAGE_KEY);
        if (savedAnswers) {
          const existingAnswers: Record<string, QuestionnaireAnswer> = JSON.parse(savedAnswers);

          // Update state with existing answers
          setState((prev) => ({
            ...prev,
            answers: existingAnswers,
          }));
        }
      } catch (error) {
        console.log('Failed to load existing answers from localStorage:', error);
      }
    };

    loadExistingAnswers();
  }, [questions]);

  // Update progress when question index changes
  useEffect(() => {
    if (questions.length > 0 && onProgressUpdate) {
      onProgressUpdate({
        current: state.currentQuestionIndex + 1,
        total: questions.length,
      });
    }
  }, [state.currentQuestionIndex, questions.length, onProgressUpdate]);

  // Force re-render when answers change (for dynamic descriptions)
  useEffect(() => {
    forceUpdate({});
  }, [state.answers]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, []);

  // Generate document changes based on answers
  const generateChanges = useCallback((answers: Record<string, QuestionnaireAnswer>) => {
    const changes: DocumentChange[] = [];

    // Company Name replacements
    const companyName = answers['onboarding.company_legal_name'];
    if (companyName && typeof companyName.value === 'string') {
      changes.push({
        type: 'replace',
        description: 'Company name placeholders throughout the document',
        oldText: '<Company Name>',
        newText: companyName.value,
        field: 'onboarding.company_legal_name',
      });
    }

    // Company Name + Address replacements
    const companyAddress = answers['onboarding.company_address'];
    if (
      companyName &&
      companyAddress &&
      typeof companyName.value === 'string' &&
      typeof companyAddress.value === 'string'
    ) {
      changes.push({
        type: 'replace',
        description: 'Company name and address placeholders',
        oldText: '<Company Name, Address>',
        newText: `${companyName.value}, ${companyAddress.value}`,
        field: 'onboarding.company_address',
      });
    }

    // Physical office - guest network removal
    const hasOffice = answers['onboarding.has_office'];
    if (hasOffice && hasOffice.value === 'No') {
      changes.push({
        type: 'remove',
        description: 'Guest network policy sections',
        oldText: 'Guest network access procedures and related bullet points',
        newText: '',
        field: 'onboarding.has_office',
      });
    }

    // Company logo
    const companyLogo = answers['onboarding.company_logo'];
    if (
      companyLogo &&
      typeof companyLogo.value === 'object' &&
      companyLogo.value &&
      'name' in companyLogo.value
    ) {
      changes.push({
        type: 'logo',
        description: 'Company logo insertion in document header',
        oldText: '[ADD COMPANY LOGO]',
        newText: `Uploaded logo: ${(companyLogo.value as FileUploadValue).name}`,
        field: 'onboarding.company_logo',
      });
    }

    // Policy owner
    const policyOwner = answers['user_response.policy_owner_email'];
    if (policyOwner && typeof policyOwner.value === 'string') {
      changes.push({
        type: 'replace',
        description: 'Policy owner contact information',
        oldText: '<Policy Owner Email>',
        newText: policyOwner.value,
        field: 'user_response.policy_owner_email',
      });
    }

    // Employee and contractor counts
    const employeeCount = parseInt(String(answers['user_response.employee_count']?.value || '0'));
    const contractorCount = parseInt(
      String(answers['user_response.contractor_count']?.value || '0'),
    );
    const totalUsers = employeeCount + contractorCount;

    // Review frequency (auto-calculated)
    let reviewFrequency = 'quarterly'; // default
    let frequencyDescription = 'Quarterly (default)';

    if (totalUsers > 0) {
      if (totalUsers < 50) {
        reviewFrequency = 'annual';
        frequencyDescription = `Annually (auto-determined for ${totalUsers} total users - small organization)`;
      } else if (totalUsers < 1000) {
        reviewFrequency = 'quarterly';
        frequencyDescription = `Quarterly (auto-determined for ${totalUsers} total users - medium organization)`;
      } else {
        reviewFrequency = 'monthly';
        frequencyDescription = `Monthly (auto-determined for ${totalUsers} total users - large organization)`;
      }

      changes.push({
        type: 'replace',
        description: `User access review schedule - ${frequencyDescription}`,
        oldText: 'quarterly',
        newText: reviewFrequency,
        field: 'user_response.review_frequency',
      });
    }

    // Termination timeframe
    const terminationTime = answers['user_response.termination_timeframe'];
    if (terminationTime && typeof terminationTime.value === 'string') {
      const timeframeText = terminationTime.value
        .replace(' (Recommended)', '')
        .replace(/^Other:\s*/, '') // Remove "Other: " prefix
        .toLowerCase();
      changes.push({
        type: 'replace',
        description: 'Access revocation timeframe when employee leaves',
        oldText: '24 business hours',
        newText: timeframeText,
        field: 'user_response.termination_timeframe',
      });
    }

    // Exception approver
    const exceptionApprover = answers['user_response.exception_approver'];
    if (exceptionApprover && typeof exceptionApprover.value === 'string') {
      changes.push({
        type: 'replace',
        description: 'Policy exception approval authority',
        oldText: '<Exceptions: IT Manager>',
        newText: exceptionApprover.value,
        field: 'user_response.exception_approver',
      });
    }

    // Violations reporter
    const violationsReporter = answers['user_response.violations_reporter'];
    if (violationsReporter && typeof violationsReporter.value === 'string') {
      changes.push({
        type: 'replace',
        description: 'Policy violation reporting contact',
        oldText: '<Violations: IT Manager>',
        newText: violationsReporter.value,
        field: 'user_response.violations_reporter',
      });
    }

    // Version control tools - source code access sections
    const versionControl = answers['onboarding.version_control_tools'];
    if (versionControl && typeof versionControl.value === 'string') {
      if (versionControl.value === 'None') {
        changes.push({
          type: 'remove',
          description: 'Source code access sections (no version control)',
          oldText: 'Access to Program Source Code sections and related content',
          newText: '',
          field: 'onboarding.version_control_tools',
        });
      } else {
        changes.push({
          type: 'add',
          description: 'Source code access policy sections',
          oldText: '',
          newText: `Source code protection for ${versionControl.value}`,
          field: 'onboarding.version_control_tools',
        });
      }
    }

    // Password management tool
    const passwordTool = answers['onboarding.password_management_tool'];
    if (passwordTool && typeof passwordTool.value === 'string') {
      if (passwordTool.value === 'None') {
        changes.push({
          type: 'remove',
          description: 'Password management tool sections',
          oldText: 'Password management systems requirements and related content',
          newText: '',
          field: 'onboarding.password_management_tool',
        });
      } else {
        const toolName = passwordTool.value.replace(' (recommended)', '');
        changes.push({
          type: 'replace',
          description: 'Password management tool requirements',
          oldText: 'Password management systems should be user-friendly',
          newText: `${toolName} systems should be user-friendly`,
          field: 'onboarding.password_management_tool',
        });
      }
    }

    // Ticket management tools
    const ticketTool = answers['onboarding.ticket_management_tools'];
    if (ticketTool && typeof ticketTool.value === 'string') {
      if (ticketTool.value === 'None') {
        changes.push({
          type: 'remove',
          description: 'Ticketing system references',
          oldText: 'Ticket management tool sections and related content',
          newText: '',
          field: 'onboarding.ticket_management_tools',
        });
      } else {
        changes.push({
          type: 'replace',
          description: 'Ticketing system references',
          oldText: '<Ticket Management Tool>',
          newText: ticketTool.value,
          field: 'onboarding.ticket_management_tools',
        });
      }
    }

    // Access request method
    const accessMethod = answers['user_response.access_request_method'];
    if (accessMethod && typeof accessMethod.value === 'string') {
      if (accessMethod.value.includes('Email')) {
        changes.push({
          type: 'replace',
          description: 'Access request process (email-based)',
          oldText: 'All requests will be sent by email to <email>',
          newText: 'All requests will be sent by email to [designated email]',
          field: 'user_response.access_request_method',
        });
      } else if (accessMethod.value.includes('Ticketing')) {
        changes.push({
          type: 'replace',
          description: 'Access request process (ticketing system)',
          oldText: 'All requests will be sent by email to <email>',
          newText: 'All requests will be submitted through the ticketing system',
          field: 'user_response.access_request_method',
        });
      } else {
        changes.push({
          type: 'replace',
          description: 'Access request and approval process',
          oldText: 'All requests will be sent by email to <email>',
          newText: `Access requests will be handled via ${accessMethod.value.toLowerCase()}`,
          field: 'user_response.access_request_method',
        });
      }
    }

    setDocumentChanges(changes);
  }, []);

  // Update document changes when answers change
  useEffect(() => {
    const currentAnswersString = JSON.stringify(state.answers);
    if (currentAnswersString !== lastAnswersRef.current && Object.keys(state.answers).length > 0) {
      lastAnswersRef.current = currentAnswersString;
      generateChanges(state.answers);
    }
  }, [state.answers, generateChanges]);

  // Save answers to API with debouncing
  const saveAnswersToAPI = useCallback(async (answers: Record<string, QuestionnaireAnswer>) => {
    try {
      setSaving(true);
      const response = await fetch('/api/answers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answers }),
      });

      if (response.ok) {
        const responseData = await response.json();

        // Store the userId for later use in automation
        if (responseData.userId) {
          localStorage.setItem('questionnaire_user_id', responseData.userId);
        }

        console.log('✅ Answers saved to API in real-time');
      } else {
        console.error('❌ Failed to save answers to API');
      }
    } catch (error) {
      console.error('❌ Network error saving answers:', error);
    } finally {
      setSaving(false);
    }
  }, []);

  const debouncedSaveToAPI = useCallback(
    (answers: Record<string, QuestionnaireAnswer>) => {
      // Clear existing timeout
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      // Set new timeout for debounced save
      saveTimeoutRef.current = setTimeout(() => {
        saveAnswersToAPI(answers);
      }, 1000); // Save 1 second after user stops typing
    },
    [saveAnswersToAPI],
  );

  const handleAnswer = useCallback(
    (answer: QuestionnaireAnswer) => {
      setState((prev) => {
        const newAnswers = {
          ...prev.answers,
          [answer.field]: answer,
        };

        // Save to localStorage immediately
        try {
          localStorage.setItem(QUESTIONNAIRE_STORAGE_KEY, JSON.stringify(newAnswers));
        } catch (error) {
          console.error('Failed to save answers to localStorage:', error);
        }

        // Debounced save to API
        debouncedSaveToAPI(newAnswers);

        return {
          ...prev,
          answers: newAnswers,
        };
      });
    },
    [debouncedSaveToAPI],
  );

  // Validation function to check if current question has a valid answer
  const isCurrentQuestionAnswered = useCallback(() => {
    if (questions.length === 0) return false;

    const currentQuestion = questions[state.currentQuestionIndex];
    const currentAnswer = state.answers[currentQuestion.field];

    if (!currentAnswer || currentAnswer.value === undefined || currentAnswer.value === null) {
      return false;
    }

    const value = currentAnswer.value;

    // Check based on response type
    switch (currentQuestion.responseType) {
      case 'Text input':
      case 'Email/User selector':
      case 'Email/User selector/String':
        return typeof value === 'string' && value.trim().length > 0;

      case 'Number input':
        return typeof value === 'number' && !isNaN(value) && value >= 0;

      case 'Date picker':
        return typeof value === 'string' && value.trim().length > 0;

      case 'File upload':
        return value !== null && typeof value === 'object' && 'name' in value;

      case 'Radio buttons':
      case 'Dropdown':
        return typeof value === 'string' && value.trim().length > 0;

      default:
        // For any other types, just check if value exists and is not empty
        return value !== '' && value !== null && value !== undefined;
    }
  }, [questions, state.currentQuestionIndex, state.answers]);

  const handleNext = useCallback(async () => {
    // Button should be disabled if no answer or automation running, but adding safety check
    if (!isCurrentQuestionAnswered() || automationRunning) {
      return;
    }

    if (state.currentQuestionIndex < questions.length - 1) {
      setState((prev) => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex + 1,
      }));
    } else {
      // All questions completed - save answers and start automation
      try {
        // Save immediately to API before completing
        await saveAnswersToAPI(state.answers);
        await onComplete(state.answers);
        setState((prev) => ({ ...prev, isCompleted: true }));

        // Start automation directly after questionnaire completion (only if not already running)
        if (onStartAutomation && !automationRunning) {
          await onStartAutomation();
        }
      } catch (error) {
        console.error('Failed to complete questionnaire or start automation:', error);
        alert('Failed to complete questionnaire. Please try again.');
      }
    }
  }, [
    state.currentQuestionIndex,
    state.answers,
    questions,
    onComplete,
    saveAnswersToAPI,
    isCurrentQuestionAnswered,
    onStartAutomation,
    automationRunning,
  ]);

  const handlePrevious = useCallback(() => {
    if (state.currentQuestionIndex > 0) {
      setState((prev) => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex - 1,
      }));
    }
  }, [state.currentQuestionIndex]);

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[400px]'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>Loading questions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className='bg-red-50 border border-red-200 rounded p-6 text-center'>
        <div className='text-red-600 mb-2'>❌ Error</div>
        <p className='text-red-700'>{error}</p>
        <button
          onClick={() => window.location.reload()}
          className='mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors'
        >
          Retry
        </button>
      </div>
    );
  }

  if (questions.length === 0) {
    return <div className='text-center text-gray-600'>No questions found.</div>;
  }

  const currentQuestion = questions[state.currentQuestionIndex];
  const currentAnswer = state.answers[currentQuestion.field];
  const progress = ((state.currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div
      className='bg-white rounded-[6px] border border-gray-200 w-full max-w-full mx-auto relative overflow-hidden flex-shrink min-w-0'
      style={{ width: '100%', maxWidth: '100%' }}
    >
      {/* Policy Generation Overlay */}
      <PolicyGenerationOverlay isVisible={automationRunning || testOverlay} />

      {/* Progress Indicator */}
      <div className='flex w-full'>
        {questions.map((_, index) => (
          <div
            key={index}
            className={`h-1 flex-1 ${
              index <= state.currentQuestionIndex ? 'bg-emerald-500' : 'bg-gray-200'
            } ${index === 0 ? 'rounded-tl-[6px]' : ''} ${
              index === questions.length - 1 ? 'rounded-tr-[6px]' : ''
            }`}
          />
        ))}
      </div>

      {/* Card Content */}
      <div className='p-8'>
        {/* Question Header */}
        <div className='flex flex-col gap-2'>
          <p className='text-xs font-normal text-gray-500 leading-4'>
            Question {state.currentQuestionIndex + 1} of {questions.length}
          </p>
          <h2 className='text-base font-medium text-gray-900 leading-6'>
            {currentQuestion.questionText}
          </h2>
        </div>

        {/* Question Input */}
        <div className='mb-8'>
          {(() => {
            const dynamicDescription = generateDynamicDescription(currentQuestion);
            return (
              dynamicDescription && (
                <p className='text-sm text-gray-600 leading-relaxed'>{dynamicDescription}</p>
              )
            );
          })()}

          <QuestionInput
            question={currentQuestion}
            value={currentAnswer?.value}
            onChange={handleAnswer}
          />
        </div>

        {/* Navigation */}
        <div className='flex justify-between items-center'>
          {/* Back Button - Only show if not on first question */}
          {state.currentQuestionIndex > 0 ? (
            <button
              onClick={handlePrevious}
              disabled={saving || automationRunning}
              className={`px-3 py-2 rounded text-sm font-medium leading-4 transition-colors duration-200 ${
                saving || automationRunning
                  ? 'text-gray-400 border border-gray-200 cursor-not-allowed'
                  : 'text-gray-700 border border-gray-300 hover:bg-gray-100 cursor-pointer'
              } shadow-[0px_1px_2px_0px_rgba(0,0,0,0.05)]`}
            >
              Back
            </button>
          ) : (
            <div></div>
          )}

          {/* Next Button */}
          <button
            onClick={handleNext}
            disabled={saving || !isCurrentQuestionAnswered() || automationRunning}
            className={`px-3 py-2 rounded text-sm font-medium leading-4 transition-colors duration-200 ${
              saving || !isCurrentQuestionAnswered() || automationRunning
                ? 'bg-gray-200 text-gray-700 border border-gray-300 cursor-not-allowed'
                : 'bg-violet-600 text-white hover:bg-violet-700 cursor-pointer'
            } shadow-[0px_1px_2px_0px_rgba(0,0,0,0.05)]`}
          >
            <div className='flex items-center gap-2'>
              {state.currentQuestionIndex === questions.length - 1 &&
                !saving &&
                !automationRunning && <SparkleIcon className='w-4 h-4' />}
              <span>
                {saving
                  ? 'Saving...'
                  : automationRunning
                  ? 'Policy Generation in Progress...'
                  : state.currentQuestionIndex === questions.length - 1
                  ? 'Generate Policy'
                  : 'Next'}
              </span>
            </div>
          </button>
        </div>

        {/* Saving indicator */}
        {saving && (
          <div className='flex items-center justify-center mt-4 text-violet-600 text-xs'>
            <div className='animate-spin rounded-full h-3 w-3 border-b border-violet-600 mr-1'></div>
            Saving...
          </div>
        )}

        {/* Test Overlay Button (Development Mode Only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className='flex items-center justify-center mt-4'>
            <button
              onClick={() => setTestOverlay(!testOverlay)}
              className='px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors cursor-pointer'
            >
              🧪 {testOverlay ? 'Hide' : 'Show'} Test Overlay
            </button>
          </div>
        )}
      </div>

      {/* Document Changes Preview - Attached to bottom of card */}
      {documentChanges.length > 0 && (
        <div
          className='border-t border-gray-200 w-full max-w-full'
          style={{ width: '100%', maxWidth: '100%' }}
        >
          <button
            onClick={() => setIsPreviewExpanded(!isPreviewExpanded)}
            className='w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors duration-200 cursor-pointer'
          >
            <div className='flex items-center gap-3'>
              <div className='text-sm font-medium text-gray-900'>Document Changes Preview</div>
              <div className='bg-violet-100 text-violet-700 text-xs font-medium px-2 py-1 rounded-full'>
                {documentChanges.length} {documentChanges.length === 1 ? 'change' : 'changes'}
              </div>
            </div>
            <div
              className={`transition-transform duration-200 ${
                isPreviewExpanded ? 'rotate-180' : ''
              }`}
            >
              <svg
                className='w-5 h-5 text-gray-400'
                fill='none'
                stroke='currentColor'
                viewBox='0 0 24 24'
              >
                <path
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  strokeWidth={2}
                  d='M19 9l-7 7-7-7'
                />
              </svg>
            </div>
          </button>

          {isPreviewExpanded && (
            <div
              className='p-6 w-full max-w-full overflow-hidden'
              style={{ width: '100%', maxWidth: '100%', wordBreak: 'break-word' }}
            >
              <p className='text-sm text-gray-600 mb-4'>
                Preview of changes that will be applied to your policy document:
              </p>
              <div
                className='space-y-3 max-h-64 overflow-y-auto overflow-x-hidden w-full max-w-full'
                style={{ width: '100%', maxWidth: '100%' }}
              >
                {documentChanges.map((change, index) => (
                  <div
                    key={index}
                    className='bg-gray-50 rounded-lg p-3 break-words overflow-hidden w-full max-w-full'
                    style={{
                      width: '100%',
                      maxWidth: '100%',
                      wordBreak: 'break-all',
                      overflowWrap: 'anywhere',
                    }}
                  >
                    {/* Text replacements */}
                    {change.type === 'replace' && change.oldText && change.newText && (
                      <div className='text-sm leading-relaxed break-words'>
                        <span className='line-through text-gray-500 break-words'>
                          {change.oldText}
                        </span>
                        <span className='mx-2 text-gray-400'>→</span>
                        <span className='text-gray-900 font-medium break-words'>
                          {change.newText}
                        </span>
                      </div>
                    )}

                    {/* Content removal */}
                    {change.type === 'remove' && (
                      <div className='text-sm text-gray-500 break-words'>
                        <span className='line-through break-words'>
                          {change.oldText || change.description}
                        </span>
                      </div>
                    )}

                    {/* Content addition */}
                    {change.type === 'add' && (
                      <div className='text-sm text-gray-900 font-medium break-words'>
                        <span className='break-words'>{change.newText}</span>
                      </div>
                    )}

                    {/* Logo changes */}
                    {change.type === 'logo' && (
                      <div className='text-sm leading-relaxed break-words'>
                        <span className='line-through text-gray-500 break-words'>
                          {change.oldText}
                        </span>
                        <span className='mx-2 text-gray-400'>→</span>
                        <span className='text-gray-900 font-medium break-words'>
                          {change.newText}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
