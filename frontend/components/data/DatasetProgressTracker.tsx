'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface DatasetProgress {
  status: string;
  progress: number;
  total_records: number;
  processed_records: number;
  current_step: string;
  started_at?: string;
  completed_at?: string;
  failed_at?: string;
  error?: string;
}

interface Props {
  datasetId: string;
  token: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function DatasetProgressTracker({ 
  datasetId, 
  token, 
  onComplete, 
  onError 
}: Props) {
  const [progress, setProgress] = useState<DatasetProgress | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);

  // Stabilize callback refs to avoid re-triggering useEffect
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  // Track whether we've already fired terminal callbacks
  const terminalFired = useRef(false);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    let errorCount = 0;
    const MAX_ERRORS = 5;
    let stopped = false;

    const fetchProgress = async () => {
      if (stopped) return;
      
      try {
        const data = await api.get<DatasetProgress>(
          `/datasets/${datasetId}/progress`,
          token
        );
        
        // Reset error count on success
        errorCount = 0;
        
        console.log(`[ProgressTracker] Dataset ${datasetId}: status=${data.status}, progress=${data.progress}%, step="${data.current_step}", records=${data.processed_records}/${data.total_records}`);
        
        setProgress(data);

        // Calculate estimated time
        if (data.started_at && data.progress > 0 && data.progress < 100) {
          const start = new Date(data.started_at);
          const elapsed = (Date.now() - start.getTime()) / 1000;
          const totalEstimated = elapsed / (data.progress / 100);
          const remaining = totalEstimated - elapsed;
          setEstimatedTime(Math.max(0, Math.round(remaining)));
        }

        // Handle completion (accept both 'completed' and 'ready')
        if ((data.status === 'completed' || data.status === 'ready') && !terminalFired.current) {
          terminalFired.current = true;
          stopped = true;
          clearInterval(intervalId);
          console.log(`[ProgressTracker] Dataset ${datasetId}: Processing COMPLETE`);
          onCompleteRef.current?.();
        }

        // Handle error
        if (data.status === 'failed' && !terminalFired.current) {
          terminalFired.current = true;
          stopped = true;
          clearInterval(intervalId);
          console.error(`[ProgressTracker] Dataset ${datasetId}: Processing FAILED - ${data.error}`);
          onErrorRef.current?.(data.error || 'Processing failed');
        }
      } catch (error) {
        console.error(`[ProgressTracker] Error fetching progress (attempt ${errorCount + 1}/${MAX_ERRORS}):`, error);
        errorCount++;
        
        // Stop polling after too many errors
        if (errorCount >= MAX_ERRORS && !terminalFired.current) {
          terminalFired.current = true;
          stopped = true;
          clearInterval(intervalId);
          onErrorRef.current?.('Failed to fetch processing progress. Please refresh the page.');
        }
      }
    };

    // Initial fetch
    fetchProgress();

    // Poll every 2 seconds (reduced from 1s to avoid overwhelming backend)
    intervalId = setInterval(fetchProgress, 2000);

    return () => {
      stopped = true;
      clearInterval(intervalId);
    };
  }, [datasetId, token]); // Only depend on stable values

  if (!progress) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">Connecting to processing pipeline...</span>
      </div>
    );
  }

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const isCompleted = progress.status === 'completed' || progress.status === 'ready';
  const isFailed = progress.status === 'failed';
  const isProcessing = !isCompleted && !isFailed;

  return (
    <div className="space-y-4 p-6 bg-white dark:bg-card rounded-lg border">
      {/* Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isProcessing && (
            <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          )}
          {isCompleted && (
            <CheckCircle className="w-5 h-5 text-green-600" />
          )}
          {isFailed && (
            <AlertCircle className="w-5 h-5 text-red-600" />
          )}
          <h3 className="font-semibold text-lg">
            {isProcessing && 'Processing Dataset'}
            {isCompleted && 'Processing Complete'}
            {isFailed && 'Processing Failed'}
          </h3>
        </div>
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {progress.progress}%
        </span>
      </div>

      {/* Progress Bar */}
      <Progress value={progress.progress} className="h-2" />

      {/* Details */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">Records Processed:</span>
          <span className="ml-2 font-medium">
            {progress.processed_records.toLocaleString()} / {progress.total_records.toLocaleString()}
          </span>
        </div>
        
        {estimatedTime !== null && isProcessing && (
          <div>
            <span className="text-gray-500 dark:text-gray-400">Time Remaining:</span>
            <span className="ml-2 font-medium">
              ~{formatTime(estimatedTime)}
            </span>
          </div>
        )}
      </div>

      {/* Current Step */}
      <div className="text-sm">
        <span className="text-gray-500 dark:text-gray-400">Current Step:</span>
        <span className="ml-2 font-medium">{progress.current_step}</span>
      </div>

      {/* Error Message */}
      {progress.error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
          <p className="text-sm text-red-800 dark:text-red-200">
            {progress.error}
          </p>
        </div>
      )}
    </div>
  );
}

