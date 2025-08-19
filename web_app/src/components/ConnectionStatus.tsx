'use client';

import { getApiUrl } from '@/config/api';
import { Wifi, WifiOff } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
}

export function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
  return (
    <div className='fixed bottom-4 right-4 z-50'>
      <div className='bg-white rounded-lg shadow-lg border p-3 flex items-center gap-2'>
        {isConnected ? (
          <Wifi className='h-4 w-4 text-green-600' />
        ) : (
          <WifiOff className='h-4 w-4 text-red-600' />
        )}
        <span className='text-sm font-medium'>{isConnected ? 'Connected' : 'Disconnected'}</span>
        <div className='text-xs text-gray-500 ml-2'>API: {getApiUrl()}</div>
      </div>
    </div>
  );
}
