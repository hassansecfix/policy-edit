'use client';

import { QuestionInput } from '@/components/QuestionInput';
import { QUESTIONNAIRE_STORAGE_KEY } from '@/lib/questionnaire-utils';
import { Question, QuestionnaireAnswer, QuestionnaireState } from '@/types';
import { useCallback, useEffect, useState } from 'react';

interface QuestionnaireProps {
  onComplete: (answers: Record<string, QuestionnaireAnswer>) => void;
  onProgressUpdate?: (progress: { current: number; total: number }) => void;
}

export function Questionnaire({ onComplete, onProgressUpdate }: QuestionnaireProps) {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [state, setState] = useState<QuestionnaireState>({
    currentQuestionIndex: 0,
    answers: {},
    isCompleted: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const handleAnswer = useCallback((answer: QuestionnaireAnswer) => {
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

      return {
        ...prev,
        answers: newAnswers,
      };
    });
  }, []);

  const handleNext = useCallback(() => {
    const currentQuestion = questions[state.currentQuestionIndex];
    const hasAnswer = state.answers[currentQuestion.field];

    if (!hasAnswer) {
      alert('Please answer this question before continuing.');
      return;
    }

    if (state.currentQuestionIndex < questions.length - 1) {
      setState((prev) => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex + 1,
      }));
    } else {
      // All questions completed
      setState((prev) => ({ ...prev, isCompleted: true }));
      onComplete(state.answers);
    }
  }, [state.currentQuestionIndex, state.answers, questions, onComplete]);

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
          <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>Loading questions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className='bg-red-50 border border-red-200 rounded-lg p-6 text-center'>
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

  if (state.isCompleted) {
    return (
      <div className='bg-green-50 border border-green-200 rounded-lg p-8 text-center'>
        <div className='text-green-600 text-2xl mb-4'>✅ Complete!</div>
        <p className='text-green-700 text-lg'>Thank you for completing the questionnaire.</p>
        <p className='text-green-600 mt-2'>
          Your responses have been saved. Redirecting to automation panel...
        </p>
        <div className='mt-4 flex items-center justify-center text-blue-600'>
          <div className='animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2'></div>
          <span className='text-sm'>Preparing automation controls</span>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[state.currentQuestionIndex];
  const currentAnswer = state.answers[currentQuestion.field];
  const progress = ((state.currentQuestionIndex + 1) / questions.length) * 100;

  return (
    <div className='max-w-2xl mx-auto'>
      {/* Progress Bar */}
      <div className='mb-8'>
        <div className='flex justify-between text-sm text-gray-600 mb-2'>
          <span>
            Question {state.currentQuestionIndex + 1} of {questions.length}
          </span>
          <span>{Math.round(progress)}% Complete</span>
        </div>
        <div className='w-full bg-gray-200 rounded-full h-2'>
          <div
            className='bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out'
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* Question Card */}
      <div className='bg-white border border-gray-200 rounded-lg shadow-sm p-8'>
        <div className='mb-6'>
          <h2 className='text-xl font-semibold text-gray-900 mb-2'>
            {currentQuestion.questionText}
          </h2>
        </div>

        <QuestionInput
          question={currentQuestion}
          value={currentAnswer?.value}
          onChange={handleAnswer}
        />

        {/* Navigation */}
        <div className='flex justify-between mt-8 pt-6 border-t border-gray-200'>
          <button
            onClick={handlePrevious}
            disabled={state.currentQuestionIndex === 0}
            className='px-6 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
          >
            Previous
          </button>

          <button
            onClick={handleNext}
            className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors'
          >
            {state.currentQuestionIndex === questions.length - 1 ? 'Complete' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
