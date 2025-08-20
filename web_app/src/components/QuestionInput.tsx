'use client';

import { FileUpload, Question, QuestionnaireAnswer } from '@/types';
import { useCallback } from 'react';

interface QuestionInputProps {
  question: Question;
  value?: string | number | File | FileUpload;
  onChange: (answer: QuestionnaireAnswer) => void;
}

export function QuestionInput({ question, value, onChange }: QuestionInputProps) {
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

  const renderInput = () => {
    switch (question.responseType) {
      case 'Text input':
        return (
          <input
            type='text'
            value={(value as string) || ''}
            onChange={(e) => handleChange(e.target.value)}
            className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-gray-900 bg-white'
            placeholder='Enter your answer...'
          />
        );

      case 'Number input':
        return (
          <input
            type='number'
            value={(value as number) || ''}
            onChange={(e) => handleChange(parseInt(e.target.value) || 0)}
            className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-gray-900 bg-white'
            placeholder='Enter a number...'
            min='0'
          />
        );

      case 'Email/User selector':
        return (
          <input
            type='email'
            value={(value as string) || ''}
            onChange={(e) => handleChange(e.target.value)}
            className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-gray-900 bg-white'
            placeholder='Enter email address...'
          />
        );

      case 'Date picker':
        return (
          <input
            type='date'
            value={(value as string) || ''}
            onChange={(e) => handleChange(e.target.value)}
            className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-gray-900 bg-white'
          />
        );

      case 'File upload':
        return (
          <div className='space-y-4'>
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
              className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-gray-900 bg-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
              accept='image/*,.pdf,.doc,.docx'
            />
            {value && typeof value === 'object' && 'name' in value && (
              <div className='text-sm text-gray-600'>
                {(value as FileUpload).data === 'existing-file'
                  ? `Previously uploaded: ${(value as FileUpload).name}`
                  : `Selected: ${(value as FileUpload).name}`}
              </div>
            )}
          </div>
        );

      case 'Radio buttons':
        return (
          <div className='space-y-3'>
            {getRadioOptions(question).map((option) => (
              <label key={option} className='flex items-center space-x-3 cursor-pointer'>
                <input
                  type='radio'
                  name={`question-${question.questionNumber}`}
                  value={option}
                  checked={value === option}
                  onChange={(e) => handleChange(e.target.value)}
                  className='w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500'
                />
                <span className='text-gray-700'>{option}</span>
              </label>
            ))}
          </div>
        );

      case 'Dropdown':
        return (
          <select
            value={(value as string) || ''}
            onChange={(e) => handleChange(e.target.value)}
            className='w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors bg-white text-gray-900'
          >
            <option value=''>Select an option...</option>
            {getDropdownOptions(question).map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      default:
        return (
          <div className='text-red-600'>Unsupported question type: {question.responseType}</div>
        );
    }
  };

  return <div className='space-y-2'>{renderInput()}</div>;
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
    default:
      return ['Yes', 'No'];
  }
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
    case 'user_response.review_frequency':
      return ['Monthly', 'Quarterly (Recommended)', 'Semi-annually', 'Annually'];
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
