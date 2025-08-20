/**
 * Utility functions for managing questionnaire data in localStorage
 */

export const QUESTIONNAIRE_STORAGE_KEY = 'questionnaire_answers';

/**
 * Clear all questionnaire answers from localStorage
 */
export function clearQuestionnaireAnswers(): void {
  try {
    localStorage.removeItem(QUESTIONNAIRE_STORAGE_KEY);
    console.log('Questionnaire answers cleared from localStorage');
  } catch (error) {
    console.error('Failed to clear questionnaire answers:', error);
  }
}

/**
 * Get questionnaire answers from localStorage
 */
export function getQuestionnaireAnswers(): Record<string, any> | null {
  try {
    const savedAnswers = localStorage.getItem(QUESTIONNAIRE_STORAGE_KEY);
    return savedAnswers ? JSON.parse(savedAnswers) : null;
  } catch (error) {
    console.error('Failed to get questionnaire answers:', error);
    return null;
  }
}

/**
 * Check if questionnaire has any answers
 */
export function hasQuestionnaireAnswers(): boolean {
  const answers = getQuestionnaireAnswers();
  return answers !== null && Object.keys(answers).length > 0;
}

/**
 * Export questionnaire answers for debugging
 */
export function exportQuestionnaireAnswers(): string {
  const answers = getQuestionnaireAnswers();
  return JSON.stringify(answers, null, 2);
}

// Make functions available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).questionnaireUtils = {
    clear: clearQuestionnaireAnswers,
    get: getQuestionnaireAnswers,
    has: hasQuestionnaireAnswers,
    export: exportQuestionnaireAnswers,
  };
}
