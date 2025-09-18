'use client';

import { QuestionInput } from '@/components/QuestionInput';
import { generateDynamicDescription } from '@/lib/dynamic-descriptions';
import { QUESTIONNAIRE_STORAGE_KEY } from '@/lib/questionnaire-utils';
import { Question, QuestionnaireAnswer, QuestionnaireState } from '@/types';
import { useCallback, useEffect, useRef, useState } from 'react';

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
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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
    <div className='bg-white rounded-[6px] border border-gray-200 overflow-hidden w-full mx-auto'>
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
                <p className='text-sm text-gray-600 leading-relaxed mb-6'>{dynamicDescription}</p>
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
        <div className='flex justify-end'>
          <button
            onClick={handleNext}
            disabled={saving || !isCurrentQuestionAnswered() || automationRunning}
            className={`px-3 py-2 rounded text-sm font-medium leading-4 transition-colors duration-200 ${
              saving || !isCurrentQuestionAnswered() || automationRunning
                ? 'bg-gray-200 text-gray-700 border border-gray-300 cursor-not-allowed'
                : 'bg-violet-600 text-white hover:bg-violet-700 cursor-pointer'
            } shadow-[0px_1px_2px_0px_rgba(0,0,0,0.05)]`}
          >
            {saving
              ? 'Saving...'
              : automationRunning
              ? 'Policy Generation in Progress...'
              : state.currentQuestionIndex === questions.length - 1
              ? 'Generate Policy'
              : 'Next'}
          </button>
        </div>

        {/* Saving indicator */}
        {saving && (
          <div className='flex items-center justify-center mt-4 text-violet-600 text-xs'>
            <div className='animate-spin rounded-full h-3 w-3 border-b border-violet-600 mr-1'></div>
            Saving...
          </div>
        )}
      </div>
    </div>
  );
}
