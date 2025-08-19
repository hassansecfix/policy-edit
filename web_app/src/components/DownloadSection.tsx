'use client';

import type { FileDownload } from '@/types';
import { Download, FileText } from 'lucide-react';

interface DownloadSectionProps {
  files: FileDownload[];
  visible: boolean;
}

export function DownloadSection({ files, visible }: DownloadSectionProps) {
  if (!visible || files.length === 0) {
    return null;
  }

  const handleDownload = (file: FileDownload) => {
    const downloadUrl = `http://localhost:5001/api/download/${encodeURIComponent(file.path)}`;

    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = file.name;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className='bg-white rounded-lg shadow-sm border'>
      <div className='bg-gradient-to-r from-green-500 to-emerald-500 text-white p-4 rounded-t-lg'>
        <h3 className='font-semibold flex items-center gap-2'>
          <Download className='h-5 w-5' />
          Download Files
        </h3>
      </div>
      <div className='p-6'>
        <div className='space-y-3'>
          {files.map((file, index) => (
            <div
              key={index}
              className='flex items-center gap-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors'
            >
              <FileText className='h-5 w-5 text-gray-500 flex-shrink-0' />
              <div className='flex-1 min-w-0'>
                <div className='font-medium text-gray-900 truncate' title={file.name}>
                  {file.name}
                </div>
                <div className='text-sm text-gray-500'>{file.size}</div>
              </div>
              <button
                onClick={() => handleDownload(file)}
                className='flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex-shrink-0 ml-4'
              >
                <Download className='h-4 w-4' />
                <span className='hidden sm:inline'>Download</span>
                <span className='sm:hidden'>DL</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
