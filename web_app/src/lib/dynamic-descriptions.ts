import { Question } from '@/types';

/**
 * Generate dynamic descriptions for questions based on previous user answers
 */
export function generateDynamicDescription(question: Question): string {
  if (
    question.field === 'user_response.review_frequency' &&
    question.questionDescription === 'DYNAMIC_DESCRIPTION_PLACEHOLDER'
  ) {
    const savedAnswers = localStorage.getItem('questionnaire_answers');
    if (savedAnswers) {
      try {
        const answers = JSON.parse(savedAnswers);
        const employeeCount = parseInt(
          String(answers['user_response.employee_count']?.value || '0'),
        );
        const contractorCount = parseInt(
          String(answers['user_response.contractor_count']?.value || '0'),
        );
        const totalUsers = employeeCount + contractorCount;

        if (totalUsers === 0) {
          return 'Please enter your employee and contractor counts first to determine the appropriate review frequency.';
        }

        let frequency = '';
        let organizationType = '';

        if (totalUsers < 50) {
          frequency = 'Annual';
          organizationType = 'small';
        } else if (totalUsers < 1000) {
          frequency = 'Quarterly';
          organizationType = 'medium';
        } else {
          frequency = 'Monthly';
          organizationType = 'large';
        }

        return `Based on your organization size (${employeeCount} employees + ${contractorCount} contractors = ${totalUsers} total users), we recommend ${frequency.toLowerCase()} reviews for ${organizationType} organizations. This option has been auto-selected for you, but you can choose a different frequency if your company has specific requirements.`;
      } catch (error) {
        console.error('Error generating dynamic description:', error);
      }
    }

    return 'Access review frequency will be automatically determined based on your organization size once you provide employee and contractor counts.';
  }

  return question.questionDescription || '';
}
