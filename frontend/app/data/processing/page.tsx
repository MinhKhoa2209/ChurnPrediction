'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store/auth-store';
import { useDatasetStore } from '@/lib/store/dataset-store';
import { api } from '@/lib/api';
import { Activity, CheckCircle, Clock, Database, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';

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

export default function DataProcessingPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuthStore();
  const { currentDataset } = useDatasetStore();
  
  const [activeTab, setActiveTab] = useState<'overview' | 'cleaning' | 'transformation'>('overview');
  const [progress, setProgress] = useState<DatasetProgress | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  // Determine the pipeline stages based on real progress
  const getStageStatus = useCallback(() => {
    if (!progress) {
      return { upload: 'pending', cleaning: 'pending', features: 'pending' };
    }

    const isCompleted = progress.status === 'completed' || progress.status === 'ready';
    const isFailed = progress.status === 'failed';

    if (isFailed) {
      return { upload: 'completed', cleaning: 'failed', features: 'pending' };
    }

    if (isCompleted) {
      return { upload: 'completed', cleaning: 'completed', features: 'completed' };
    }

    // Processing
    if (progress.progress < 30) {
      return { upload: 'completed', cleaning: 'processing', features: 'pending' };
    } else if (progress.progress < 80) {
      return { upload: 'completed', cleaning: 'processing', features: 'pending' };
    } else {
      return { upload: 'completed', cleaning: 'completed', features: 'processing' };
    }
  }, [progress]);

  // Poll progress when we have a processing dataset
  useEffect(() => {
    if (!currentDataset?.id || !token) return;

    let intervalId: NodeJS.Timeout;
    let stopped = false;

    const fetchProgress = async () => {
      if (stopped) return;
      try {
        const data = await api.get<DatasetProgress>(
          `/datasets/${currentDataset.id}/progress`,
          token
        );

        setProgress(data);

        // Add log entry
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `[${timestamp}] ${data.current_step} (${data.progress}%)`;
        setLogs(prev => {
          // Avoid duplicate consecutive entries
          if (prev.length > 0 && prev[prev.length - 1].includes(data.current_step)) {
            return prev;
          }
          return [...prev, logEntry].slice(-50); // Keep last 50 entries
        });

        // Stop polling when done
        if (data.status === 'completed' || data.status === 'ready' || data.status === 'failed') {
          stopped = true;
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('[ProcessingPage] Error fetching progress:', err);
      }
    };

    fetchProgress();
    intervalId = setInterval(fetchProgress, 2000);

    return () => {
      stopped = true;
      clearInterval(intervalId);
    };
  }, [currentDataset?.id, token]);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== 'Admin')) {
      router.push('/dashboard');
    }
  }, [user, authLoading, router]);

  if (authLoading || (!user || user.role !== 'Admin')) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const stages = getStageStatus();
  const isCompleted = progress?.status === 'completed' || progress?.status === 'ready';
  const isFailed = progress?.status === 'failed';

  const getStageIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5" />;
      case 'processing': return <Activity className="w-5 h-5 animate-pulse" />;
      case 'failed': return <AlertCircle className="w-5 h-5" />;
      default: return <Clock className="w-5 h-5" />;
    }
  };

  const getStageColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500 text-white';
      case 'processing': return 'bg-blue-500 text-white';
      case 'failed': return 'bg-red-500 text-white';
      default: return 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400';
    }
  };

  const getStageLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'Completed';
      case 'processing': return 'Processing';
      case 'failed': return 'Failed';
      default: return 'Pending';
    }
  };

  const getStageBg = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-50 dark:bg-green-900/10 border-green-100 dark:border-green-800';
      case 'processing': return 'bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-800';
      case 'failed': return 'bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-800';
      default: return 'bg-white dark:bg-card border-gray-100 dark:border-border opacity-60';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-background">
      <nav className="bg-white dark:bg-card shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900 dark:text-foreground">
                Data Processing Pipeline
              </h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0 space-y-6">
          
          {/* Status Header */}
          <div className="bg-white dark:bg-card shadow rounded-lg p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-foreground">Dataset Processing</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {currentDataset ? `Processing dataset: ${currentDataset.filename || currentDataset.id}` : 'No active dataset selected for processing'}
              </p>
              {progress && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Overall progress: <span className="font-semibold">{progress.progress}%</span>
                  {progress.total_records > 0 && ` — ${progress.processed_records.toLocaleString()} / ${progress.total_records.toLocaleString()} records`}
                </p>
              )}
            </div>
            <div className="flex gap-3">
              <button 
                onClick={() => router.push('/data/upload')}
                className="px-4 py-2 border border-gray-300 dark:border-border rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-muted transition-colors"
              >
                Upload New Data
              </button>
              <button 
                onClick={() => {
                  if (currentDataset?.id) {
                    router.push(`/data/eda/${currentDataset.id}`);
                  }
                }}
                disabled={!currentDataset || !isCompleted}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                Continue to EDA <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          {progress && currentDataset && (
            <div className="bg-white dark:bg-card shadow rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {progress.current_step}
                </span>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {progress.progress}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-muted rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full transition-all duration-500 ${
                    isFailed ? 'bg-red-500' : isCompleted ? 'bg-green-500' : 'bg-blue-600'
                  }`}
                  style={{ width: `${progress.progress}%` }}
                />
              </div>
              {progress.error && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{progress.error}</p>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Sidebar Navigation */}
            <div className="md:col-span-1 space-y-2">
              <button 
                onClick={() => setActiveTab('overview')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'overview' 
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-muted'
                }`}
              >
                Processing Overview
              </button>
              <button 
                onClick={() => setActiveTab('cleaning')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'cleaning' 
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-muted'
                }`}
              >
                Processing Log
              </button>
              <button 
                onClick={() => setActiveTab('transformation')}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'transformation' 
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' 
                    : 'text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-muted'
                }`}
              >
                Pipeline Info
              </button>
            </div>

            {/* Main Content Area */}
            <div className="md:col-span-3">
              <div className="bg-white dark:bg-card shadow rounded-lg p-6 min-h-[400px]">
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-foreground border-b pb-2">Pipeline Status</h3>
                    
                    {!currentDataset ? (
                      <div className="text-center py-12">
                        <Database className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-500">Please upload a dataset first to view processing details.</p>
                      </div>
                    ) : (
                      <div className="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-300 dark:before:via-gray-600 before:to-transparent">
                        
                        {/* Step 1: Upload & Validation */}
                        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                          <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-card shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 ${getStageColor(stages.upload)}`}>
                            {getStageIcon(stages.upload)}
                          </div>
                          <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg border shadow-sm ${getStageBg(stages.upload)}`}>
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-bold text-gray-900 dark:text-foreground">Upload & Validation</h4>
                              <span className={`text-xs font-medium ${stages.upload === 'completed' ? 'text-green-600' : 'text-gray-500'}`}>
                                {getStageLabel(stages.upload)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500">File uploaded and schema validated successfully.</p>
                          </div>
                        </div>

                        {/* Step 2: Record Processing */}
                        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                          <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-card shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 ${getStageColor(stages.cleaning)}`}>
                            {getStageIcon(stages.cleaning)}
                          </div>
                          <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg border shadow-sm ${getStageBg(stages.cleaning)}`}>
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-bold text-gray-900 dark:text-foreground">Record Processing</h4>
                              <span className={`text-xs font-medium ${
                                stages.cleaning === 'completed' ? 'text-green-600' : 
                                stages.cleaning === 'processing' ? 'text-blue-600 dark:text-blue-400' : 
                                stages.cleaning === 'failed' ? 'text-red-600' : 'text-gray-500'
                              }`}>
                                {getStageLabel(stages.cleaning)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500">
                              {progress ? `Parsing CSV rows and storing customer records. ${progress.processed_records.toLocaleString()} / ${progress.total_records.toLocaleString()} records.` : 'Parsing and storing customer records.'}
                            </p>
                          </div>
                        </div>

                        {/* Step 3: Finalization */}
                        <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                          <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-white dark:border-card shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 ${getStageColor(stages.features)}`}>
                            {getStageIcon(stages.features)}
                          </div>
                          <div className={`w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg border shadow-sm ${getStageBg(stages.features)}`}>
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-bold text-gray-900 dark:text-foreground">Finalization & Quality Check</h4>
                              <span className={`text-xs font-medium ${
                                stages.features === 'completed' ? 'text-green-600' : 
                                stages.features === 'processing' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500'
                              }`}>
                                {getStageLabel(stages.features)}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500">Validating data integrity and preparing for EDA.</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Post-completion info */}
                    {isCompleted && (
                      <div className="bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg p-4 mt-4">
                        <p className="text-sm text-green-800 dark:text-green-200 font-medium">
                          ✓ Processing complete! Your dataset is ready for Exploratory Data Analysis.
                        </p>
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                          Note: Feature engineering (encoding, scaling, SMOTE) will be applied automatically when you start model training.
                        </p>
                      </div>
                    )}
                  </div>
                )}
                
                {activeTab === 'cleaning' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-foreground border-b pb-2">Processing Log</h3>
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-64 overflow-y-auto">
                      {logs.length === 0 ? (
                        <>
                          <p>Waiting for processing events...</p>
                          <p className="text-gray-500">
                            {currentDataset ? 'Polling for progress updates...' : 'Upload a dataset to begin.'}
                          </p>
                        </>
                      ) : (
                        logs.map((log, i) => (
                          <p key={i}>{log}</p>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'transformation' && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-foreground border-b pb-2">Pipeline Information</h3>
                    <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
                      <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                        <h4 className="font-semibold mb-2">Upload Processing (Current Stage)</h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                          <li>CSV schema validation (21 required columns)</li>
                          <li>Data type validation per row</li>
                          <li>Duplicate customerID detection</li>
                          <li>Batch record insertion (1000 rows per batch)</li>
                          <li>Sensitive field encryption (customerID, PaymentMethod)</li>
                        </ul>
                      </div>
                      <div className="bg-gray-50 dark:bg-muted border border-gray-200 dark:border-border rounded-lg p-4">
                        <h4 className="font-semibold mb-2">Feature Engineering (Applied at Training Time)</h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">
                          <li>Missing value imputation (median/mode)</li>
                          <li>Outlier treatment (IQR clipping)</li>
                          <li>Binary feature encoding</li>
                          <li>One-hot encoding for multi-class features</li>
                          <li>Standard scaling (fit on train, transform on test)</li>
                          <li>SMOTE oversampling for class balance</li>
                          <li>Stratified train/test split (80/20)</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
