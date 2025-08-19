'use client'

import { Wifi, WifiOff } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ConnectionStatusProps {
  isConnected: boolean
}

export function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-lg font-medium text-sm transition-all",
        isConnected 
          ? "bg-green-600 text-white animate-pulse" 
          : "bg-red-600 text-white"
      )}>
        {isConnected ? (
          <>
            <Wifi className="h-4 w-4" />
            Connected
          </>
        ) : (
          <>
            <WifiOff className="h-4 w-4" />
            Disconnected
          </>
        )}
      </div>
    </div>
  )
}
