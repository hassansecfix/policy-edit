'use client';
import { MultiStepLoader as Loader } from '@/components/ui';
import { useState } from 'react';

const loadingStates = [
  {
    text: '📋 Validating policy document and questionnaire data',
  },
  {
    text: '🔧 Setting up automation environment and parameters',
  },
  {
    text: '🤖 Processing questionnaire responses with AI analysis',
  },
  {
    text: '✨ Generating intelligent policy edits using Claude Sonnet 4',
  },
  {
    text: '📝 Creating tracked changes and document modifications',
  },
  {
    text: '⚙️ Triggering GitHub Actions workflow for processing',
  },
  {
    text: '🎯 Finalizing document with comments and suggestions',
  },
  {
    text: '✅ Policy automation complete - ready for download',
  },
];

interface PolicyAutomationLoaderProps {
  loading: boolean;
}

export function PolicyAutomationLoader({ loading }: PolicyAutomationLoaderProps) {
  return <Loader loadingStates={loadingStates} loading={loading} duration={3000} loop={false} />;
}

// Demo component for testing - can be removed in production
export default function MultiStepLoaderDemo() {
  const [loading, setLoading] = useState(false);

  return (
    <div className='w-full p-6'>
      <div className='mb-6 text-center'>
        <button
          onClick={() => setLoading(!loading)}
          className='bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium px-6 py-2 rounded-lg transition-colors duration-200'
        >
          {loading ? 'Stop' : 'Test'} Policy Automation Loader
        </button>
      </div>

      <PolicyAutomationLoader loading={loading} />
    </div>
  );
}
