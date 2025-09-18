'use client';

import { FileUpload, Question, QuestionnaireAnswer } from '@/types';
import { FileText, Upload } from 'lucide-react';
import Image from 'next/image';
import { useCallback, useEffect, useState } from 'react';

interface QuestionInputProps {
  question: Question;
  value?: string | number | File | FileUpload;
  onChange: (answer: QuestionnaireAnswer) => void;
}

export function QuestionInput({ question, value, onChange }: QuestionInputProps) {
  const [customText, setCustomText] = useState('');
  const [isOtherSelected, setIsOtherSelected] = useState(false);
  const [, forceUpdate] = useState({});

  // Helper function to get recommended frequency based on organization size
  const getRecommendedFrequency = useCallback(() => {
    if (question.field !== 'user_response.review_frequency') return null;

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

        if (totalUsers === 0) return null;

        // Return the option WITH the (Recommended) label to match dynamic options
        if (totalUsers < 50) {
          return 'Annually (Recommended)';
        } else if (totalUsers < 1000) {
          return 'Quarterly (Recommended)';
        } else {
          return 'Monthly (Recommended)';
        }
      } catch (error) {
        console.error('Error calculating recommended frequency:', error);
      }
    }
    return null;
  }, [question.field]);

  // Initialize state based on current value
  useEffect(() => {
    if (typeof value === 'string' && value.startsWith('Other: ')) {
      setIsOtherSelected(true);
      setCustomText(value.replace('Other: ', ''));
    } else if (value === 'Other') {
      setIsOtherSelected(true);
      setCustomText('');
    } else {
      setIsOtherSelected(false);
      setCustomText('');
    }
  }, [value]);

  const handleChange = useCallback(
    (newValue: string | number | File | FileUpload) => {
      onChange({
        field: question.field,
        value: newValue,
        questionNumber: question.questionNumber,
      });
    },
    [question, onChange],
  );

  // Auto-select recommended frequency when employee/contractor counts are available
  useEffect(() => {
    if (question.field === 'user_response.review_frequency' && !value) {
      const recommended = getRecommendedFrequency();
      if (recommended) {
        handleChange(recommended);
      }
    }
  }, [question.field, value, getRecommendedFrequency, handleChange]);

  // Force re-render when employee/contractor counts change (for dynamic recommended labels)
  useEffect(() => {
    if (question.field === 'user_response.review_frequency') {
      const handleStorageChange = () => {
        forceUpdate({});
      };

      // Listen for localStorage changes
      window.addEventListener('storage', handleStorageChange);

      return () => {
        window.removeEventListener('storage', handleStorageChange);
      };
    }
  }, [question.field]);

  const handleRadioChange = useCallback(
    (selectedValue: string) => {
      if (selectedValue === 'Other') {
        setIsOtherSelected(true);
        // If there's already custom text, use it; otherwise just "Other"
        const finalValue = customText ? `Other: ${customText}` : 'Other';
        handleChange(finalValue);
      } else {
        setIsOtherSelected(false);
        setCustomText('');
        handleChange(selectedValue);
      }
    },
    [customText, handleChange],
  );

  const handleCustomTextChange = useCallback(
    (text: string) => {
      setCustomText(text);
      if (isOtherSelected) {
        const finalValue = text ? `Other: ${text}` : 'Other';
        handleChange(finalValue);
      }
    },
    [isOtherSelected, handleChange],
  );

  const renderInput = () => {
    switch (question.responseType) {
      case 'Text input':
        return (
          <div>
            <input
              type='text'
              value={(value as string) || ''}
              onChange={(e) => handleChange(e.target.value)}
              className='w-full py-3 border-0 border-b border-gray-200 focus:outline-none focus:border-violet-600 bg-transparent text-sm text-gray-900 placeholder-gray-400'
              placeholder='Type your answer here'
            />
          </div>
        );

      case 'Number input':
        return (
          <div className='space-y-2'>
            <label className='block text-sm font-medium text-gray-700'>Number</label>
            <input
              type='number'
              value={String(value || '')}
              onChange={(e) => handleChange(parseInt(e.target.value) || 0)}
              min='0'
              className='w-full px-3 py-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-violet-600 focus:border-violet-600 text-gray-900'
              placeholder='Enter a number'
            />
          </div>
        );

      case 'Email/User selector':
      case 'Email/User selector/String':
        return (
          <div>
            <input
              type='email'
              value={(value as string) || ''}
              onChange={(e) => handleChange(e.target.value)}
              className='w-full py-3 border-0 border-b border-gray-200 focus:outline-none focus:border-violet-600 bg-transparent text-sm text-gray-900 placeholder-gray-400'
              placeholder='Type your answer here'
            />
          </div>
        );

      case 'Date picker':
        return (
          <div className='space-y-2'>
            <label className='block text-sm font-medium text-gray-700'>Select Date</label>
            <input
              type='date'
              value={(value as string) || ''}
              onChange={(e) => handleChange(e.target.value)}
              className='w-full px-3 py-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-violet-600 focus:border-violet-600 text-gray-900'
            />
          </div>
        );

      case 'File upload':
        return (
          <div className='space-y-4'>
            {/* File Upload Area */}
            <div className='relative'>
              <div className='border-2 border-dashed border-gray-300 rounded p-6 text-center hover:border-gray-400 transition-colors'>
                <Upload className='h-12 w-12 text-gray-400 mx-auto mb-4' />
                <h4 className='text-lg font-medium text-gray-900 mb-2'>Upload File</h4>
                <p className='text-sm text-gray-600 mb-4'>
                  Drag and drop your file here, or click to browse
                </p>
                <input
                  type='file'
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      // Convert file to base64 for JSON serialization
                      const reader = new FileReader();
                      reader.onload = () => {
                        const base64 = reader.result as string;
                        // Store both filename and base64 data
                        handleChange({
                          name: file.name,
                          type: file.type,
                          size: file.size,
                          data: base64,
                        });
                      };
                      reader.readAsDataURL(file);
                    }
                  }}
                  className='absolute inset-0 w-full h-full opacity-0 cursor-pointer'
                  accept='image/*,.pdf,.doc,.docx'
                />
                <div className='text-xs text-gray-500'>
                  Supported formats: Images, PDF, Word documents
                </div>
              </div>
            </div>

            {/* File Preview */}
            {value && typeof value === 'object' && 'name' in value && (
              <div className='bg-white border border-gray-200 rounded-xl p-4'>
                <div className='flex items-center gap-4'>
                  <div className='w-10 h-10 bg-violet-50 rounded flex items-center justify-center'>
                    <FileText className='h-5 w-5 text-violet-600' />
                  </div>
                  <div className='flex-1'>
                    <h5 className='font-medium text-gray-900'>
                      {(value as FileUpload).data === 'existing-file'
                        ? 'Previously uploaded file'
                        : 'Selected file'}
                    </h5>
                    <p className='text-sm text-gray-600'>{(value as FileUpload).name}</p>
                  </div>
                </div>

                {/* Show image preview for uploaded images */}
                {(value as FileUpload).type?.startsWith('image/') &&
                  (value as FileUpload).data &&
                  (value as FileUpload).data !== 'existing-file' && (
                    <div className='mt-4 p-3 bg-gray-50 rounded'>
                      <div className='text-xs font-medium text-gray-700 mb-2'>Preview:</div>
                      <Image
                        src={(value as FileUpload).data}
                        alt={`Preview of ${(value as FileUpload).name}`}
                        className='max-w-full max-h-32 object-contain rounded border bg-white'
                        width={200}
                        height={128}
                        onError={(e) => {
                          console.error('Image preview load error:', e);
                          (e.target as HTMLImageElement).style.display = 'none';
                        }}
                      />
                    </div>
                  )}
              </div>
            )}
          </div>
        );

      case 'Radio buttons':
        // For review frequency, always use dynamic options; for others, use static options from CSV
        const radioOptions =
          question.field === 'user_response.review_frequency'
            ? getRadioOptions(question)
            : question.options || getRadioOptions(question);
        return (
          <div className='flex flex-col gap-3'>
            {radioOptions.map((option) => {
              const isCurrentlySelected =
                option === 'Other'
                  ? isOtherSelected
                  : typeof value === 'string' && !value.startsWith('Other: ') && value === option;

              return (
                <div key={option}>
                  <label className='flex items-center gap-2 p-3 rounded border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors duration-200'>
                    {/* Custom Radio Button */}
                    <div className='relative'>
                      <input
                        type='radio'
                        name={`question-${question.questionNumber}`}
                        value={option}
                        checked={isCurrentlySelected}
                        onChange={(e) => handleRadioChange(e.target.value)}
                        className='sr-only'
                      />
                      <div
                        className={`w-4 h-4 rounded-full border-2 transition-all duration-200 ${
                          isCurrentlySelected
                            ? 'bg-violet-600 border-violet-600'
                            : 'bg-white border-gray-300'
                        }`}
                      >
                        {isCurrentlySelected && (
                          <div className='w-2 h-2 bg-white rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2' />
                        )}
                      </div>
                    </div>

                    {/* Option Text */}
                    <span className='text-sm text-gray-900 font-normal leading-5'>{option}</span>

                    {/* Recommended Badge */}
                    {option.includes('(Recommended)') && (
                      <span className='ml-auto bg-violet-100 text-violet-800 text-xs px-2 py-1 rounded'>
                        Recommended
                      </span>
                    )}
                  </label>

                  {/* Show text input when "Other" is selected */}
                  {option === 'Other' && isOtherSelected && (
                    <div className='mt-3 ml-6'>
                      <input
                        type='text'
                        value={customText}
                        onChange={(e) => handleCustomTextChange(e.target.value)}
                        placeholder='Please specify...'
                        className='w-full py-3 border-0 border-b border-gray-200 focus:outline-none focus:border-violet-600 bg-transparent text-sm text-gray-900 placeholder-gray-400'
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        );

      case 'Dropdown':
        const dropdownOptions = question.options || getDropdownOptions(question);
        const dropdownValue =
          typeof value === 'string' && value.startsWith('Other: ')
            ? 'Other'
            : (value as string) || '';

        // const selectOptions = dropdownOptions.map((option) => ({
        //   value: option,
        //   label: option,
        // }));

        return (
          <div className='space-y-4'>
            <div className='space-y-2'>
              <label className='block text-sm font-medium text-gray-700'>Select Option</label>
              <select
                value={dropdownValue}
                onChange={(e) => handleRadioChange(e.target.value)}
                className='w-full px-3 py-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-violet-600 focus:border-violet-600 text-gray-900'
              >
                <option value=''>Choose an option...</option>
                {dropdownOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>

            {/* Show text input when "Other" is selected in dropdown */}
            {isOtherSelected && (
              <div className='space-y-2'>
                <label className='block text-sm font-medium text-gray-700'>Please Specify</label>
                <input
                  type='text'
                  value={customText}
                  onChange={(e) => handleCustomTextChange(e.target.value)}
                  placeholder='Please specify...'
                  className='w-full px-3 py-2 border border-gray-200 rounded focus:outline-none focus:ring-2 focus:ring-violet-600 focus:border-violet-600 text-gray-900'
                />
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className='text-red-600'>Unsupported question type: {question.responseType}</div>
        );
    }
  };

  return <div className='space-y-2 mt-6'>{renderInput()}</div>;
}

// Helper functions to get options for different question types
function getRadioOptions(question: Question): string[] {
  switch (question.field) {
    case 'onboarding.has_office':
    case 'onboarding.provides_company_devices':
    case 'user_response.require_mfa':
      return ['Yes', 'No'];
    case 'user_response.access_request_method':
      return ['Ticketing system (Jira/ServiceNow/etc.)', 'Email approval', 'Manual process'];
    case 'user_response.review_frequency':
      return getDynamicReviewFrequencyOptions();
    default:
      return ['Yes', 'No'];
  }
}

// Helper function to get dynamic review frequency options with recommended labels
function getDynamicReviewFrequencyOptions(): string[] {
  const savedAnswers = localStorage.getItem('questionnaire_answers');
  let recommendedOption = 'Quarterly'; // default fallback

  if (savedAnswers) {
    try {
      const answers = JSON.parse(savedAnswers);
      const employeeCount = parseInt(String(answers['user_response.employee_count']?.value || '0'));
      const contractorCount = parseInt(
        String(answers['user_response.contractor_count']?.value || '0'),
      );
      const totalUsers = employeeCount + contractorCount;

      if (totalUsers > 0) {
        if (totalUsers < 50) {
          recommendedOption = 'Annually';
        } else if (totalUsers < 1000) {
          recommendedOption = 'Quarterly';
        } else {
          recommendedOption = 'Monthly';
        }
      }
    } catch (error) {
      console.error('Error determining recommended frequency:', error);
    }
  }

  // Return options with dynamic "(Recommended)" label
  const options = ['Annually', 'Quarterly', 'Monthly', 'Other'];
  return options.map((option) =>
    option === recommendedOption ? `${option} (Recommended)` : option,
  );
}

function getDropdownOptions(question: Question): string[] {
  switch (question.field) {
    case 'onboarding.version_control_tools':
      return ['GitHub', 'GitLab', 'Bitbucket', 'Azure DevOps', 'Other'];
    case 'onboarding.service_type':
      return ['SaaS', 'On-premise', 'Hybrid', 'Consulting', 'Other'];
    case 'onboarding.password_management_tool':
      return ['1Password (recommended)', 'LastPass', 'Bitwarden', 'Dashlane', 'Other', 'None'];
    case 'onboarding.ticket_management_tools':
      return ['Jira', 'ServiceNow', 'Zendesk', 'Clickup', 'Asana', 'Trello', 'Other'];
    case 'user_response.termination_timeframe':
      return [
        'Immediately',
        '4 business hours',
        '24 business hours',
        '48 business hours',
        '1 week',
      ];
    case 'user_response.exception_approver':
    case 'user_response.violations_reporter':
      return ['CISO', 'Security Team', 'IT Manager', 'CTO', 'CEO'];
    default:
      return [];
  }
}
