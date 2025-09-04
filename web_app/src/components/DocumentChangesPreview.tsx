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
  type: 'replace' | 'remove' | 'add' | 'logo' | 'info';
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

    // Employee and contractor counts
    const employeeCount = parseInt(String(answers['user_response.employee_count']?.value || '0'));
    const contractorCount = parseInt(
      String(answers['user_response.contractor_count']?.value || '0'),
    );
    const totalUsers = employeeCount + contractorCount;

    if (employeeCount > 0) {
      changes.push({
        type: 'info',
        description: `Organization size calculation: ${employeeCount} employees`,
        oldText: '',
        newText: `${employeeCount}`,
        field: 'user_response.employee_count',
      });
    }

    if (contractorCount > 0) {
      changes.push({
        type: 'info',
        description: `Organization size calculation: ${contractorCount} contractors`,
        oldText: '',
        newText: `${contractorCount}`,
        field: 'user_response.contractor_count',
      });
    }

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
      case 'info':
        return '📊';
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
      case 'info':
        return 'border-cyan-200 bg-cyan-50';
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
