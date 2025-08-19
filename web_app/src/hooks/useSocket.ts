'use client';

import type { FileDownload, LogEntry, ProgressUpdate } from '@/types';
import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  logs: LogEntry[];
  progress: ProgressUpdate | null;
  files: FileDownload[];
  clearLogs: () => void;
  addLog: (log: LogEntry) => void;
}

export function useSocket(url: string = 'http://localhost:5001'): UseSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [files, setFiles] = useState<FileDownload[]>([]);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize socket connection
    const socket = io(url);
    socketRef.current = socket;

    // Connection event handlers
    socket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to server');
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from server');
    });

    // Application event handlers
    socket.on('log_message', (data: LogEntry) => {
      setLogs((prev) => [...prev, data]);
    });

    socket.on('progress_update', (data: ProgressUpdate) => {
      setProgress(data);
    });

    socket.on('files_ready', (data: { files: FileDownload[] }) => {
      setFiles(data.files);
    });

    socket.on('logs_cleared', () => {
      setLogs([]);
    });

    // Cleanup on unmount
    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, [url]);

  const clearLogs = () => {
    if (socketRef.current) {
      socketRef.current.emit('clear_logs');
    }
  };

  const addLog = (log: LogEntry) => {
    setLogs((prev) => [...prev, log]);
  };

  return {
    socket: socketRef.current,
    isConnected,
    logs,
    progress,
    files,
    clearLogs,
    addLog,
  };
}
