'use client';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { API_CONFIG, getApiUrl } from '@/config/api';
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
    const downloadUrl = getApiUrl(
      `${API_CONFIG.endpoints.download}/${encodeURIComponent(file.path)}`,
    );

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
    <Card className='border-0 overflow-hidden'>
      <CardHeader className='bg-gradient-to-r from-green-50 to-emerald-50 border-b border-green-100'>
        <div className='flex items-center justify-between'>
          <div>
            <CardTitle className='text-lg font-semibold text-gray-900 flex items-center gap-2'>
              <Download className='h-5 w-5 text-green-600' />
              Download Files
            </CardTitle>
            <CardDescription className='mt-1'>
              Your customized policy documents are ready
            </CardDescription>
          </div>
          <Badge variant='success' className='bg-emerald-100 text-emerald-800'>
            {files.length} {files.length === 1 ? 'file' : 'files'} ready
          </Badge>
        </div>
      </CardHeader>

      <CardContent className='p-0'>
        <div className='divide-y divide-gray-50'>
          {files.map((file, index) => (
            <div key={index} className='p-6 hover:bg-gray-50/50 transition-all duration-200 group'>
              <div className='flex items-center gap-4'>
                {/* File Icon */}
                <div className='flex-shrink-0'>
                  <div className='w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center group-hover:bg-blue-100 transition-colors'>
                    <FileText className='h-5 w-5 text-blue-600' />
                  </div>
                </div>

                {/* File Info */}
                <div className='flex-1 min-w-0'>
                  <h4 className='font-medium text-gray-900 truncate mb-1' title={file.name}>
                    {file.name}
                  </h4>
                  <div className='flex items-center gap-2'>
                    <Badge variant='outline' className='text-xs'>
                      {file.size}
                    </Badge>
                    <span className='text-xs text-gray-500'>Ready for download</span>
                  </div>
                </div>

                {/* Download Button */}
                <div className='flex-shrink-0'>
                  <Button
                    onClick={() => handleDownload(file)}
                    variant='default'
                    size='sm'
                    className=''
                  >
                    <Download className='h-4 w-4' />
                    <span className='hidden sm:inline ml-2'>Download</span>
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>

      <div className='px-6 py-4 bg-gray-50 border-t border-gray-100'>
        <p className='text-xs text-gray-600 text-center'>
          🎉 Your customized policy documents have been generated successfully
        </p>
      </div>
    </Card>
  );
}
