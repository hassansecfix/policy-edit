'use client';

import { QuestionnaireAnswer } from '@/types';
import { useEffect, useState } from 'react';

interface FileUploadValue {
  name: string;
  size: number;
  type: string;
  data: string;
}

interface DocumentChangesPreviewProps {
  visible?: boolean;
}

interface DocumentChange {
  type: 'replace' | 'remove' | 'add' | 'logo';
  description: string;
  oldText: string;
  newText: string;
  field: string;
}

export function DocumentChangesPreview({ visible = true }: DocumentChangesPreviewProps) {
  const [answers, setAnswers] = useState<Record<string, QuestionnaireAnswer> | null>(null);
  const [changes, setChanges] = useState<DocumentChange[]>([]);

  useEffect(() => {
    if (!visible) return;

    // Load answers from localStorage
    try {
      const savedAnswers = localStorage.getItem('questionnaire_answers');
      if (savedAnswers) {
        const parsedAnswers: Record<string, QuestionnaireAnswer> = JSON.parse(savedAnswers);
        setAnswers(parsedAnswers);
        generateChanges(parsedAnswers);
      }
    } catch (error) {
      console.error('Error loading answers:', error);
    }
  }, [visible]);

  const generateChanges = (answers: Record<string, QuestionnaireAnswer>) => {
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

    // Review frequency
    const reviewFreq = answers['user_response.review_frequency'];
    if (reviewFreq && typeof reviewFreq.value === 'string') {
      changes.push({
        type: 'replace',
        description: 'User access review schedule',
        oldText: 'quarterly',
        newText: reviewFreq.value.toLowerCase().replace(' (recommended)', ''),
        field: 'user_response.review_frequency',
      });
    }

    // Termination timeframe
    const terminationTime = answers['user_response.termination_timeframe'];
    if (terminationTime && typeof terminationTime.value === 'string') {
      const timeframeText = terminationTime.value.replace(' (Recommended)', '').toLowerCase();
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

    // Access request method
    const accessMethod = answers['user_response.access_request_method'];
    if (accessMethod && typeof accessMethod.value === 'string') {
      changes.push({
        type: 'replace',
        description: 'Access request and approval process',
        oldText: 'ticketing system processes',
        newText: accessMethod.value.toLowerCase() + ' processes',
        field: 'user_response.access_request_method',
      });
    }

    setChanges(changes);
  };

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'replace':
        return '🔄';
      case 'remove':
        return '🗑️';
      case 'add':
        return '➕';
      case 'logo':
        return '🖼️';
      default:
        return '📝';
    }
  };

  const getChangeColor = (type: string) => {
    switch (type) {
      case 'replace':
        return 'border-blue-200 bg-blue-50';
      case 'remove':
        return 'border-red-200 bg-red-50';
      case 'add':
        return 'border-green-200 bg-green-50';
      case 'logo':
        return 'border-purple-200 bg-purple-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  if (!visible || !answers) {
    return null;
  }

  return (
    <div className='bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-6'>
      <div className='flex items-center gap-2 mb-4'>
        <h3 className='text-lg font-semibold text-gray-900'>📄 Document Changes Preview</h3>
        <span className='text-sm text-gray-500'>({changes.length} changes will be made)</span>
      </div>

      <p className='text-sm text-gray-600 mb-4'>
        Based on your questionnaire responses, here are the changes that will be applied to your
        policy document:
      </p>

      {changes.length === 0 ? (
        <div className='text-center py-8 text-gray-500'>
          <div className='text-4xl mb-2'>📝</div>
          <p>Complete the questionnaire to see what changes will be made to your document.</p>
        </div>
      ) : (
        <div className='space-y-3 max-h-80 overflow-y-auto'>
          {changes.map((change, index) => (
            <div key={index} className={`border rounded-lg p-4 ${getChangeColor(change.type)}`}>
              <div className='flex items-start gap-3'>
                <span className='text-lg flex-shrink-0'>{getChangeIcon(change.type)}</span>
                <div className='flex-1 min-w-0'>
                  <div className='font-medium text-gray-900 mb-1'>{change.description}</div>

                  {change.type === 'remove' ? (
                    <div className='text-sm'>
                      <span className='text-red-700 line-through bg-red-100 px-2 py-1 rounded'>
                        {change.oldText}
                      </span>
                      <span className='text-green-700 ml-2 font-medium'>will be removed</span>
                    </div>
                  ) : change.type === 'logo' ? (
                    <div className='text-sm'>
                      <span className='text-gray-700 line-through bg-gray-100 px-2 py-1 rounded'>
                        {change.oldText}
                      </span>
                      <span className='mx-2'>→</span>
                      <span className='text-purple-700 bg-purple-100 px-2 py-1 rounded font-medium'>
                        {change.newText}
                      </span>
                    </div>
                  ) : (
                    <div className='text-sm'>
                      <span className='text-gray-700 line-through bg-gray-100 px-2 py-1 rounded'>
                        {change.oldText}
                      </span>
                      <span className='mx-2'>→</span>
                      <span className='text-blue-700 bg-blue-100 px-2 py-1 rounded font-medium'>
                        {change.newText}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className='mt-4 pt-4 border-t border-gray-200'>
        <div className='text-xs text-gray-500 space-y-1'>
          <div>
            🔄 = Text replacement • 🗑️ = Content removal • ➕ = Content addition • 🖼️ = Logo
            insertion
          </div>
          <div>Changes are applied automatically when you run the automation process.</div>
        </div>
      </div>
    </div>
  );
}
